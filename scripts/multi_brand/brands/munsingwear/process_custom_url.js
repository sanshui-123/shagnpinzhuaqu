#!/usr/bin/env node

/**
 * 处理用户指定的URL
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');

class CustomUrlProcessor {
    constructor() {
        this.scraper = new UnifiedDetailScraper({
            headless: false, // 显示浏览器，便于调试
            debug: true,
            timeout: 60000
        });
    }

    async processUrl(url) {
        console.log('🚀 开始处理指定URL...');
        console.log('🌐 目标URL:', url);
        console.log('🌐 运行模式：调试模式（显示浏览器）');

        // 提取商品ID
        const extractProductId = (url) => {
            const match = url.match(/\/([A-Z0-9]+)\/$/);
            return match ? match[1] : '';
        };
        const productId = extractProductId(url);

        const extraData = productId ? { productId } : {};

        // 使用统一抓取器
        const result = await this.scraper.scrapeDetailPage(url, extraData);

        console.log('\n📊 抓取结果汇总:');
        console.log(`✅ 抓取成功: ${result.success}`);

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
                timestamp: new Date().toISOString(),
                scraper_info: result._scraper_info
            };

            const outputFile = `/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/custom_url_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');

            console.log(`\n💾 结果已保存: ${outputFile}`);
            console.log(`📁 文件名: ${outputFile.split('/').pop()}`);

            if (result.sizeChart && result.sizeChart.success) {
                console.log('\n📋 尺码表内容预览:');
                const preview = result.sizeChart.text.substring(0, 300);
                console.log(preview + (result.sizeChart.text.length > 300 ? '...' : ''));
            }

            return outputFile;
        } else {
            console.log(`❌ 错误信息: ${result.error}`);
            return null;
        }
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
                尺码表: result.sizeChart
            }
        };
    }
}

// 主函数 - 处理用户指定的URL
async function main() {
    const processor = new CustomUrlProcessor();

    // 使用用户指定的URL
    const targetUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1452EW028267/';

    console.log('🎯 处理URL:', targetUrl);
    const outputFile = await processor.processUrl(targetUrl);

    if (outputFile) {
        console.log('\n✅ URL处理完成！');
        console.log('\n🎯 接下来执行第二步：');
        console.log(`cd "/Users/sanshui/Desktop/CallawayJP"`);
        console.log(`python3 -m tongyong_feishu_update.run_pipeline "${outputFile}" --verbose`);
    }

    // 退出码
    process.exit(outputFile ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = CustomUrlProcessor;