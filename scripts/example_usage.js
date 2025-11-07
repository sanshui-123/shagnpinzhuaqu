#!/usr/bin/env node

/**
 * CallawayJP 产品详情抓取脚本使用示例
 */

const { main } = require('./scrape_product_detail.js');

async function runExamples() {
    console.log('🚀 CallawayJP 产品详情抓取脚本使用示例\n');

    const examples = [
        {
            name: '女士外套',
            url: 'https://www.callawaygolf.jp/womens/tops/outer/C25215200_.html?pid=C25215200_1031_S',
            productId: 'C25215200'
        },
        {
            name: '男士Polo衫',
            url: 'https://www.callawaygolf.jp/mens/tops/polo/C25128100_.html',
            productId: 'C25128100'  // 自动提取
        }
    ];

    for (const example of examples) {
        console.log(`\n📦 抓取示例: ${example.name}`);
        console.log(`🔗 URL: ${example.url}`);
        console.log(`🏷️  产品ID: ${example.productId}`);
        
        try {
            // 模拟命令行参数
            process.argv = [
                'node',
                'scrape_product_detail.js',
                '--url', example.url,
                '--product-id', example.productId,
                '--output-dir', 'CallawayJP/results'
            ];

            console.log('⏳ 开始抓取...');
            const result = await main();
            console.log(`✅ 抓取完成: ${result}`);
            
        } catch (error) {
            console.error(`❌ 抓取失败: ${error.message}`);
        }
        
        console.log('─'.repeat(60));
    }

    console.log('\n🎉 所有示例执行完成！');
    console.log('\n📋 使用说明：');
    console.log('node scrape_product_detail.js --url <产品URL> [选项]');
    console.log('\n📁 输出目录：CallawayJP/results/');
    console.log('📊 文件格式：product_detail_<产品ID>_<时间戳>.json');
}

// 如果直接运行此文件
if (require.main === module) {
    runExamples().catch(console.error);
}

module.exports = { runExamples };