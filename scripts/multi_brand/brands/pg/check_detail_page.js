#!/usr/bin/env node

/**
 * 检查详情页的品牌货号完整结构
 */

const { chromium } = require('playwright');

async function checkDetailPage() {
    console.log('🔍 检查详情页品牌货号结构...');

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
        // 访问一个样例详情页
        const url = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM011353/';

        console.log(`📄 访问详情页: ${url}`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(3000);

        const detailData = await page.evaluate(() => {
            const data = {
                title: document.title,
                brandCode: null,
                brandCodeInfo: {}
            };

            // 方法1: 查找包含「ブランド商品番号」的 th，然后找对应的 td
            const tables = document.querySelectorAll('table');
            for (const table of tables) {
                const rows = table.querySelectorAll('tr');
                for (const row of rows) {
                    const th = row.querySelector('th');
                    const td = row.querySelector('td');
                    if (th && th.textContent.includes('ブランド商品番号')) {
                        data.brandCodeInfo.tableMethod = {
                            th: th.textContent.trim(),
                            td: td ? td.textContent.trim() : null,
                            tdHTML: td ? td.innerHTML : null
                        };
                        if (td) {
                            data.brandCode = td.textContent.trim();
                        }
                    }
                }
            }

            // 方法2: 使用 XPath 查找
            const xpath = "//th[contains(text(), 'ブランド商品番号')]/following-sibling::td";
            const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            if (result.singleNodeValue) {
                data.brandCodeInfo.xpathMethod = {
                    text: result.singleNodeValue.textContent.trim(),
                    html: result.singleNodeValue.innerHTML
                };
                if (!data.brandCode) {
                    data.brandCode = result.singleNodeValue.textContent.trim();
                }
            }

            // 方法3: 查找所有包含商品编号格式的文本（大写字母开头的编号）
            const allText = document.body.innerText;
            const codePatterns = allText.match(/\b[A-Z]{2}\d[A-Z\d]{5,10}\b/g);
            if (codePatterns) {
                data.brandCodeInfo.potentialCodes = codePatterns;
            }

            // 提取 URL 中的编号作为对比
            data.urlCode = window.location.pathname.match(/\/([A-Z]+\d+[A-Z]*\d*)\//)?.[1];

            return data;
        });

        console.log('\n=== 详情页品牌货号完整信息 ===');
        console.log(JSON.stringify(detailData, null, 2));

        // 再访问第二个商品做对比
        console.log('\n🔍 访问第二个商品详情页做对比...');
        const url2 = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM009639/';
        await page.goto(url2, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(3000);

        const detailData2 = await page.evaluate(() => {
            const data = {
                brandCode: null,
                urlCode: window.location.pathname.match(/\/([A-Z]+\d+[A-Z]*\d*)\//)?.[1]
            };

            const xpath = "//th[contains(text(), 'ブランド商品番号')]/following-sibling::td";
            const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            if (result.singleNodeValue) {
                data.brandCode = result.singleNodeValue.textContent.trim();
            }

            return data;
        });

        console.log('\n=== 第二个商品对比 ===');
        console.log(JSON.stringify(detailData2, null, 2));

    } catch (error) {
        console.error('❌ 检查失败:', error);
    } finally {
        await browser.close();
    }
}

checkDetailPage();
