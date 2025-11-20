#!/usr/bin/env node

/**
 * 调试脚本：详细分析可见按钮的结构
 */

const { chromium } = require('playwright');

async function debugButtons() {
    const url = 'https://mix.tokyo/products/0536170151';

    console.log(`🔍 分析页面: ${url}\n`);

    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // 关闭可能的模态框
    await page.evaluate(() => {
        const modals = document.querySelectorAll('.modal, .c_modal, [role="dialog"]');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });

        const closeButtons = document.querySelectorAll('.modal-close, .c_modal__close, [aria-label="close"], [aria-label="閉じる"]');
        closeButtons.forEach(btn => btn.click());
    });

    await page.waitForTimeout(1000);

    // 分析按钮结构
    const buttonInfo = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button.product__thumbnail-item'));

        return buttons.map((btn, i) => {
            const visible = btn.offsetParent !== null;  // 更准确的可见性检查
            const textContent = btn.textContent.trim();
            const innerHTML = btn.innerHTML.substring(0, 200);  // 前200个字符
            const className = btn.className;
            const ariaLabel = btn.getAttribute('aria-label');
            const dataValue = btn.getAttribute('data-value') || btn.getAttribute('data-color');

            // 检查子元素
            const childElements = [];
            for (const child of btn.children) {
                childElements.push({
                    tag: child.tagName,
                    text: child.textContent.trim().substring(0, 50),
                    class: child.className
                });
            }

            return {
                index: i + 1,
                visible,
                textContent,
                ariaLabel,
                dataValue,
                className,
                innerHTML: innerHTML.replace(/\n/g, ' ').replace(/\s+/g, ' '),
                childCount: btn.children.length,
                childElements: childElements.slice(0, 3)
            };
        });
    });

    console.log('='.repeat(80));
    console.log('📋 按钮详细信息\n');

    buttonInfo.forEach(info => {
        console.log(`按钮 ${info.index}:`);
        console.log(`  可见: ${info.visible ? '✅' : '❌'}`);
        console.log(`  文本: "${info.textContent || '(空)'}"`);
        console.log(`  aria-label: ${info.ariaLabel || '无'}`);
        console.log(`  data属性: ${info.dataValue || '无'}`);
        console.log(`  class: ${info.className}`);
        console.log(`  子元素数量: ${info.childCount}`);
        if (info.childElements.length > 0) {
            console.log(`  子元素:`);
            info.childElements.forEach(child => {
                console.log(`    - <${child.tag}> class="${child.class}" text="${child.text}"`);
            });
        }
        console.log(`  HTML: ${info.innerHTML}`);
        console.log('');
    });

    // 查找库存表
    console.log('='.repeat(80));
    console.log('📦 库存表信息\n');

    const inventoryInfo = await page.evaluate(() => {
        const cells = Array.from(document.querySelectorAll('.c_size-availability__cell'));
        return {
            cellCount: cells.length,
            cells: cells.slice(0, 10).map(cell => ({
                text: cell.textContent.trim(),
                className: cell.className,
                visible: cell.offsetParent !== null
            }))
        };
    });

    console.log(`找到 ${inventoryInfo.cellCount} 个库存单元格`);
    if (inventoryInfo.cells.length > 0) {
        inventoryInfo.cells.forEach((cell, i) => {
            console.log(`  单元格 ${i + 1}: "${cell.text}" | class="${cell.className}" | 可见=${cell.visible}`);
        });
    }

    console.log('\n' + '='.repeat(80));
    console.log('✅ 分析完成！');
    console.log('='.repeat(80));

    await page.waitForTimeout(5000);
    await browser.close();
}

debugButtons().catch(console.error);
