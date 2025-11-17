#!/usr/bin/env node

/**
 * 单个URL自定义处理器 - 处理指定的URL
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');

class SingleCustomProcessor {
    constructor() {
        this.scraper = new UnifiedDetailScraper({
            headless: false, // 显示浏览器，便于调试
            debug: true,
            timeout: 60000
        });
    }

    async processSingleUrl(url, productId = '') {
        console.log('🚀 开始处理指定URL...');
        console.log('🌐 目标URL:', url);
        console.log('🌐 运行模式：调试模式（显示浏览器）');

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

            const outputFile = `/Users/sanshui/Desktop/CallawayJP/custom_url_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');

            console.log(`\n💾 结果已保存: ${outputFile}`);

            if (result.sizeChart && result.sizeChart.success) {
                console.log('\n📋 尺码表内容预览:');
                const preview = result.sizeChart.text.substring(0, 500);
                console.log(preview + (result.sizeChart.text.length > 500 ? '...' : ''));
            }
        } else {
            console.log(`❌ 错误信息: ${result.error}`);
        }

        console.log('\n✅ 指定URL处理完成！');
        return result;
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
    const processor = new SingleCustomProcessor();

    // 使用用户指定的URL
    const targetUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1452EW028231/';
    const extractProductId = (url) => {
        const match = url.match(/\/([A-Z0-9]+)\/$/);
        return match ? match[1] : '';
    };
    const productId = extractProductId(targetUrl);

    const result = await processor.processSingleUrl(targetUrl, productId);

    // 退出码
    process.exit(result.success ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = SingleCustomProcessor;