#!/usr/bin/env node

/**
 * 批量统一处理器 - 使用统一抓取器
 * 集成高级尺码表抓取功能，批量处理所有商品
 */

const fs = require('fs');
const path = require('path');
const UnifiedDetailScraper = require('./unified_detail_scraper');

class BatchUnifiedProcessor {
    constructor(options = {}) {
        // 🎯 使用统一抓取器 - 后台模式，适合批量处理
        this.scraper = new UnifiedDetailScraper({
            headless: options.headless !== undefined ? options.headless : true, // 批量处理默认后台模式
            debug: options.debug !== undefined ? options.debug : false,         // 批量处理默认关闭调试
            timeout: options.timeout || 45000,
            ...options
        });

        this.inputFile = options.inputFile || this.findLatestInputFile();
        // 保持原有的输出目录结构
        this.outputDir = options.outputDir || './golf_content/lecoqgolf/';
        this.outputPath = options.outputPath;  // 完整输出文件路径（可选）
        this.results = {};
        this.processedCount = 0;
        this.totalProducts = 0;
        this.errors = [];

        // 状态管理 - 放在当前工作目录而不是输出目录
        this.statusFile = './batch_unified_status.json';
        this.loadStatus();
    }

    // 自动查找最新的输入文件
    findLatestInputFile() {
        const searchPaths = [
            '/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/golf_content/lecoqgolf/',
            '/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/',
            '/Users/sanshui/Desktop/CallawayJP/'
        ];

        const possiblePatterns = [
            /lecoqgolf_products_.*\.json$/,
            /.*products.*\.json$/,
            /.*batch.*\.json$/
        ];

        let latestFile = null;
        let latestTime = new Date(0);

        for (const searchPath of searchPaths) {
            try {
                if (!fs.existsSync(searchPath)) continue;

                const files = fs.readdirSync(searchPath);

                for (const file of files) {
                    const filePath = path.join(searchPath, file);
                    const stat = fs.statSync(filePath);

                    // 检查是否匹配模式
                    const matchesPattern = possiblePatterns.some(pattern => pattern.test(file));

                    if (matchesPattern && stat.isFile() && stat.mtime > latestTime) {
                        latestTime = stat.mtime;
                        latestFile = filePath;
                    }
                }
            } catch (error) {
                console.log(`⚠️ 搜索路径失败: ${searchPath}, 错误: ${error.message}`);
            }
        }

        if (latestFile) {
            console.log(`📁 自动找到最新输入文件: ${latestFile}`);
            return latestFile;
        } else {
            console.log('⚠️ 未找到合适的输入文件，请使用 --input 参数指定');
            return null;
        }
    }

    // 状态管理方法
    loadStatus() {
        try {
            if (fs.existsSync(this.statusFile)) {
                const statusData = JSON.parse(fs.readFileSync(this.statusFile, 'utf8'));
                this.processedUrls = new Set(statusData.processedUrls || []);
                this.failedUrls = new Map(statusData.failedUrls || []);
                console.log(`📊 加载状态: 已处理 ${this.processedUrls.size} 个URL，失败 ${this.failedUrls.size} 个`);
            } else {
                this.processedUrls = new Set();
                this.failedUrls = new Map();
            }
        } catch (error) {
            console.log('⚠️ 状态文件加载失败，使用全新状态');
            this.processedUrls = new Set();
            this.failedUrls = new Map();
        }
    }

    saveStatus() {
        try {
            const statusData = {
                processedUrls: Array.from(this.processedUrls),
                failedUrls: Array.from(this.failedUrls.entries()),
                lastUpdate: new Date().toISOString(),
                processedCount: this.processedCount,
                totalCount: this.totalProducts
            };
            fs.writeFileSync(this.statusFile, JSON.stringify(statusData, null, 2));
        } catch (error) {
            console.warn('⚠️ 状态文件保存失败:', error.message);
        }
    }

    isUrlProcessed(url) {
        return this.processedUrls.has(url);
    }

    markUrlProcessed(url) {
        this.processedUrls.add(url);
        this.failedUrls.delete(url);
        this.saveStatus();
    }

    markUrlFailed(url, error) {
        const failCount = this.failedUrls.get(url) || 0;
        this.failedUrls.set(url, failCount + 1);
        this.saveStatus();
    }

