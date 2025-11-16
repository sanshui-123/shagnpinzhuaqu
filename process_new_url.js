#!/usr/bin/env node

/**
 * 处理新URL的临时脚本
 */

const UnifiedDetailScraper = require('./scripts/multi_brand/brands/lecoqgolf/unified_detail_scraper');
const fs = require('fs');

class NewUrlProcessor {
    constructor() {
        this.scraper = new UnifiedDetailScraper({
            headless: false, // 显示浏览器，便于调试
            debug: true,
            timeout: 60000
        });
    }

    async processUrl(url) {
        console.log('🎯 处理URL:', url);
        console.log('🆔 提取的商品ID:', url.match(/\/([A-Z0-9]+)\//)?.[1] || 'Unknown');

        console.log('🚀 开始单个URL统一处理...');
        console.log('🌐 运行模式：调试模式（显示浏览器）');

        const result = await this.scraper.scrapeDetailPage(url, {});

        console.log('\n📊 抓取结果汇总:');
        console.log(`✅ 抓取成功: ${result.success}`);

        if (result.success && result.data) {
            const product = result.data;
            console.log(`🎯 商品标题: ${product.productName}`);
            console.log(`🆔 商品ID: ${product.productId}`);
            console.log(`👕 性别: ${product.gender}`);
            console.log(`💰 价格: ${product.price}`);
            console.log(`🎨 颜色数量: ${product.colors ? product.colors.length : 0}种`);
            console.log(`📏 尺码数量: ${product.sizes ? product.sizes.length : 0}个`);
            console.log(`🖼️ 图片数量: ${product.imageUrls ? product.imageUrls.length : 0}张`);

            if (result.sizeChartContent) {
                console.log(`📋 尺码表抓取成功! 方法: ${result.sizeChartMethod}`);
                console.log(`📏 尺码表内容长度: ${result.sizeChartContent.length}字符`);
            }

            // 生成文件名
            const timestamp = new Date().toISOString().replace(/[:.]*/g, '-');
            const filename = `single_unified_${timestamp}.json`;

            // 保存结果
            const finalData = {
                products: {
                    [product.productId]: product
                },
                timestamp: timestamp,
                scraper_info: {
                    version: 'unified_v1.0',
                    debug_mode: true,
                    size_chart_method: result.sizeChartMethod,
                    processing_time: new Date().toISOString()
                }
            };

            fs.writeFileSync(filename, JSON.stringify(finalData, null, 2), 'utf8');
            console.log(`💾 结果已保存: ${filename}`);

            if (result.sizeChartContent) {
                console.log('\n📋 尺码表内容预览:');
                console.log(result.sizeChartContent.substring(0, 200) + '...');
            }

            console.log('\n✅ 单个URL统一处理完成!');
            console.log('\n🎯 接下来执行第二步：');
            console.log(`cd "/Users/sanshui/Desktop/CallawayJP"`);
            console.log(`python3 -m tongyong_feishu_update.run_pipeline "${filename}" --verbose`);

            return filename;
        } else {
            console.log('❌ 抓取失败');
            return null;
        }
    }
}

// 主函数
async function main() {
    const url = process.argv[2] || 'https://store.descente.co.jp/commodity/SDSC0140D/LE1452EW028267/';

    const processor = new NewUrlProcessor();
    await processor.processUrl(url);
}

// 运行主函数
if (require.main === module) {
    main().catch(console.error);
}