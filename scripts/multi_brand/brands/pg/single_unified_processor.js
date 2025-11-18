#!/usr/bin/env node

/**
 * 单个URL统一处理器 - 使用统一抓取器
 * 支持CLI参数: node single_unified_processor.js <url> [productId] [--output <path>]
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');

class SingleUnifiedProcessor {
    constructor(options = {}) {
        this.scraper = new UnifiedDetailScraper({
            headless: options.headless !== undefined ? options.headless : true, // 默认后台运行，可传 --headless=false 显示浏览器
            debug: options.debug !== undefined ? options.debug : true,
            timeout: options.timeout || 60000
        });
        this.outputPath = options.outputPath;
    }

    async processSingleUrl(url, productId = '') {
        console.log('🚀 开始单个URL统一处理...');
        console.log(`🌐 运行模式：${this.scraper.options.headless ? '后台运行（headless）' : '显示浏览器'}`);

        const extraData = productId ? { productId } : {};

        // 使用统一抓取器
        const result = await this.scraper.scrapeDetailPage(url, extraData);

        console.log('\n📊 抓取结果汇总:');
        console.log(`✅ 抓取成功: ${result.success}`);

        // 生成输出文件路径（只生成一次）
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const defaultPath = `/Users/sanshui/Desktop/CallawayJP/single_unified_${timestamp}.json`;
        const outputFile = this.outputPath || defaultPath;

        if (result.success) {
            console.log(`🎯 商品标题: ${result.productName}`);
            console.log(`🆔 商品ID: ${result.productId}`);
            console.log(`👕 性别: ${result.gender}`);
            console.log(`💰 价格: ${result.price}`);
            console.log(`🎨 颜色数量: ${result.colors?.length || 0}种`);
            console.log(`📏 尺码数量: ${result.sizes?.length || 0}个`);
            console.log(`🖼️ 图片数量: ${result.imageUrls?.length || 0}张`);

            if (result.sizeChart && result.sizeChart.success) {
                console.log(`📋 尺码表抓取成功! 方法: ${result.sizeChart.method}`);
                console.log(`📏 尺码表内容长度: ${result.sizeChart.text?.length || 0}字符`);
            } else {
                console.log(`❌ 尺码表抓取失败: ${result.sizeChart?.reason || '未知原因'}`);
            }

            // 转换为产品格式
            const productData = this.convertToProductFormat(result);

            // 保存结果
            const outputData = {
                products: {
                    [result.productId || 'unknown']: productData
                },
                source: 'pg',  // 品牌来源标识
                brandId: 'pg',  // 品牌ID
                timestamp: new Date().toISOString(),
                scraper_info: result._scraper_info,
                source_file: outputFile  // 记录生成的文件路径
            };

            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');

            console.log(`\n💾 结果已保存: ${outputFile}`);

            if (result.sizeChart && result.sizeChart.success) {
                console.log('\n📋 尺码表内容预览:');
                const preview = result.sizeChart.text.substring(0, 300);
                console.log(preview + (result.sizeChart.text.length > 300 ? '...' : ''));
            }
        } else {
            console.log(`❌ 错误信息: ${result.error}`);
            // 失败时也保存空结果，确保文件路径一致性
            const outputData = {
                products: {},
                timestamp: new Date().toISOString(),
                scraper_info: result._scraper_info,
                source_file: outputFile,
                error: result.error
            };
            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');
            console.log(`\n💾 错误结果已保存: ${outputFile}`);
        }

        console.log('\n✅ 单个URL统一处理完成！');

        // 返回包含实际输出文件路径的结果
        return {
            ...result,
            outputFile  // 新增：返回实际使用的文件路径
        };
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
            category: result.category || "",
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
                尺码表: result.sizeChart
            }
        };
    }
}

// 解析命令行参数的辅助函数
function parseArgs(args) {
    const result = {
        targetUrl: '',
        productId: '',
        outputPath: '',
        help: false
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        if (arg === '--help' || arg === '-h') {
            result.help = true;
            return result;
        }

        if (arg.startsWith('--output=')) {
            result.outputPath = arg.substring(9);
        } else if (arg === '--output' || arg === '-o') {
            if (i + 1 < args.length) {
                result.outputPath = args[i + 1];
                i++; // 跳过下一个参数
            } else {
                console.error('❌ --output 参数需要指定路径');
                process.exit(1);
            }
        } else if (!result.targetUrl) {
            result.targetUrl = arg;
        } else if (!result.productId) {
            result.productId = arg;
        } else {
            console.error(`❌ 未知参数: ${arg}`);
            process.exit(1);
        }
    }

    return result;
}

// 主函数 - 支持CLI参数
async function main() {
    // 解析命令行参数
    const args = process.argv.slice(2);

    if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
        console.log('用法: node single_unified_processor.js <url> [productId] [选项]');
        console.log('');
        console.log('参数:');
        console.log('  url        要处理的商品URL');
        console.log('  productId  可选的商品ID，如果不提供将自动从URL提取');
        console.log('');
        console.log('选项:');
        console.log('  -o, --output <path>   输出文件路径');
        console.log('  -h, --help            显示帮助信息');
        console.log('');
        console.log('示例:');
        console.log('  node single_unified_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/"');
        console.log('  node single_unified_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/" "LG5FST81M"');
        console.log('  node single_unified_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/" --output "/path/to/output.json"');
        console.log('  node single_unified_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/" -o "/tmp/result.json"');
        console.log('  node single_unified_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/" --output=/tmp/result.json');
        process.exit(0);
    }

    const parsed = parseArgs(args);

    if (!parsed.targetUrl) {
        console.error('❌ 请提供要处理的URL');
        process.exit(1);
    }

    // 从URL提取商品ID - 如果没有提供的话
    let finalProductId = parsed.productId;
    if (!finalProductId) {
        const extractProductId = (url) => {
            // 从多个可能的位置提取商品ID
            const patterns = [
                /\/([A-Z0-9]+)\/$/,           // 以商品ID结尾
                /commodity\/[^\/]+\/([A-Z0-9]+)\//, // commodity/xxx/PRODUCTID/
                /LE([A-Z0-9]+)/,           // LE开头的商品ID
                /([A-Z0-9]{10,})/          // 10位以上的字母数字组合
            ];

            for (const pattern of patterns) {
                const match = url.match(pattern);
                if (match) {
                    return match[1] || match[0];
                }
            }
            return '';
        };
        finalProductId = extractProductId(parsed.targetUrl);
    }

    // 创建处理器实例
    const processor = new SingleUnifiedProcessor({
        outputPath: parsed.outputPath
    });

    console.log('🎯 使用的输入URL:', parsed.targetUrl);
    console.log('🆔 提取的商品ID:', finalProductId);
    if (parsed.outputPath) {
        console.log('📁 输出路径:', parsed.outputPath);
    }

    // 执行处理
    const result = await processor.processSingleUrl(parsed.targetUrl, finalProductId);

    if (result.success) {
        console.log('\n📁 输出文件:', result.outputFile);
        console.log('\n✅ URL处理完成！');
        console.log('\n🎯 接下来执行第二步：');
        console.log(`cd "/Users/sanshui/Desktop/CallawayJP"`);
        console.log(`python3 -m tongyong_feishu_update.run_pipeline "${result.outputFile}" --verbose`);
    } else {
        console.log('\n📁 输出文件:', result.outputFile);
        console.log('\n❌ URL处理失败，但错误信息已保存到文件');
    }

    // 退出码
    process.exit(result.success ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = SingleUnifiedProcessor;