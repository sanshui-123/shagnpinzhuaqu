#!/usr/bin/env node

/**
 * 检查列表页是否包含品牌货号（ブランド商品番号）
 */

const { chromium } = require('playwright');

async function checkBrandCode() {
    console.log('🔍 检查列表页是否包含品牌货号...');

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
        const url = 'https://store.descente.co.jp/brand/le%2520coq%2520sportif%2520golf/ds_apparel_m?commercialType=0%7C2%7C3&groupByModel=1&currentPage=1&alignmentSequence=recommend_commodity_rank+asc';

        console.log(`📄 访问页面: ${url}`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(5000);

        // 检查列表项结构
        const itemsData = await page.evaluate(() => {
            const items = document.querySelectorAll('.catalogList_item');
            console.log(`找到 ${items.length} 个商品项`);

            if (items.length === 0) return [];

            // 只检查前3个商品
            return Array.from(items).slice(0, 3).map((item, index) => {
                // 提取所有可能的信息
                const data = {
                    index: index + 1,
                    html: item.innerHTML.substring(0, 2000), // 前2000字符
                    allText: item.textContent.trim(),
                    attributes: {}
                };

                // 提取所有data-*属性
                for (const attr of item.attributes) {
                    if (attr.name.startsWith('data-')) {
                        data.attributes[attr.name] = attr.value;
                    }
                }

                // 查找所有可能包含商品编号的元素
                const potentialCodeElements = item.querySelectorAll('[class*="code"], [class*="number"], [class*="id"], [data-code], [data-product-code], [data-item-code]');
                if (potentialCodeElements.length > 0) {
                    data.potentialCodes = Array.from(potentialCodeElements).map(el => ({
                        tag: el.tagName,
                        class: el.className,
                        text: el.textContent.trim(),
                        html: el.outerHTML.substring(0, 300)
                    }));
                }

                // 提取URL
                const link = item.querySelector('a[href*="/commodity/"]');
                if (link) {
                    data.url = link.href;
                }

                return data;
            });
        });

        console.log('\n=== 列表页结构分析 ===');
        console.log(JSON.stringify(itemsData, null, 2));

        // 现在访问第一个详情页，看看品牌货号在哪里
        if (itemsData.length > 0 && itemsData[0].url) {
            console.log('\n🔍 访问详情页检查品牌货号位置...');
            await page.goto(itemsData[0].url, { waitUntil: 'domcontentloaded', timeout: 30000 });
            await page.waitForTimeout(3000);

            const detailData = await page.evaluate(() => {
                const data = {
                    title: document.title,
                    brandCode: null,
                    brandCodeElement: null
                };

                // 查找「ブランド商品番号」
                const allText = document.body.textContent;
                if (allText.includes('ブランド商品番号')) {
                    // 尝试找到包含这个文本的元素
                    const xpath = "//text()[contains(., 'ブランド商品番号')]/..";
                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    if (result.singleNodeValue) {
                        const parent = result.singleNodeValue;
                        data.brandCodeElement = {
                            tag: parent.tagName,
                            class: parent.className,
                            text: parent.textContent.trim(),
                            html: parent.outerHTML.substring(0, 500)
                        };

                        // 尝试提取实际的商品编号
                        const match = parent.textContent.match(/[A-Z]{2}\d[A-Z\d]+/);
                        if (match) {
                            data.brandCode = match[0];
                        }
                    }
                }

                return data;
            });

            console.log('\n=== 详情页品牌货号信息 ===');
            console.log(JSON.stringify(detailData, null, 2));
        }

    } catch (error) {
        console.error('❌ 检查失败:', error);
    } finally {
        await browser.close();
    }
}

checkBrandCode();
