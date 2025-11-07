const { chromium } = require('playwright');

async function testAccess() {
    let browser;
    try {
        console.log('启动浏览器...');
        browser = await chromium.launch({
            headless: false
        });
        
        const page = await browser.newPage();
        
        // 测试访问主页
        console.log('测试访问主页...');
        try {
            await page.goto('https://www.callawaygolf.jp/', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            console.log('✓ 主页访问成功');
        } catch (error) {
            console.log('✗ 主页访问失败:', error.message);
        }
        
        // 测试访问目标分类页
        console.log('\n测试访问大尺码上装分类页...');
        try {
            // 先尝试不带参数的URL
            await page.goto('https://www.callawaygolf.jp/apparel/mens/tops/', {
                waitUntil: 'domcontentloaded', 
                timeout: 30000
            });
            console.log('✓ 基础URL访问成功');
            
            // 等待页面稳定
            await page.waitForTimeout(3000);
            
            // 尝试访问带size参数的URL
            await page.goto('https://www.callawaygolf.jp/apparel/mens/tops/?size=149', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            console.log('✓ 带参数URL访问成功');
            
            // 检查商品数量
            await page.waitForTimeout(5000);
            const countText = await page.textContent('.plp-header-bar__result').catch(() => null);
            if (countText) {
                console.log('商品数量:', countText);
            }
            
        } catch (error) {
            console.log('✗ 分类页访问失败:', error.message);
        }
        
        console.log('\n测试完成，浏览器将在10秒后关闭...');
        await page.waitForTimeout(10000);
        
    } catch (error) {
        console.error('测试出错:', error);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

testAccess();