    async processAllProducts() {
        console.log('🚀 开始批量统一处理Le Coq Sportif Golf详情页...');
        console.log('🌐 运行模式：纯后台模式（无界面，使用统一抓取器）');

        try {
            // 1. 读取商品列表
            const productData = await this.loadProductList();
            const products = this.extractProductUrls(productData);

            console.log(`📋 从文件加载 ${products.length} 个商品`);
            this.totalProducts = products.length;

            if (products.length === 0) {
                console.log('❌ 未找到商品URL');
                return;
            }

            // 过滤已处理的URL
            const unprocessedProducts = products.filter(product => {
                if (!product.url) {
                    console.log('⚠️ 商品缺少URL:', product.productId || product.name);
                    return false;
                }
                return !this.isUrlProcessed(product.url);
            });

            console.log(`🔄 过滤后需要处理 ${unprocessedProducts.length} 个商品`);

            if (unprocessedProducts.length === 0) {
                console.log('✅ 所有商品都已处理完成');
                return null; // 返回null表示没有新文件生成
            }

            // 2. 批量处理
            console.log('\n🔄 开始批量处理详情页...\n');

            for (let i = 0; i < unprocessedProducts.length; i++) {
                const product = unprocessedProducts[i];
                const progress = Math.round(((i + 1) / unprocessedProducts.length) * 100);

                console.log(`\n📦 [${progress}%] 处理商品 ${i + 1}/${unprocessedProducts.length}`);
                console.log(`🆔 商品ID: ${product.productId}`);
                console.log(`🔗 URL: ${product.url}`);

                try {
                    // 🎯 使用统一抓取器处理单个商品
                    const result = await this.scraper.scrapeDetailPage(product.url, {
                        productId: product.productId,
                        name: product.name
                    });

                    if (result.success) {
                        // 转换为标准格式
                        const productData = this.convertToProductFormat(result);

                        this.results[result.productId || product.productId] = productData;
                        this.processedCount++;

                        this.markUrlProcessed(product.url);

                        console.log(`✅ 处理成功: ${result.productName}`);
                        console.log(`🎨 颜色: ${(result.colors || []).length}种`);
                        console.log(`📏 尺码: ${(result.sizes || []).length}个`);
                        console.log(`🖼️ 图片: ${(result.imageUrls || []).length}张`);

                        if (result.sizeChart && result.sizeChart.success) {
                            console.log(`📋 尺码表: ✅ (${result.sizeChart.method})`);
                        } else {
                            console.log(`📋 尺码表: ❌`);
                        }
                    } else {
                        console.log(`❌ 处理失败: ${result.error}`);
                        this.markUrlFailed(product.url, result.error);
                    }

                } catch (error) {
                    console.log(`❌ 处理异常: ${error.message}`);
                    this.markUrlFailed(product.url, error.message);
                }

                // 每5个商品保存一次中间结果
                if ((i + 1) % 5 === 0) {
                    await this.saveIntermediateResults();
                    console.log(`💾 已保存中间结果 (处理了 ${i + 1} 个商品)`);
                }

                // 简短的延迟，避免过于频繁请求
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // 3. 保存最终结果
            const finalFile = await this.saveFinalResults();

            console.log('\n🎉 批量处理完成!');
            console.log(`📊 处理统计: 成功 ${this.processedCount}/${this.totalProducts} 个商品`);
            console.log(`❌ 失败: ${this.failedUrls.size} 个商品`);

            return finalFile; // 返回实际保存的文件路径

        } catch (error) {
            console.error('❌ 批量处理过程出错:', error);
            throw error; // 重新抛出错误，让主函数能正确处理异常
        }
    }

    async loadProductList() {
        try {
            const rawData = fs.readFileSync(this.inputFile, 'utf8');
            return JSON.parse(rawData);
        } catch (error) {
            console.error('❌ 读取商品列表失败:', error);
            throw error;
        }
    }

    extractProductUrls(productData) {
        const products = [];

        // 支持多种数据格式
        if (productData.products && typeof productData.products === 'object') {
            // 对象格式: { "product_id": { ... } }
            Object.entries(productData.products).forEach(([productId, info]) => {
                products.push({
                    productId: productId,
                    url: info.url || info.detailUrl,
                    name: info.name || info.productName
                });
            });
        } else if (Array.isArray(productData)) {
            // 数组格式: [ { ... } ]
            productData.forEach(item => {
                products.push({
                    productId: item.id || item.productId,
                    url: item.url || item.detailUrl,
                    name: item.name || item.productName
                });
            });
        }

        return products.filter(product => product.url);
    }

    convertToProductFormat(result) {
        return {
            productId: result.productId,
            productName: result.productName,
            detailUrl: result.url,
            price: result.price,
            brand: result.brand,
            gender: result.gender,
            colors: result.colors || [],
            sizes: result.sizes || [],
            imageUrls: result.imageUrls || [],
            description: result.description,
            sizeChart: result.sizeChart && result.sizeChart.success ? {
                html: result.sizeChart.html || '',
                text: result.sizeChart.text || ''
            } : {},
            category: "",
            sku: "",
            status: "",
            priceText: result.price,
            mainImage: (result.imageUrls && result.imageUrls.length > 0) ? result.imageUrls[0] : "",
            originalPrice: "",
            currentPrice: "",
            _original_data: {
                商品链接: result.url,
                商品ID: result.productId,
                商品标题: result.productName,
                品牌名: result.brand,
                价格: result.price,
                性别: result.gender,
                颜色: result.colors || [],
                图片链接: result.imageUrls || [],
                尺码: result.sizes || [],
                详情页文字: result.description,
                尺码表: result.sizeChart,
                _scraper_info: result._scraper_info
            }
        };
    }

    async saveIntermediateResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const tempFile = path.join(this.outputDir, `temp_batch_unified_${timestamp}.json`);

        const outputData = {
            products: this.results,
            timestamp: new Date().toISOString(),
            processed_count: this.processedCount,
            total_count: this.totalProducts,
            status: 'intermediate'
        };

        fs.writeFileSync(tempFile, JSON.stringify(outputData, null, 2), 'utf8');
    }

