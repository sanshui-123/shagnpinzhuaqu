#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 详情页批量处理器
 * 纯后台运行，批量处理330个商品
 */

const fs = require('fs');
const path = require('path');
const EnhancedDetailScraper = require('./enhanced_detail_scraper');

class BatchDetailProcessor {
    constructor() {
        this.scraper = new EnhancedDetailScraper();
        this.inputFile = './golf_content/lecoqgolf/lecoqgolf_products_2025-11-12T16-18-23-072Z.json';
        this.outputDir = './golf_content/lecoqgolf/';
        this.results = [];
        this.processedCount = 0;
        this.totalProducts = 0;
        this.errors = [];

        // 🚀 借鉴卡拉威：添加状态管理
        this.statusFile = './batch_status.json';
        this.loadStatus();
    }

    // 🚀 借鉴卡拉威：状态管理
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
                lastUpdate: new Date().toISOString()
            };
            fs.writeFileSync(this.statusFile, JSON.stringify(statusData, null, 2));
        } catch (error) {
            console.warn('⚠️ 状态文件保存失败:', error.message);
        }
    }

    // 🚀 借鉴卡拉威：检查URL是否已处理
    isUrlProcessed(url) {
        return this.processedUrls.has(url);
    }

    // 🚀 借鉴卡拉威：标记URL已处理
    markUrlProcessed(url) {
        this.processedUrls.add(url);
        this.failedUrls.delete(url); // 从失败列表中移除
        this.saveStatus();
    }

    // 🚀 借鉴卡拉威：标记URL失败
    markUrlFailed(url, error) {
        const failCount = this.failedUrls.get(url) || 0;
        this.failedUrls.set(url, failCount + 1);
        this.saveStatus();
    }

    async processAllProducts() {
        console.log('🚀 开始批量处理Le Coq Sportif Golf详情页...');
        console.log('🌐 运行模式：纯后台模式（无界面）');

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

            // 🚀 借鉴卡拉威：增量更新逻辑
            console.log('\n🔄 开始批量处理详情页...\n');

            // 过滤已处理的URL
            const unprocessedProducts = products.filter(product => {
                if (!product.url) {
                    console.log(`⚠️ 跳过无URL的产品: ${product.title || 'Unknown'}`);
                    return false;
                }

                if (this.isUrlProcessed(product.url)) {
                    console.log(`🔄 跳过已处理: ${product.productId || product.title}`);
                    return false;
                }

                return true;
            });

            console.log(`📊 状态统计:`);
            console.log(`   - 总产品数: ${products.length}`);
            console.log(`   - 已处理: ${products.length - unprocessedProducts.length}`);
            console.log(`   - 待处理: ${unprocessedProducts.length}`);

            if (unprocessedProducts.length === 0) {
                console.log('✅ 所有产品已处理完成！');
                return;
            }

            // 处理未处理的产品
            console.log(`🚀 开始处理 ${unprocessedProducts.length} 个新产品`);

            for (let i = 0; i < unprocessedProducts.length; i++) {
                const product = unprocessedProducts[i];
                await this.processProduct(product, i + 1, unprocessedProducts.length);
            }

            // 3. 保存结果
            await this.saveResults();

            console.log('\n✅ 批量处理完成！');
            this.printSummary();

        } catch (error) {
            console.error('❌ 批量处理失败:', error.message);
            this.errors.push({ type: 'batch_error', message: error.message });
            await this.saveResults();
        }
    }

    async loadProductList() {
        if (!fs.existsSync(this.inputFile)) {
            console.log('📁 寻找最新的商品列表文件...');
            const files = fs.readdirSync(this.outputDir)
                .filter(file => file.startsWith('lecoqgolf_products_') && file.endsWith('.json'))
                .sort()
                .reverse();

            if (files.length > 0) {
                this.inputFile = path.join(this.outputDir, files[0]);
                console.log(`📁 使用文件: ${this.inputFile}`);
            } else {
                throw new Error('未找到商品列表文件');
            }
        }

        const content = fs.readFileSync(this.inputFile, 'utf8');
        return JSON.parse(content);
    }

    extractProductUrls(productData) {
        const products = [];

        if (productData.results && productData.results.length > 0) {
            productData.results.forEach(collection => {
                if (collection.products && collection.products.length > 0) {
                    collection.products.forEach(product => {
                        if (product.url && product.url.startsWith('http')) {
                            products.push({
                                id: product.id,
                                url: product.url,
                                title: product.title,
                                collection: collection.collection
                            });
                        }
                    });
                }
            });
        }

        return products;
    }

    async processProduct(product, index, total) {
        try {
            console.log(`[${index}/${total}] 📊 处理商品: ${product.title.substring(0, 50)}...`);

            // 抓取详情页数据
            const detailData = await this.scraper.scrapeDetailPage(product.url);

            // 转换为飞书格式
            const feishuData = this.convertToFeishuFormat(detailData, product);

            // 添加到结果列表
            this.results.push(feishuData);
            this.processedCount++;

            // 🚀 借鉴卡拉威：标记URL已处理
            this.markUrlProcessed(product.url);

            console.log(`✅ [${index}/${total}] 成功处理 - 商品编号: ${detailData.productCode}`);

            // 添加延迟避免过于频繁的请求
            if (index < total) {
                await this.delay(2000); // 2秒延迟
            }

        } catch (error) {
            console.log(`❌ [${index}/${total}] 处理失败: ${error.message}`);

            // 🚀 借鉴卡拉威：标记URL失败
            this.markUrlFailed(product.url, error.message);

            this.errors.push({
                product: product,
                error: error.message,
                index: index
            });

            // 即使失败也要继续处理下一个
            if (index < total) {
                await this.delay(3000); // 错误后延长延迟
            }
        }
    }

    convertToFeishuFormat(detailData, product) {
        const feishuRecord = {
            // 基础信息 - 使用新的数据结构
            '商品标题': detailData.商品标题 || '',
            '品牌': detailData.品牌名 || 'Le Coq公鸡乐卡克',
            '商品编号': detailData.商品ID || '',
            '性别': detailData.性别 || '',
            '价格': detailData.价格 || '',
            '详情页链接': detailData.商品链接 || '',

            // 分类信息 - 暂时留空，因为新规则不抓取衣服分类
            '一级分类': '',
            '二级分类': '',
            '三级分类': '',
            '四级分类': '',
            '五级分类': '',

            // 产品规格 - 使用新的数据结构
            '颜色选项': (detailData.颜色 && detailData.颜色.map(c => c.name).join(', ')) || '',
            '颜色数量': detailData.颜色 ? detailData.颜色.length : 0,
            '首个颜色': (detailData.颜色 && detailData.颜色.find(c => c.isFirstColor)?.name) || '',
            '尺寸选项': (detailData.尺码 && detailData.尺码.join(', ')) || '',
            '尺寸数量': detailData.尺码 ? detailData.尺码.length : 0,

            // 库存信息 - 新数据结构中没有库存统计，设为默认值
            '总尺码数': detailData.尺码 ? detailData.尺码.length : 0,
            '有库存尺码': detailData.尺码 ? detailData.尺码.length : 0, // 假设都有库存
            '缺货尺码': 0,
            '库存率(%)': 100,

            // 图片信息 - 使用新的数据结构（只有第一个颜色的图片）
            '图片总数': detailData.图片链接 ? detailData.图片链接.length : 0,
            '首个颜色图片数': detailData.图片链接 ? detailData.图片链接.length : 0,
            '其他颜色图片数': 0, // 新规则只抓取第一个颜色
            '主要图片链接': (detailData.图片链接 && detailData.图片链接[0]) || '',
            '所有图片链接': (detailData.图片链接 && detailData.图片链接.slice(0, 10).join('\n') + (detailData.图片链接.length > 10 ? `\n... 还有 ${detailData.图片链接.length - 10} 张` : '')) || '',

            // 功能特性 - 新数据结构中没有这些字段，设为默认值
            '核心功能': '',
            '材质信息': '',
            '所有功能': '',

            // 翻译内容 - 新规则不包含翻译，设为空
            '详情页译文': '',
            '尺码表译文': '',

            // 原始内容 - 使用新的数据结构
            '标题原文': detailData.商品标题 || '',
            '详情页原文': detailData.详情页文字 || '',
            '尺码表原文': (detailData.尺码表 && detailData.尺码表.text) || '',

            // 时间戳
            '抓取时间': new Date().toISOString(),
            '更新时间': new Date().toISOString(),

            // 系统信息
            '数据来源': 'lecoqgolf',
            '状态': '待同步',
            '处理状态': 'success'
        };

        return feishuRecord;
    }

    async saveResults() {
        // 确保输出目录存在
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

        // 将records转换为products格式
        const products = {};
        this.results.forEach(product => {
            const productId = product.商品编号 || product.productId || `product_${Math.random().toString(36).substr(2, 9)}`;
            products[productId] = {
                productId: product.商品编号 || product.productId,
                productName: product.商品标题 || product.productName,
                detailUrl: product.详情页链接 || product.detailUrl,
                price: product.价格 || product.price,
                brand: product.品牌 || product.brand,
                category: product.一级分类 || product.category,
                gender: product.性别 === "男" ? "男士" : product.性别 === "女" ? "女士" : "",
                description: product.描述 || product.description || "",
                colors: product.颜色选项 ? product.颜色选项.split(', ').filter(c => c.trim()) : [],
                sizes: product.尺寸选项 ? product.尺寸选项.split(', ').filter(s => s.trim()) : [],
                imageUrls: product.所有图片链接 ? product.所有图片链接.split('\n').filter(url => url.trim()) : [],
                sizeChart: product.尺码表原文 ? { text: product.尺码表原文 } : {},
                scrapeInfo: product.抓取信息 || {
                    totalColors: product.颜色数量 || 0,
                    totalSizes: product.尺寸数量 || 0,
                    totalImages: product.图片总数 || 0
                }
            };
        });

        // 保存飞书格式数据
        const feishuFile = `${this.outputDir}batch_feishu_results_${timestamp}.json`;
        const outputData = {
            products: products,
            total: this.results.length,
            processed: this.processedCount,
            failed: this.errors.length,
            errors: this.errors,
            timestamp: new Date().toISOString(),
            brand: 'lecoqgolf',
            batchMode: true
        };

        fs.writeFileSync(feishuFile, JSON.stringify(outputData, null, 2));
        console.log(`💾 飞书格式数据已保存: ${feishuFile}`);

        // 保存处理报告
        const reportFile = `${this.outputDir}batch_processing_report_${timestamp}.txt`;
        const report = this.generateReport();
        fs.writeFileSync(reportFile, report);
        console.log(`📄 处理报告已保存: ${reportFile}`);

        return { feishuFile, reportFile };
    }

    generateReport() {
        const report = [
            `=== Le Coq Sportif Golf 批量详情页处理报告 ===`,
            ``,
            `处理时间: ${new Date().toISOString()}`,
            `运行模式: 纯后台模式`,
            ``,
            `📊 处理统计:`,
            `- 总商品数: ${this.totalProducts}`,
            `- 成功处理: ${this.processedCount}`,
            `- 处理失败: ${this.errors.length}`,
            `- 成功率: ${Math.round((this.processedCount / this.totalProducts) * 100)}%`,
            ``,
            `📋 数据质量统计:`,
            `- 平均图片数: ${this.calculateAverageImages()}`,
            `- 平均颜色数: ${this.calculateAverageColors()}`,
            `- 平均尺码数: ${this.calculateAverageSizes()}`,
            ``,
            `❌ 错误记录:`,
            ...this.errors.map((err, i) => [
                `${i + 1}. 商品ID: ${err.product.id}`,
                `   URL: ${err.product.url}`,
                `   错误: ${err.error}`
            ]).flat()
        ].join('\n');

        return report;
    }

    calculateAverageImages() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['图片总数'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    calculateAverageColors() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['颜色数量'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    calculateAverageSizes() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['尺寸数量'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    printSummary() {
        console.log('\n📊 处理总结:');
        console.log(`✅ 成功处理: ${this.processedCount} 个商品`);
        console.log(`❌ 处理失败: ${this.errors.length} 个商品`);
        console.log(`📈 成功率: ${Math.round((this.processedCount / this.totalProducts) * 100)}%`);
        console.log(`🖼️ 平均图片: ${this.calculateAverageImages()} 张/商品`);
        console.log(`🎨 平均颜色: ${this.calculateAverageColors()} 个/商品`);
        console.log(`📏 平均尺码: ${this.calculateAverageSizes()} 个/商品`);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 运行批量处理
if (require.main === module) {
    const processor = new BatchDetailProcessor();

    processor.processAllProducts()
        .then(() => {
            console.log('\n🎉 批量处理完成！');
            console.log('📁 检查输出目录以获取飞书格式数据');
        })
        .catch(error => {
            console.error('❌ 批量处理失败:', error);
            process.exit(1);
        });
}

module.exports = BatchDetailProcessor;