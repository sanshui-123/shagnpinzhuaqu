const puppeteer = require('puppeteer');

async function testColorButtons() {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.goto('https://www.callawaygolf.jp/womens/tops/outer/C25215200_.html?pid=C25215200_1031_S', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });

  await page.waitForTimeout(5000);

  // 检查所有可能的颜色元素
  const colorInfo = await page.evaluate(() => {
    const info = {
      radioButtons: [],
      colorElements: [],
      allButtons: []
    };

    // 1. 查找所有 radio 按钮
    const radios = document.querySelectorAll('[role="radio"]');
    radios.forEach((radio, index) => {
      const ariaLabel = radio.getAttribute('aria-label') || '';
      info.radioButtons.push({
        index,
        ariaLabel,
        ariaChecked: radio.getAttribute('aria-checked'),
        id: radio.id,
        visible: radio.offsetParent !== null
      });
    });

    // 2. 查找包含颜色关键词的元素
    const selectors = [
      '[role="radio"][aria-label*="カラー"]',
      '[data-attr="color"] button',
      '[data-attr="color"] [role="radio"]',
      '.variation-attribute-value[data-attr="color"]',
      'button[title*="WHITE"]',
      'button[title*="BLACK"]',
      'button[title*="NAVY"]',
      '.selectable[data-attr-value]'
    ];

    selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          info.colorElements.push({
            selector,
            text: el.textContent?.trim(),
            ariaLabel: el.getAttribute('aria-label'),
            title: el.getAttribute('title'),
            dataAttrValue: el.getAttribute('data-attr-value'),
            tagName: el.tagName
          });
        });
      } catch (e) {}
    });

    // 3. 查找所有按钮
    const allButtons = document.querySelectorAll('button');
    allButtons.forEach(btn => {
      const text = btn.textContent?.trim() || '';
      if (text.includes('WHITE') || text.includes('BLACK') || text.includes('NAVY') ||
          text.includes('ホワイト') || text.includes('ブラック') || text.includes('ネイビー')) {
        info.allButtons.push({
          text,
          title: btn.getAttribute('title'),
          className: btn.className
        });
      }
    });

    return info;
  });

  console.log('\n=== 颜色元素分析 ===\n');
  
  console.log('1. Radio 按钮:');
  colorInfo.radioButtons.forEach(radio => {
    if (radio.ariaLabel.includes('カラー') || radio.ariaLabel.includes('COLOR')) {
      console.log(`  - ${radio.ariaLabel} (checked: ${radio.ariaChecked})`);
    }
  });

  console.log('\n2. 颜色选择器匹配:');
  colorInfo.colorElements.forEach(el => {
    console.log(`  - [${el.tagName}] ${el.text || el.ariaLabel || el.title || el.dataAttrValue}`);
  });

  console.log('\n3. 包含颜色关键词的按钮:');
  colorInfo.allButtons.forEach(btn => {
    console.log(`  - ${btn.text}`);
  });

  // 尝试点击不同的颜色
  console.log('\n=== 尝试点击颜色 ===\n');

  // 获取所有颜色 radio
  const colorRadios = await page.$$('[role="radio"][aria-label*="カラー"]');
  console.log(`找到 ${colorRadios.length} 个颜色选项`);

  for (let i = 0; i < colorRadios.length; i++) {
    const ariaLabel = await colorRadios[i].evaluate(el => el.getAttribute('aria-label'));
    console.log(`\n点击第 ${i + 1} 个颜色: ${ariaLabel}`);
    
    await colorRadios[i].click();
    await page.waitForTimeout(2000);
    
    // 检查图片是否改变
    const mainImage = await page.$eval('.slick-slide.slick-active img', img => img.src).catch(() => 'No image');
    console.log(`  主图: ${mainImage.substring(0, 50)}...`);
  }

  console.log('\n测试完成，请手动检查浏览器中的颜色选项');
  
  // 保持浏览器打开30秒
  await page.waitForTimeout(30000);
  await browser.close();
}

testColorButtons().catch(console.error);