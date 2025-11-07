#!/usr/bin/env node
/**
 * 测试脚本：分析CallawayJP页面结构
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;

async function analyzePageStructure(url) {
  const browser = await chromium.launch({ headless: true });
  
  try {
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      locale: 'ja-JP',
      timezone: 'Asia/Tokyo',
      viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    console.log('访问页面:', url);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    
    // 等待页面完全加载
    await page.waitForTimeout(5000);
    
    // 分析页面结构
    const pageAnalysis = await page.evaluate(() => {
      const results = {
        title: document.querySelector('h1')?.innerText || '',
        scripts: [],
        colorButtons: [],
        sizeSelects: [],
        images: [],
        productInfo: {}
      };
      
      // 查找所有script标签
      document.querySelectorAll('script').forEach((script, index) => {
        const content = script.textContent || '';
        if (content.length > 1000 && content.includes('product')) {
          results.scripts.push({
            index,
            length: content.length,
            hasProductDetail: content.includes('productDetail'),
            hasVariationAttributes: content.includes('variationAttributes'),
            preview: content.substring(0, 200)
          });
        }
      });
      
      // 查找颜色按钮
      const colorSelectors = [
        'button[aria-label*="カラー"]',
        'button[title*="1031"]',
        'button[title*="1030"]',
        '[role="radio"][aria-label*="カラー"]',
        '.color-button',
        '[data-color]'
      ];
      
      colorSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results.colorButtons.push({
            selector,
            count: elements.length,
            samples: Array.from(elements).slice(0, 3).map(el => ({
              text: el.textContent?.trim(),
              ariaLabel: el.getAttribute('aria-label'),
              title: el.getAttribute('title'),
              dataAttrs: {
                color: el.getAttribute('data-color'),
                variant: el.getAttribute('data-variant'),
                pid: el.getAttribute('data-pid')
              }
            }))
          });
        }
      });
      
      // 查找尺码选择器
      const sizeSelectors = [
        'select[name*="size"]',
        'button[aria-label*="サイズ"]',
        '[role="radio"][aria-label*="サイズ"]',
        '.size-select',
        '[data-size]'
      ];
      
      sizeSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results.sizeSelects.push({
            selector,
            count: elements.length,
            samples: Array.from(elements).slice(0, 3).map(el => ({
              text: el.textContent?.trim(),
              value: el.value,
              options: el.tagName === 'SELECT' ? 
                Array.from(el.options).map(opt => opt.text) : null
            }))
          });
        }
      });
      
      // 查找商品图片
      const imageSelectors = [
        'img[alt*="商品画像"]',
        '.product-image img',
        '.gallery img',
        'img[src*="1280_"]',
        'img[src*="product"]'
      ];
      
      imageSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results.images.push({
            selector,
            count: elements.length,
            samples: Array.from(elements).slice(0, 3).map(el => ({
              src: el.src,
              alt: el.alt,
              srcset: el.srcset
            }))
          });
        }
      });
      
      return results;
    });
    
    // 保存分析结果
    await fs.writeFile(
      'page_analysis.json', 
      JSON.stringify(pageAnalysis, null, 2)
    );
    
    console.log('页面分析完成，已保存到 page_analysis.json');
    console.log('\n分析摘要:');
    console.log('- 标题:', pageAnalysis.title);
    console.log('- 找到的脚本:', pageAnalysis.scripts.length);
    console.log('- 颜色按钮组:', pageAnalysis.colorButtons.length);
    console.log('- 尺码选择器组:', pageAnalysis.sizeSelects.length);
    console.log('- 图片组:', pageAnalysis.images.length);
    
    // 截图保存
    await page.screenshot({ path: 'page_screenshot.png', fullPage: true });
    
  } catch (error) {
    console.error('错误:', error);
  } finally {
    await browser.close();
  }
}

// 执行分析
const url = process.argv[2] || 'https://www.callawaygolf.jp/womens/tops/outer/C25215200_.html?pid=C25215200_1031_S';
analyzePageStructure(url);