#!/usr/bin/env node

/**
 * 测试修改后的字段映射功能
 */

const { EnhancedDetailScraper } = require('./enhanced_detail_scraper.js');

async function testFieldMapping() {
    const scraper = new EnhancedDetailScraper();
    const testUrl = "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012903/";

    console.log('🔍 测试字段映射功能...');
    console.log('URL:', testUrl);

    try {
        const results = await scraper.scrapeDetailPage(testUrl);

        console.log('\n✅ 抓取成功！输出字段检查：\n');

        // 检查原有字段
        console.log('📋 原有字段（第一部分）：');
        console.log('  - 商品链接:', results.商品链接 ? '✅ 存在' : '❌ 缺失');
        console.log('  - 商品ID:', results.商品ID ? '✅ 存在' : '❌ 缺失');
        console.log('  - 商品标题:', results.商品标题 ? '✅ 存在' : '❌ 缺失');
        console.log('  - 品牌名:', results.品牌名 ? '✅ 存在' : '❌ 缺失');
        console.log('  - 价格:', results.价格 ? '✅ 存在' : '❌ 缺失');

        // 检查新增映射字段
        console.log('\n📋 新增映射字段（第二部分期望）：');
        console.log('  - 详情页链接:', results['详情页链接'] ? '✅ 存在' : '❌ 缺失');
        console.log('  - 商品编号:', results['商品编号'] ? '✅ 存在' : '❌ 缺失');
        console.log('  - productName:', results.productName ? '✅ 存在' : '❌ 缺失');
        console.log('  - productId:', results.productId ? '✅ 存在' : '❌ 缺失');
        console.log('  - priceText:', results.priceText ? '✅ 存在' : '❌ 缺失');
        console.log('  - detailUrl:', results.detailUrl ? '✅ 存在' : '❌ 缺失');

        console.log('\n📊 字段值验证：');
        console.log('  商品链接:', results.商品链接);
        console.log('  详情页链接:', results['详情页链接']);
        console.log('  商品ID:', results.商品ID);
        console.log('  商品编号:', results['商品编号']);
        console.log('  价格:', results.价格);
        console.log('  priceText:', results.priceText);

        // 保存完整结果
        const fs = require('fs');
        fs.writeFileSync('./test_enhanced_mapping_result.json', JSON.stringify(results, null, 2), 'utf8');
        console.log('\n📁 完整结果已保存到: test_enhanced_mapping_result.json');

    } catch (error) {
        console.error('❌ 测试失败:', error.message);
    }
}

testFieldMapping();