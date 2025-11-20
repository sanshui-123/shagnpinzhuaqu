#!/usr/bin/env node

/**
 * 测试 unified_detail_scraper 是否正确提取品牌货号
 */

const UnifiedDetailScraper = require('./unified_detail_scraper.js');

async function testScraper() {
    console.log('🧪 测试 UnifiedDetailScraper 提取品牌货号...\n');

    const scraper = new UnifiedDetailScraper({
        headless: true,
        debug: false
    });

    // 测试样例URL
    const testUrls = [
        {
            url: 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM011353/',
            urlCode: 'LE1872EM011353',
            expectedBrandCode: 'LG5SSWD2M'
        },
        {
            url: 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM009639/',
            urlCode: 'LE1872EM009639',
            expectedBrandCode: 'LG4FST30M'
        }
    ];

    for (const test of testUrls) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`🔍 测试 URL: ${test.url}`);
        console.log(`   URL 编号: ${test.urlCode}`);
        console.log(`   期望品牌货号: ${test.expectedBrandCode}`);
        console.log(`${'='.repeat(80)}\n`);

        const result = await scraper.scrapeDetailPage(test.url, {
            productId: test.urlCode // 传入URL编号作为fallback
        });

        if (result.success) {
            console.log(`\n✅ 抓取成功！`);
            console.log(`   提取的 productId: ${result.productId}`);
            console.log(`   商品名称: ${result.productName}`);
            console.log(`   价格: ${result.price}`);
            console.log(`   性别: ${result.gender}`);

            // 验证结果
            if (result.productId === test.expectedBrandCode) {
                console.log(`\n✅ 验证通过！productId 是品牌货号（${test.expectedBrandCode}），不是 URL 编号`);
            } else if (result.productId === test.urlCode) {
                console.log(`\n⚠️ 警告！productId 仍然是 URL 编号（${test.urlCode}），未提取到品牌货号`);
                console.log(`   期望: ${test.expectedBrandCode}`);
                console.log(`   实际: ${result.productId}`);
            } else {
                console.log(`\n❓ 未知结果: ${result.productId}`);
            }
        } else {
            console.log(`\n❌ 抓取失败: ${result.error}`);
        }
    }

    console.log(`\n${'='.repeat(80)}`);
    console.log('🎉 测试完成！');
    console.log(`${'='.repeat(80)}\n`);
}

testScraper().catch(error => {
    console.error('❌ 测试失败:', error);
    process.exit(1);
});
