#!/usr/bin/env node

/**
 * 高级尺码表抓取器 - 尝试多种方法获取详细尺码信息
 * 1. 检查是否有外部链接到尺码表页面
 * 2. 检查是否需要等待更长时间加载
 * 3. 检查是否需要多次点击
 * 4. 检查是否有隐藏的尺码表内容
 */

const { chromium } = require('playwright');
const fs = require('fs');

class AdvancedSizeChartProcessor {
    constructor() {
        this.results = {};
    }

    async processAdvancedSizeChart(url) {
        console.log('🎯 开始高级尺码表抓取:', url);

        const browser = await chromium.launch({
            headless: false, // 🈳 显示浏览器，方便调试
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            const page = await browser.newPage();

            // 🈳 设置更长的超时时间和视窗
            await page.setDefaultTimeout(30000);
            await page.setViewportSize({ width: 1920, height: 1080 });

            await page.goto(url, {
                waitUntil: 'domcontentloaded', // 等待DOM加载完成
                timeout: 45000
            });

            await page.waitForTimeout(3000);

            // 🔍 方法1: 检查是否有尺码表的外部链接
            console.log('🔍 方法1: 检查尺码表外部链接...');
            const sizeGuideLinks = await page.evaluate(() => {
                const links = document.querySelectorAll('a[href], button[onclick]');
                const result = [];

                for (const link of links) {
                    const text = link.textContent.trim();
                    const href = link.getAttribute('href') || link.getAttribute('onclick') || '';

                    if (text.includes('サイズガイド') ||
                        text.includes('サイズ') ||
                        href.includes('size') ||
                        href.includes('guide') ||
                        href.includes('chart')) {
                        result.push({
                            text: text,
                            href: href,
                            element: link.tagName,
                            isExternal: href.startsWith('http') && !href.includes('descente.co.jp')
                        });
                    }
                }
                return result;
            });

            console.log(`找到 ${sizeGuideLinks.length} 个可能的尺码表链接:`);
            sizeGuideLinks.forEach((link, index) => {
                console.log(`  ${index + 1}. [${link.element}] ${link.text} -> ${link.href.substring(0, 50)}... (外部: ${link.isExternal})`);
            });

            // 🔍 方法2: 尝试多种点击策略
            console.log('🔍 方法2: 尝试多种点击策略...');

            let sizeChartFound = false;
            let clickMethod = '';

            // 策略A: 直接点击找到的链接
            for (let i = 0; i < sizeGuideLinks.length; i++) {
                const link = sizeGuideLinks[i];
                console.log(`尝试点击链接 ${i + 1}: ${link.text}`);

                try {
                    if (link.isExternal) {
                        console.log('跳过外部链接，可能需要新页面处理');
                        continue;
                    }

                    // 重新加载页面以确保干净状态
                    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
                    await page.waitForTimeout(3000);

                    const clicked = await page.evaluate((targetText) => {
                        const allElements = document.querySelectorAll('*');
                        for (const element of allElements) {
                            if (element.textContent.trim() === targetText) {
                                try {
                                    element.scrollIntoView({ block: 'center' });
                                    setTimeout(() => element.click(), 500);
                                    return true;
                                } catch (e) {
                                    console.log('点击失败:', e.message);
                                }
                            }
                        }
                        return false;
                    }, link.text);

                    if (clicked) {
                        console.log('✅ 成功点击，等待内容加载...');
                        await page.waitForTimeout(8000);

                        // 检查页面变化
                        const hasModal = await page.evaluate(() => {
                            const modals = document.querySelectorAll('.modal, .popup, .dialog, .overlay, [role="dialog"], [style*="position: fixed"]');
                            const tables = document.querySelectorAll('table');
                            const hasSizeContent = Array.from(tables).some(table =>
                                table.textContent.includes('cm') ||
                                table.textContent.includes('身長') ||
                                table.textContent.includes('胸囲') ||
                                table.textContent.includes('着丈')
                            );

                            return {
                                modalCount: modals.length,
                                tableCount: tables.length,
                                hasSizeContent: hasSizeContent,
                                pageContent: document.body.innerHTML.substring(0, 5000)
                            };
                        });

                        console.log(`检查结果: 模态框=${hasModal.modalCount}, 表格=${hasModal.tableCount}, 包含尺码=${hasModal.hasSizeContent}`);

                        if (hasModal.hasSizeContent || hasModal.modalCount > 0) {
                            sizeChartFound = true;
                            clickMethod = `点击链接: ${link.text}`;
                            break;
                        }
                    }
                } catch (error) {
                    console.log(`点击链接失败: ${error.message}`);
                }
            }

            // 🔍 方法3: 如果点击失败，尝试检查所有可能的尺码表内容
            if (!sizeChartFound) {
                console.log('🔍 方法3: 深度搜索所有尺码表内容...');

                // 重新加载页面
                await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
                await page.waitForTimeout(5000);

                const deepSearch = await page.evaluate(() => {
                    const result = {
                        found: false,
                        tables: [],
                        divs: [],
                        sections: []
                    };

                    // 搜索所有表格
                    const tables = document.querySelectorAll('table');
                    tables.forEach((table, index) => {
                        const text = table.textContent.trim();
                        const hasSizeInfo = (
                            text.includes('身長') ||
                            text.includes('胸囲') ||
                            text.includes('着丈') ||
                            text.includes('肩幅') ||
                            text.includes('袖丈') ||
                            text.includes('ウエスト') ||
                            text.includes('ヒップ') ||
                            text.includes('cm') ||
                            /\d+\.?\d*\s*cm/i.test(text) ||
                            /S|M|L|LL|3L/.test(text)
                        );

                        if (hasSizeInfo) {
                            result.tables.push({
                                index: index,
                                textLength: text.length,
                                html: table.outerHTML,
                                text: text.substring(0, 500),
                                fullText: text
                            });
                            result.found = true;
                        }
                    });

                    // 搜索可能包含尺码信息的div
                    const potentialDivs = document.querySelectorAll('div[class*="size"], div[id*="size"], .size-guide, .size-chart, .spec, .detail');
                    potentialDivs.forEach((div, index) => {
                        const text = div.textContent.trim();
                        if (text.length > 100 && (text.includes('cm') || text.includes('サイズ'))) {
                            result.divs.push({
                                index: index,
                                className: div.className,
                                textLength: text.length,
                                text: text.substring(0, 300)
                            });
                        }
                    });

                    return result;
                });

                console.log(`深度搜索结果:`);
                console.log(`  - 找到相关表格: ${deepSearch.tables.length} 个`);
                console.log(`  - 找到相关div: ${deepSearch.divs.length} 个`);

                if (deepSearch.found) {
                    console.log('✅ 找到尺码表内容!');
                    this.results = {
                        抓取成功: true,
                        找到方法: '深度搜索',
                        尺码表HTML: deepSearch.tables.length > 0 ? deepSearch.tables[0].html : '',
                        尺码表文本: deepSearch.tables.length > 0 ? deepSearch.tables[0].fullText : '',
                        找到的表格: deepSearch.tables,
                        找到的div: deepSearch.divs,
                        点击方法: clickMethod
                    };
                } else {
                    // 最后尝试：检查隐藏内容
                    console.log('🔍 方法4: 检查隐藏内容和延迟加载...');

                    await page.waitForTimeout(15000); // 等待更长时间

                    const finalCheck = await page.evaluate(() => {
                        // 检查是否有新的元素出现
                        const newTables = document.querySelectorAll('table');
                        const hiddenElements = document.querySelectorAll('[style*="display: none"], [hidden]');

                        // 尝试显示隐藏元素
                        Array.from(hiddenElements).forEach(el => {
                            if (el.textContent.includes('サイズ') || el.textContent.includes('cm')) {
                                el.style.display = 'block';
                                el.removeAttribute('hidden');
                            }
                        });

                        // 重新检查表格
                        const allTables = document.querySelectorAll('table');
                        const sizeTables = Array.from(allTables).filter(table => {
                            const text = table.textContent.trim();
                            return text.includes('サイズ') || text.includes('cm') || text.length > 800;
                        });

                        return {
                            totalTables: allTables.length,
                            sizeTables: sizeTables.length,
                            hiddenElements: hiddenElements.length,
                            sizeTableData: sizeTables.map((table, index) => ({
                                index: index,
                                textLength: table.textContent.trim().length,
                                html: table.outerHTML,
                                text: table.textContent.trim().substring(0, 300)
                            }))
                        };
                    });

                    console.log(`最终检查结果: 总表格=${finalCheck.totalTables}, 尺码表格=${finalCheck.sizeTables}, 隐藏元素=${finalCheck.hiddenElements}`);

                    if (finalCheck.sizeTables > 0) {
                        console.log('✅ 在最终检查中找到尺码表!');
                        const bestTable = finalCheck.sizeTableData[0];
                        this.results = {
                            抓取成功: true,
                            找到方法: '最终检查',
                            尺码表HTML: bestTable.html,
                            尺码表文本: bestTable.text,
                            点击方法: '等待后自动出现'
                        };
                    } else {
                        this.results = {
                            抓取成功: false,
                            错误信息: '所有方法都未找到详细尺码表',
                            尝试方法: [
                                '外部链接检查',
                                '多种点击策略',
                                '深度搜索',
                                '隐藏内容检查'
                            ],
                            找到的链接: sizeGuideLinks,
                            深度搜索结果: deepSearch,
                            最终检查结果: finalCheck
                        };
                    }
                }
            }

        } catch (error) {
            console.log('❌ 处理过程出错:', error.message);
            this.results = {
                抓取成功: false,
                错误信息: error.message
            };
        } finally {
            await browser.close();
        }

        return this.results;
    }
}

// 主函数
async function main() {
    const processor = new AdvancedSizeChartProcessor();

    // 使用测试URL
    const testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EW011538/';

    console.log('🚀 开始高级尺码表抓取测试...');
    console.log('🌐 运行模式：完整调试模式');

    const result = await processor.processAdvancedSizeChart(testUrl);

    console.log('\n📊 最终抓取结果:');
    console.log(`✅ 抓取成功: ${result.抓取成功}`);

    if (result.抓取成功) {
        console.log(`🎯 找到方法: ${result.找到方法}`);
        console.log(`🖱️ 点击方法: ${result.点击方法 || '无需点击'}`);
        console.log(`📏 尺码表文本长度: ${result.尺码表文本.length}字符`);

        // 显示尺码表内容预览
        console.log('\n📋 尺码表内容预览:');
        const preview = result.尺码表文本.substring(0, 800);
        console.log(preview + (result.尺码表文本.length > 800 ? '...' : ''));

        // 保存结果
        const outputData = {
            url: testUrl,
            timestamp: new Date().toISOString(),
            success: result.抓取成功,
            method: result.找到方法,
            clickMethod: result.点击方法,
            data: result
        };

        const outputFile = `/Users/sanshui/Desktop/CallawayJP/advanced_size_chart_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');

        console.log(`\n💾 完整结果已保存: ${outputFile}`);
    } else {
        console.log(`❌ 失败原因: ${result.错误信息}`);
        if (result.尝试方法) {
            console.log('🔧 尝试的方法:', result.尝试方法.join(', '));
        }
        if (result.找到的链接 && result.找到的链接.length > 0) {
            console.log(`🔗 找到的链接数量: ${result.找到的链接.length}`);
        }
    }

    console.log('\n✅ 高级尺码表抓取测试完成！');
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = AdvancedSizeChartProcessor;