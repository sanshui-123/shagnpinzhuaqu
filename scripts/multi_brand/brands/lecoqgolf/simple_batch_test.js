#!/usr/bin/env node

/**
 * 简化的批量详情页测试
 * 纯后台运行，测试前3个商品
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

class SimpleBatchTester {
    constructor() {
        this.outputDir = './golf_content/lecoqgolf/';
        this.results = [];
    }

    async runSimpleTest() {
        console.log('🚀 开始简化批量测试...');
        console.log('🌐 纯后台模式运行');

        const testUrls = [
            'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
            'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012623/',
            'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012561/'
        ];

        console.log(`📋 测试 ${testUrls.length} 个商品`);

        const browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });

        try {
            for (let i = 0; i < testUrls.length; i++) {
                console.log(`\n[${i + 1}/${testUrls.length}] 🔍 处理商品 ${i + 1}`);
                    await this.processSingle(browser, testUrls[i], i + 1);
            }
        } finally {
            await browser.close();
        }

        await this.saveResults();
        console.log('\n✅ 测试完成！');

    }

    async processSingle(browser, url, index) {
        const page = await browser.newPage();

        try {
            console.log(`  📄 访问: ${url}`);

            // 访问页面
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 60000
            });

            await page.waitForTimeout(5000);

            // 提取基础信息
            const data = await page.evaluate(() => {
                const title = document.querySelector('h1, .commodityName, .productName')?.textContent.trim() || '';
                const price = document.querySelector('.price')?.textContent.trim() || '';
                const images = Array.from(document.querySelectorAll('img[src*="LE/LE"]')).map(img => img.src).slice(0, 3);

                // 提取商品编号
                let productCode = '';
                const sizeChart = document.querySelector('table');
                if (sizeChart) {
                    const text = sizeChart.textContent;
                    const lgMatch = text.match(/\b(LG[A-Z0-9]{6,})\b/);
                    if (lgMatch) productCode = lgMatch[1];
                }

                return {
                    title,
                    price,
                    productCode,
                    images: images.length,
                    url: window.location.href
                };
            });

            console.log(`  ✅ 成功: ${data.title.substring(0, 30)}...`);
            console.log(`  🏷️ 编号: ${data.productCode || '未找到'}`);
            console.log(`  💰 价格: ${data.price}`);
            console.log(`  🖼️ 图片: ${data.images}张`);

            this.results.push({
                index,
                url: url,
                title: data.title,
                price: data.price,
                productCode: data.productCode,
                imagesCount: data.images,
                status: 'success',
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.log(`  ❌ 失败: ${error.message}`);
            this.results.push({
                index,
                url: url,
                error: error.message,
                status: 'failed',
                timestamp: new Date().toISOString()
            });
        } finally {
            await page.close();
        }
    }

    async saveResults() {
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputFile = `${this.outputDir}simple_batch_test_${timestamp}.json`;

        const outputData = {
            testType: 'simple_batch_test',
            total: this.results.length,
            successful: this.results.filter(r => r.status === 'success').length,
            failed: this.results.filter(r => r.status === 'failed').length,
            timestamp: new Date().toISOString(),
            mode: 'headless_background',
            results: this.results
        };

        fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2));
        console.log(`💾 结果已保存: ${outputFile}`);

        // 生成简短报告
        const reportFile = `${this.outputDir}simple_batch_report_${timestamp}.txt`;
        const report = [
            `=== Le Coq Sportif Golf 简化批量测试报告 ===`,
            ``,
            `运行模式: 纯后台`,
            `处理时间: ${new Date().toISOString()}`,
            ``,
            `📊 处理结果:`,
            `- 总数: ${this.results.length}`,
            `- 成功: ${this.results.filter(r => r.status === 'success').length}`,
            `- 失败: ${this.results.filter(r => r.status === 'failed').length}`,
            `- 成功率: ${Math.round((this.results.filter(r => r.status === 'success').length / this.results.length) * 100)}%`,
            ``,
            `📋 详细结果:`,
            ...this.results.map(r => [
                `商品${r.index}: ${r.status === 'success' ? '✅' : '❌'} ${r.title ? r.title.substring(0, 40) : 'N/A'}`,
                `  编号: ${r.productCode || 'N/A'}`,
                `  价格: ${r.price || 'N/A'}`,
                `  图片: ${r.imagesCount || 0}张`
            ])
        ].join('\n');

        fs.writeFileSync(reportFile, report);
        console.log(`📄 报告已保存: ${reportFile}`);

        return { outputFile, reportFile };
    }
}

// 运行测试
if (require.main === module) {
    const tester = new SimpleBatchTester();

    tester.runSimpleTest()
        .then(() => {
            console.log('\n🎉 纯后台批量测试完成！');
            console.log('📁 检查输出目录获取结果');
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}

module.exports = SimpleBatchTester;