#!/usr/bin/env node

/**
 * PG 库存抓取测试脚本
 * 用于验证 unified_detail_scraper.js 的 extractVariantInventory 方法
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');

async function testInventory() {
    console.log('🧪 开始测试 PG 库存抓取功能...\n');

    // 测试 URL（用户提供的）
    const testUrls = [
        'https://mix.tokyo/products/0536170151',
        'https://mix.tokyo/products/0536120021'
    ];

    const scraper = new UnifiedDetailScraper({
        headless: false,  // 显示浏览器，方便调试
        debug: true,      // 开启调试模式
        timeout: 60000
    });

    for (let i = 0; i < testUrls.length; i++) {
        const url = testUrls[i];
        console.log(`\n${'='.repeat(60)}`);
        console.log(`测试 URL ${i + 1}/${testUrls.length}: ${url}`);
        console.log('='.repeat(60));

        try {
            const result = await scraper.scrapeDetailPage(url, {
                productId: `TEST_${i + 1}`
            });

            if (result.success) {
                console.log('\n✅ 抓取成功！\n');
                console.log('📦 商品基本信息:');
                console.log(`  商品ID: ${result.productId}`);
                console.log(`  商品名称: ${result.productName}`);
                console.log(`  价格: ${result.price}`);
                console.log(`  性别: ${result.gender}`);

                console.log('\n🎨 颜色列表:');
                console.log(`  ${result.colors.join(', ')}`);

                console.log('\n📏 尺码列表:');
                console.log(`  ${result.sizes.join(', ')}`);

                console.log('\n📦 库存详情 (variantInventory):');
                if (result.variantInventory && result.variantInventory.length > 0) {
                    console.log(`  总共 ${result.variantInventory.length} 个变体\n`);

                    // 按颜色分组显示
                    const byColor = {};
                    result.variantInventory.forEach(v => {
                        if (!byColor[v.color]) {
                            byColor[v.color] = [];
                        }
                        byColor[v.color].push(v);
                    });

                    for (const [color, variants] of Object.entries(byColor)) {
                        console.log(`  颜色: ${color}`);
                        variants.forEach(v => {
                            const status = v.inStock ? '✅ 有货' : '❌ 无货';
                            console.log(`    尺码 ${v.size}: ${status}`);
                        });
                        console.log('');
                    }

                    // 统计
                    const inStockCount = result.variantInventory.filter(v => v.inStock).length;
                    const outOfStockCount = result.variantInventory.length - inStockCount;
                    console.log(`  统计: ${inStockCount} 个有货, ${outOfStockCount} 个缺货`);
                } else {
                    console.log('  ⚠️ 未找到库存信息');
                }

                // 保存结果到文件
                const outputPath = `/tmp/pg_inventory_test_${i + 1}.json`;
                fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf8');
                console.log(`\n💾 完整结果已保存到: ${outputPath}`);

            } else {
                console.log(`\n❌ 抓取失败: ${result.error}`);
            }

        } catch (error) {
            console.log(`\n❌ 测试失败: ${error.message}`);
            console.error(error);
        }

        // 测试间隔
        if (i < testUrls.length - 1) {
            console.log('\n⏳ 等待 3 秒后继续下一个测试...');
            await new Promise(resolve => setTimeout(resolve, 3000));
        }
    }

    console.log('\n' + '='.repeat(60));
    console.log('🎉 所有测试完成！');
    console.log('='.repeat(60));
}

// 运行测试
testInventory().catch(console.error);