    async saveFinalResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

        // 使用指定的输出路径或生成默认路径
        const finalFile = this.outputPath || path.join(this.outputDir, `batch_unified_final_${timestamp}.json`);

        const outputData = {
            products: this.results,
            timestamp: new Date().toISOString(),
            processed_count: this.processedCount,
            total_count: this.totalProducts,
            failed_urls: Array.from(this.failedUrls.entries()),
            status: 'completed',
            scraper_info: {
                version: 'unified_v1.0',
                processing_mode: 'batch_headless',
                advanced_size_chart: true
            },
            source_file: finalFile  // 新增：记录生成的文件路径
        };

        fs.writeFileSync(finalFile, JSON.stringify(outputData, null, 2), 'utf8');
        console.log(`💾 最终结果已保存: ${finalFile}`);
        return finalFile;  // 返回文件路径供主函数使用
    }
}

// 主函数 - 支持CLI参数
async function main() {
    // 解析命令行参数
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
        console.log('用法: node batch_unified_processor.js [选项]');
        console.log('');
        console.log('选项:');
        console.log('  --input <path>     指定输入文件路径（不指定则自动查找最新文件）');
        console.log('  --output <path>    指定输出文件路径');
        console.log('  --headless         使用无头模式（默认开启）');
        console.log('  --debug            开启调试模式（默认关闭）');
        console.log('  --timeout <ms>     设置超时时间（毫秒）');
        console.log('  --help, -h         显示帮助信息');
        console.log('');
        console.log('示例:');
        console.log('  node batch_unified_processor.js');
        console.log('  node batch_unified_processor.js --input "/path/to/input.json"');
        console.log('  node batch_unified_processor.js --output "/path/to/output.json" --debug');
        console.log('  node batch_unified_processor.js --input "data.json" --output "result.json"');
        process.exit(0);
    }

    // 提取参数
    const options = {};

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        switch (arg) {
            case '--input':
                if (i + 1 < args.length) {
                    options.inputFile = args[i + 1];
                    i++; // 跳过下一个参数
                } else {
                    console.error('❌ --input 参数需要指定文件路径');
                    process.exit(1);
                }
                break;

            case '--output':
                if (i + 1 < args.length) {
                    options.outputPath = args[i + 1];
                    i++; // 跳过下一个参数
                } else {
                    console.error('❌ --output 参数需要指定文件路径');
                    process.exit(1);
                }
                break;

            case '--headless':
                options.headless = true;
                break;

            case '--debug':
                options.debug = true;
                break;

            case '--timeout':
                if (i + 1 < args.length) {
                    const timeout = parseInt(args[i + 1]);
                    if (isNaN(timeout) || timeout <= 0) {
                        console.error('❌ --timeout 参数需要指定正整数（毫秒）');
                        process.exit(1);
                    }
                    options.timeout = timeout;
                    i++; // 跳过下一个参数
                } else {
                    console.error('❌ --timeout 参数需要指定时间（毫秒）');
                    process.exit(1);
                }
                break;

            default:
                if (arg.startsWith('--')) {
                    console.error(`❌ 未知参数: ${arg}`);
                    console.error('使用 --help 查看可用选项');
                    process.exit(1);
                }
                break;
        }
    }

    // 创建处理器实例
    const processor = new BatchUnifiedProcessor(options);

    // 检查输入文件
    if (!processor.inputFile) {
        console.error('❌ 未找到输入文件，请使用 --input 参数指定或确保目录中有可用的产品文件');
        process.exit(1);
    }

    if (!fs.existsSync(processor.inputFile)) {
        console.error(`❌ 输入文件不存在: ${processor.inputFile}`);
        process.exit(1);
    }

    console.log('🎯 使用的输入文件:', processor.inputFile);
    if (options.outputPath) {
        console.log('📁 输出路径:', options.outputPath);
    }

    try {
        // 执行批量处理并获取实际文件路径
        const actualOutputPath = await processor.processAllProducts();

        // 如果成功处理且有输出文件，输出下一步命令
        if (processor.processedCount > 0 && actualOutputPath) {
            console.log('\n✅ 批量处理完成！');
            console.log('\n🎯 接下来执行第二步：');
            console.log(`cd "/Users/sanshui/Desktop/CallawayJP"`);
            console.log(`python3 -m tongyong_feishu_update.run_pipeline "${actualOutputPath}" --verbose`);
        } else if (processor.processedCount > 0) {
            console.log('\n✅ 批量处理完成，但没有新文件生成（所有商品都已处理）');
        } else {
            console.log('\n⚠️ 没有商品需要处理');
        }

        process.exit(0);
    } catch (error) {
        console.error('\n❌ 批量处理异常退出:', error.message);
        console.error('错误详情:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = BatchUnifiedProcessor;