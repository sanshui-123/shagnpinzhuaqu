#!/usr/bin/env node

/**
 * 正确的尺码表抓取器 - 按照用户的思路实现两步式抓取
 * 步骤1: 点击"サイズガイド"按钮
 * 步骤2: 从弹窗中抓取详细尺码表数据
 */

const { chromium } = require('playwright');
const fs = require('fs');

class CorrectSizeChartProcessor {
    constructor() {
        this.results = {};
    }

    async processSizeChart(url) {
        console.log('🎯 开始正确抓取尺码表:', url);

        const browser = await chromium.launch({
            headless: false, // 🈳 显示浏览器，方便调试
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            const page = await browser.newPage();
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 60000
            });

            await page.waitForTimeout(3000);

            // 🔥 步骤1: 精确点击"サイズガイド"按钮
            console.log('🔍 步骤1: 正在查找并点击サイズガイド按钮...');

            const sizeGuideButtonClicked = await page.evaluate(() => {
                // 查找所有可能包含"サイズガイド"文本的可点击元素
                const selectors = [
                    'a:has-text("サイズガイド")',
                    'button:has-text("サイズガイド")',
                    '[onclick*="サイズガイド"]',
                    'a[href*="size"]',
                    'a[href*="guide"]',
                    '.size-guide',
                    '[class*="size"]',
                    '[id*="size"]'
                ];

                // 首先尝试文本查找
                const allElements = document.querySelectorAll('*');
                for (const element of allElements) {
                    const text = element.textContent.trim();
                    if (text === 'サイズガイド' || text.includes('サイズガイドを見る') || text.includes('サイズガイドを開く')) {
                        console.log('✅ 找到包含"サイズガイド"文本的元素:', text);
                        try {
                            element.scrollIntoView();
                            element.click();
                            console.log('✅ 成功点击サイズガイド按钮');
                            return true;
                        } catch (e) {
                            console.log('⚠️ 点击失败:', e.message);
                        }
                    }
                }

                // 备用：使用选择器
                for (const selector of selectors) {
                    try {
                        const element = document.querySelector(selector);
                        if (element && element.offsetParent !== null) {
                            element.scrollIntoView();
                            element.click();
                            console.log(`✅ 通过选择器 ${selector} 点击了按钮`);
                            return true;
                        }
                    } catch (e) {
                        console.log(`⚠️ 选择器 ${selector} 失败:`, e.message);
                    }
                }

                return false;
            });

            if (sizeGuideButtonClicked) {
                console.log('✅ 尺寸指南按钮点击成功');

                // 🈳 等待弹窗/模态框出现并加载
                await page.waitForTimeout(5000);

                // 🔥 步骤2: 精确抓取弹窗中的尺码表
                console.log('🔍 步骤2: 正在抓取弹窗中的详细尺码表...');

                // 先检查页面状态
                const pageStatus = await page.evaluate(() => {
                    const modals = document.querySelectorAll('.modal, .popup, .dialog, .overlay');
                    const allElements = document.querySelectorAll('*');
                    let sizeGuideElements = 0;

                    for (const element of allElements) {
                        const text = element.textContent.trim();
                        if (text.includes('サイズ') || text.includes('cm')) {
                            sizeGuideElements++;
                        }
                    }

                    return {
                        modalCount: modals.length,
                        sizeGuideElements: sizeGuideElements,
                        pageHTML: document.documentElement.innerHTML.substring(0, 1000)
                    };
                });

                console.log('📊 页面状态信息:');
                console.log(`  - 找到模态框数量: ${pageStatus.modalCount}`);
                console.log(`  - 包含尺寸信息的元素数量: ${pageStatus.sizeGuideElements}`);

                const sizeChartData = await page.evaluate(() => {
                    const result = {
                        foundModal: false,
                        modalContent: '',
                        sizeTableHTML: '',
                        sizeTableText: '',
                        allTables: [],
                        debugInfo: ''
                    };

                    // 查找所有表格，先保存所有表格的信息
                    const allTables = document.querySelectorAll('table');
                    result.allTables = Array.from(allTables).map((table, index) => {
                        const tableText = table.textContent.trim();
                        return {
                            index: index,
                            textLength: tableText.length,
                            preview: tableText.substring(0, 200),
                            hasCM: tableText.includes('cm'),
                            hasSizeKeywords: tableText.includes('身長') || tableText.includes('胸囲') || tableText.includes('着丈'),
                            outerHTML: table.outerHTML
                        };
                    });

                    // 查找模态框/弹窗中的尺码表
                    const modalSelectors = [
                        '.modal',
                        '.popup',
                        '.dialog',
                        '.overlay',
                        '[role="dialog"]',
                        '[class*="modal"]',
                        '[class*="popup"]',
                        '[class*="overlay"]',
                        '[style*="position: fixed"]',
                        '[style*="position: absolute"]',
                        '[class*="size"]',
                        '[id*="size"]'
                    ];

                    // 在模态框中查找尺码表
                    for (const modalSelector of modalSelectors) {
                        const modals = document.querySelectorAll(modalSelector);
                        console.log(`检查模态框选择器 ${modalSelector}, 找到 ${modals.length} 个元素`);

                        for (const modal of modals) {
                            const isVisible = modal.offsetParent !== null &&
                                            modal.style.display !== 'none' &&
                                            modal.style.visibility !== 'hidden';

                            if (isVisible) {
                                result.foundModal = true;
                                result.modalContent = modal.innerHTML;

                                // 在模态框内查找表格
                                const tables = modal.querySelectorAll('table');
                                console.log(`在模态框中找到 ${tables.length} 个表格`);

                                for (const table of tables) {
                                    const tableText = table.textContent.trim();
                                    // 检查是否包含尺码表特征 - 更宽松的条件
                                    const hasSizeKeywords = (
                                        tableText.includes('身長') ||
                                        tableText.includes('胸囲') ||
                                        tableText.includes('着丈') ||
                                        tableText.includes('肩幅') ||
                                        tableText.includes('袖丈') ||
                                        tableText.includes('ウエスト') ||
                                        tableText.includes('ヒップ') ||
                                        tableText.includes('サイズ')
                                    );

                                    const hasSizeNumbers = (
                                        /\d+[.]\d+cm/.test(tableText) ||  // 小数+cm
                                        /\d+cm/.test(tableText) ||         // 整数+cm
                                        /S|M|L|LL|3L/.test(tableText) ||   // 尺寸标识
                                        tableText.length > 400            // 长度阈值
                                    );

                                    console.log(`检查表格: 长度=${tableText.length}, 尺寸关键词=${hasSizeKeywords}, 尺寸数字=${hasSizeNumbers}`);

                                    if (hasSizeKeywords || hasSizeNumbers) {
                                        result.sizeTableHTML = table.outerHTML;
                                        result.sizeTableText = tableText;
                                        console.log('✅ 在模态框中找到尺码表，长度:', tableText.length);
                                        return result;
                                    }
                                }
                            }
                        }
                    }

                    // 备用：查找所有表格（不只是模态框内）
                    console.log(`备用检查：查找所有表格，共 ${allTables.length} 个`);
                    for (let i = 0; i < allTables.length; i++) {
                        const table = allTables[i];
                        const tableText = table.textContent.trim();

                        if (tableText.includes('cm') && tableText.length > 200) {
                            result.sizeTableHTML = table.outerHTML;
                            result.sizeTableText = tableText;
                            result.debugInfo = `找到表格索引 ${i}，包含cm且长度${tableText.length}`;
                            console.log('✅ 在页面中找到详细尺码表:', result.debugInfo);
                            return result;
                        }
                    }

                    result.debugInfo = `检查了 ${allTables.length} 个表格，但未找到合适的尺码表`;
                    return result;
                });

                if (sizeChartData.sizeTableText) {
                    console.log('✅ 成功抓取详细尺码表数据');
                    console.log('📏 尺码表内容预览（前150字符）:');
                    console.log(`  ${sizeChartData.sizeTableText.substring(0, 150)}...`);

                    this.results = {
                        抓取成功: true,
                        找到模态框: sizeChartData.foundModal,
                        尺码表HTML: sizeChartData.sizeTableHTML,
                        尺码表文本: sizeChartData.sizeTableText,
                        原始模态框内容: sizeChartData.modalContent,
                        所有表格信息: sizeChartData.allTables,
                        调试信息: sizeChartData.debugInfo
                    };
                } else {
                    console.log('⚠️ 未找到详细尺码表，显示调试信息...');
                    console.log('🔍 调试信息:');
                    console.log(`  - 找到模态框: ${sizeChartData.foundModal}`);
                    console.log(`  - 模态框内容长度: ${sizeChartData.modalContent.length}`);
                    console.log(`  - 调试信息: ${sizeChartData.debugInfo}`);
                    console.log(`  - 找到表格数量: ${sizeChartData.allTables.length}`);

                    // 显示找到的所有表格信息
                    sizeChartData.allTables.forEach((tableInfo, index) => {
                        console.log(`    表格${index}: 长度=${tableInfo.textLength}, 包含cm=${tableInfo.hasCM}, 包含尺寸关键词=${tableInfo.hasSizeKeywords}`);
                        if (tableInfo.hasCM || tableInfo.hasSizeKeywords) {
                            console.log(`      预览: ${tableInfo.preview.substring(0, 100)}...`);
                        }
                    });

                    // 尝试更长的等待时间后重新抓取
                    console.log('⏰ 等待10秒后重新尝试...');
                    await page.waitForTimeout(10000);

                    const retryData = await page.evaluate(() => {
                        const tables = document.querySelectorAll('table');
                        for (const table of tables) {
                            const tableText = table.textContent.trim();
                            if (tableText.includes('cm') && tableText.length > 200) {
                                return {
                                    sizeTableHTML: table.outerHTML,
                                    sizeTableText: tableText
                                };
                            }
                        }
                        return null;
                    });

                    if (retryData) {
                        console.log('✅ 延长等待后成功抓取尺码表');
                        this.results = {
                            抓取成功: true,
                            找到模态框: false,
                            尺码表HTML: retryData.sizeTableHTML,
                            尺码表文本: retryData.sizeTableText,
                            原始模态框内容: '',
                            所有表格信息: sizeChartData.allTables,
                            调试信息: '延长等待后找到尺码表'
                        };
                    } else {
                        console.log('❌ 最终未能抓取详细尺码表');
                        this.results = {
                            抓取成功: false,
                            错误信息: '未找到详细的尺码表数据',
                            所有表格信息: sizeChartData.allTables,
                            调试信息: sizeChartData.debugInfo,
                            模态框信息: {
                                找到模态框: sizeChartData.foundModal,
                                模态框内容长度: sizeChartData.modalContent.length
                            }
                        };
                    }
                }
            } else {
                console.log('❌ 未找到或未能点击尺寸指南按钮');
                this.results = {
                    抓取成功: false,
                    错误信息: '未找到尺寸指南按钮'
                };
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
    const processor = new CorrectSizeChartProcessor();

    // 使用测试URL
    const testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EW011538/';

    console.log('🚀 开始正确的尺码表抓取测试...');
    console.log('🌐 运行模式：显示浏览器模式（便于调试）');

    const result = await processor.processSizeChart(testUrl);

    console.log('\n📊 抓取结果汇总:');
    console.log(`✅ 抓取成功: ${result.抓取成功}`);

    if (result.抓取成功) {
        console.log(`🎯 找到模态框: ${result.找到模态框}`);
        console.log(`📏 尺码表文本长度: ${result.尺码表文本.length}字符`);
        console.log(`📄 HTML内容长度: ${result.尺码表HTML.length}字符`);

        // 保存结果
        const outputData = {
            url: testUrl,
            timestamp: new Date().toISOString(),
            success: result.抓取成功,
            data: result
        };

        const outputFile = `/Users/sanshui/Desktop/CallawayJP/correct_size_chart_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');

        console.log(`💾 结果已保存: ${outputFile}`);
        console.log('\n📋 尺码表完整内容:');
        console.log(result.尺码表文本);
    } else {
        console.log(`❌ 错误信息: ${result.错误信息}`);
    }

    console.log('\n✅ 正确的尺码表抓取测试完成！');
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = CorrectSizeChartProcessor;