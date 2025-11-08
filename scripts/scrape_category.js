const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const argv = yargs(hideBin(process.argv))
  .option('url', {
    alias: 'u',
    type: 'string',
    description: '完整的分类页面URL',
    demandOption: true
  })
  .option('category', {
    alias: 'c',
    type: 'string',
    description: '英文分类名称',
    demandOption: true
  })
  .option('overwrite-latest', {
    alias: 'ol',
    type: 'boolean',
    default: false,
    description: '将抓取结果写入固定最新文件(raw_links_<category>_latest.json)，避免生成新文件'
  })
  .option('skip-if-unchanged', {
    alias: 'su',
    type: 'boolean',
    default: false,
    description: '若检测到页面数量与最近一次抓取一致，则跳过本次抓取'
  })
  .argv;

const overwriteLatest = argv.overwriteLatest || false;
const skipIfUnchanged = argv.skipIfUnchanged || false;

// 统一去重工具函数
function normalizeProductId(variantId) {
  if (!variantId) return null;
  return variantId.toString().split('_')[0];
}

// 从商品数据中提取标准化信息 - 增强版
function extractProductInfo(rawProduct, category) {
  const variantId = rawProduct.item_variant || rawProduct.variant_id || rawProduct.item_id || rawProduct.productId || rawProduct.id || rawProduct.pid;
  const productId = normalizeProductId(variantId);
  
  if (!productId || !variantId) return null;
  
  // 基础信息
  const product = {
    productId: productId,
    variantId: variantId.toString(),
    detailUrl: rawProduct.detailUrl || rawProduct.url || rawProduct.link || rawProduct.href || '',
    productName: rawProduct.item_name || rawProduct.name || rawProduct.title || '',
    category: category
  };
  
  // 🚀 增强字段提取（零性能影响）
  // 价格信息
  if (rawProduct.price || rawProduct.original_price || rawProduct.sale_price) {
    product.originalPrice = rawProduct.original_price || rawProduct.price_original || rawProduct.was_price;
    product.currentPrice = rawProduct.price || rawProduct.sale_price || rawProduct.current_price;
    product.currency = rawProduct.currency || 'JPY';
  }
  
  // 图片信息
  if (rawProduct.image || rawProduct.thumbnail || rawProduct.main_image) {
    product.mainImage = rawProduct.image || rawProduct.thumbnail || rawProduct.main_image;
    if (rawProduct.images && Array.isArray(rawProduct.images)) {
      product.allImages = rawProduct.images;
    }
  }
  
    
  // 商品标签和分类
  if (rawProduct.tags || rawProduct.labels || rawProduct.badges) {
    product.tags = rawProduct.tags || rawProduct.labels || rawProduct.badges;
  }
  
  if (rawProduct.subcategory || rawProduct.type || rawProduct.product_type) {
    product.subcategory = rawProduct.subcategory || rawProduct.type || rawProduct.product_type;
  }
  
  // 变体信息（颜色、尺寸等）
  if (rawProduct.color || rawProduct.colour) {
    product.color = rawProduct.color || rawProduct.colour;
  }
  
  if (rawProduct.size) {
    product.size = rawProduct.size;
  }
  
  if (rawProduct.variants || rawProduct.options) {
    product.variants = rawProduct.variants || rawProduct.options;
  }
  
  // 评分和评价
  if (rawProduct.rating || rawProduct.review_count) {
    product.rating = rawProduct.rating;
    product.reviewCount = rawProduct.review_count;
  }
  
  // 促销信息
  if (rawProduct.discount || rawProduct.promotion || rawProduct.sale) {
    product.discountInfo = rawProduct.discount || rawProduct.promotion;
    product.isOnSale = rawProduct.sale || false;
  }
  
  // 清理空值
  Object.keys(product).forEach(key => {
    if (product[key] === '' || product[key] === null || product[key] === undefined) {
      delete product[key];
    }
  });
  
  return product;
}

// 分页API调用函数 - 优化版
async function callPaginationApi(page, apiUrl, productMap, uniqueProductIds, category) {
  let offset = 0;
  let page_num = 1;
  const pageSize = 24; // CallawayJP常用分页大小
  let requestCount = 0;
  
  console.log(`开始调用分页API: ${apiUrl}`);
  
  while (requestCount < 15) { // 限制最大请求次数
    try {
      requestCount++;
      
      // 多种API URL构建方式
      const apiVariants = [
        `${apiUrl}?offset=${offset}&limit=${pageSize}`,
        `${apiUrl}?page=${page_num}&size=${pageSize}`,
        `${apiUrl}?from=${offset}&size=${pageSize}`,
        `${apiUrl}?skip=${offset}&take=${pageSize}`,
        apiUrl.includes('?') ? `${apiUrl}&offset=${offset}&size=${pageSize}` : `${apiUrl}?offset=${offset}&size=${pageSize}`
      ];
      
      console.log(`尝试第${requestCount}页 (offset=${offset}, page=${page_num})`);
      
      let response = null;
      
      // 尝试多种API变体
      for (const variant of apiVariants) {
        try {
          response = await page.evaluate(async (url) => {
            const resp = await fetch(url, {
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              }
            });
            if (resp.ok) {
              const data = await resp.json();
              return data;
            }
            return null;
          }, variant);
          
          if (response && (response.products || response.data || response.items || response.hits)) {
            console.log(`API变体成功: ${variant}`);
            break;
          }
        } catch (e) {
          // 继续尝试下一个变体
        }
      }
      
      // 处理API响应
      let products = null;
      if (response) {
        products = response.products || response.data || response.items || response.hits || 
                  (response.data && response.data.products) || 
                  (response.search && response.search.results && response.search.results.hits);
      }
      
      if (!products || !Array.isArray(products) || products.length === 0) {
        console.log('API返回空数据或格式不正确，停止请求');
        if (response) {
          console.log('响应结构:', Object.keys(response));
        }
        break;
      }
      
      // 处理返回的商品数据
      let newProductsCount = 0;
      for (const rawProduct of products) {
        const productInfo = extractProductInfo(rawProduct, category);
        if (productInfo && productInfo.productId && !productMap.has(productInfo.variantId)) {
          productMap.set(productInfo.variantId, productInfo);
          uniqueProductIds.add(productInfo.productId);
          newProductsCount++;
        }
      }
      
      console.log(`第${requestCount}页新增商品: ${newProductsCount}个 (总计: ${uniqueProductIds.size}个独特商品)`);
      
      // 调试：打印第一个商品的结构
      if (requestCount === 1 && products.length > 0) {
        console.log('第一个API返回商品结构:', JSON.stringify(products[0], null, 2));
      }
      
      if (newProductsCount === 0) {
        console.log('本页无新商品，停止请求');
        break;
      }
      
      offset += pageSize;
      page_num++;
      
      // 短暂延迟，避免请求过快
      await page.waitForTimeout(300);
      
    } catch (e) {
      console.log(`分页请求失败 (第${requestCount}页):`, e.message);
      break;
    }
  }
  
  console.log(`分页接口请求完成，共请求${requestCount}页，获得${uniqueProductIds.size}个独特商品`);
  return requestCount;
}

// GLM 4.6 超强滚动兜底方法 - 终极增强版
async function fallbackScrollMethod(page, productMap, uniqueProductIds, expectedCount, category) {
  console.log('🚀 启动 GLM 4.6 超强滚动兜底抓取引擎...');
  
  const startedAt = Date.now();
  const maxDurationMs = 3 * 60 * 1000; // 严格3分钟时间限制
  const maxIdleCycles = 30; // 最大空闲周期
  const maxClickAttempts = Math.max(20, Math.ceil(expectedCount / Math.max(uniqueProductIds.size || 1, 1)) * 2);
  
  let idleCycles = 0;
  let clickAttempts = 0;
  let scrollCount = 0;
  let totalHarvested = 0;
  let lastPerformanceCheck = Date.now();
  
  console.log(`⚙️  配置参数: 时间限制=${Math.round(maxDurationMs/1000)}秒, 空闲限制=${maxIdleCycles}, 点击限制=${maxClickAttempts}`);
  
  // 🔍 超强商品收集器 - 多层级检测机制
  const collectVisibleProducts = async () => {
    try {
      const products = await page.evaluate(() => {
        const items = [];
        
        // 策略1: 精确PID链接抓取
        const pidLinks = document.querySelectorAll('a[href*="?pid="]');
        pidLinks.forEach(link => {
          const href = link.href;
          const pidMatch = href.match(/\?pid=([A-Za-z0-9_-]+)/);
          if (!pidMatch) return;
          
          const fullId = pidMatch[1];
          const productId = fullId.split('_')[0];
          if (!productId) return;
          
          // 多层级标题检测
          const titleCandidates = [
            link.querySelector('[data-testid="product-title"]'),
            link.querySelector('img[alt]'),
            link.querySelector('.product-title, .title, h1, h2, h3'),
            link.closest('.product-card, .item-card')?.querySelector('.title, h1, h2, h3'),
            link
          ].filter(Boolean);
          
          const name = titleCandidates
            .map(el => (el.innerText || el.textContent || el.getAttribute('alt') || '').trim())
            .find(text => text.length > 0) || '';
          
          // 🚀 增强字段提取 - 策略1
          const productData = {
            productId,
            variantId: fullId,
            detailUrl: href,
            productName: name,
            source: 'pid-link'
          };
          
          // 🚀 增强价格提取 - 从链接容器中查找价格
          const container = link.closest('div, article, section, li') || link.parentElement;
          if (container) {
            const containerText = container.textContent || '';
            const priceMatch = containerText.match(/[￥¥]\s*[\d,]+(?:\s*\([^)]*\))?/g);
            if (priceMatch && priceMatch.length > 0) {
              productData.priceText = priceMatch[0];
              productData.allPrices = priceMatch;
            }
            
            // 🚀 增强图片提取 - 从容器中查找图片
            const imgEl = container.querySelector('img');
            if (imgEl && imgEl.src && !imgEl.src.includes('data:') && !imgEl.src.includes('placeholder')) {
              productData.mainImage = imgEl.src;
              productData.imageAlt = imgEl.alt || '';
            }
            
            // 🚀 促销信息提取
            if (containerText.includes('OFF') || containerText.includes('セール') || containerText.includes('割引')) {
              productData.hasPromotion = true;
              const promoMatch = containerText.match(/(\d+%?\s*OFF|\d+%?\s*割引|セール)/gi);
              if (promoMatch) {
                productData.promotionText = promoMatch.join(', ');
              }
            }
          }
          
          items.push(productData);
        });
        
        // 策略2: 商品卡片结构检测
        const productCards = document.querySelectorAll('.c-productCard, [class*="product"], [class*="item-card"]');
        productCards.forEach(card => {
          const link = card.querySelector('a[href*="?pid="]');
          if (!link) return;
          
          const href = link.href;
          const pidMatch = href.match(/\?pid=([A-Za-z0-9_-]+)/);
          if (!pidMatch) return;
          
          const fullId = pidMatch[1];
          const productId = fullId.split('_')[0];
          if (!productId) return;
          
          // 检查是否已通过策略1收集
          const exists = items.find(item => item.variantId === fullId);
          if (exists) return;
          
          const titleEl = card.querySelector('.title, .name, h1, h2, h3, [data-testid="product-title"]');
          const name = titleEl ? (titleEl.innerText || titleEl.textContent || '').trim() : '';
          
          // 🚀 增强字段提取 - 策略2 (商品卡片)
          const productData = {
            productId,
            variantId: fullId,
            detailUrl: href,
            productName: name,
            source: 'product-card'
          };
          
          // 🚀 策略2增强提取 - 基于实际DOM结构
          const cardText = card.textContent || '';
          
          // 价格提取 - 使用正则匹配
          const priceMatch = cardText.match(/[￥¥]\s*[\d,]+(?:\s*\([^)]*\))?/g);
          if (priceMatch && priceMatch.length > 0) {
            productData.priceText = priceMatch[0];
            productData.allPrices = priceMatch;
            
            // 区分原价和现价
            if (priceMatch.length > 1) {
              productData.originalPriceText = priceMatch[1]; // 通常第二个是原价
              productData.currentPriceText = priceMatch[0];  // 第一个是现价
            }
          }
          
          // 图片提取 - 更宽泛的匹配
          const imgEl = card.querySelector('img[src*="product"], img[src*="item"], img[src*="cdn"], img');
          if (imgEl && imgEl.src && !imgEl.src.includes('data:') && !imgEl.src.includes('placeholder')) {
            productData.mainImage = imgEl.src;
            productData.imageAlt = imgEl.alt || '';
          }
          
          // 🚀 促销和标签提取 - 基于文本分析
          if (cardText.includes('OFF') || cardText.includes('セール') || cardText.includes('割引')) {
            productData.hasPromotion = true;
            const promoMatch = cardText.match(/(\d+%?\s*OFF|\d+%?\s*割引|セール)/gi);
            if (promoMatch) {
              productData.promotionText = promoMatch.join(', ');
            }
          }
          
            
          // NEW/SALE标签检测
          const tags = [];
          if (cardText.includes('NEW') || cardText.includes('新商品')) tags.push('NEW');
          if (cardText.includes('SALE') || cardText.includes('セール')) tags.push('SALE');
          if (cardText.includes('LIMITED') || cardText.includes('限定')) tags.push('LIMITED');
          if (tags.length > 0) {
            productData.tags = tags;
          }
          
          // 从URL推断分类
          if (href.includes('/tops/')) productData.subcategory = 'tops';
          else if (href.includes('/bottoms/')) productData.subcategory = 'bottoms';
          else if (href.includes('/outer/')) productData.subcategory = 'outer';
          else if (href.includes('/accessories/')) productData.subcategory = 'accessories';
          
          items.push(productData);
        });
        
        return items;
      });
      
      let newItems = 0;
      let duplicateItems = 0;
      
      for (const product of products) {
        const existingProduct = productMap.get(product.variantId);
        
        // 🚀 智能数据合并：增强数据优先
        if (!existingProduct) {
          // 新商品：直接保存增强数据
          const enhancedProduct = {
            ...product, // 保留所有增强字段
            category    // 确保分类字段正确
          };
          
          productMap.set(product.variantId, enhancedProduct);
          uniqueProductIds.add(product.productId);
          newItems++;
        } else {
          // 已存在商品：用增强数据覆盖基础数据
          const hasEnhancedFields = product.priceText || product.mainImage || product.promotionText || product.hasPromotion;
          
          if (hasEnhancedFields) {
            // 合并增强字段到现有商品
            const mergedProduct = {
              ...existingProduct, // 保留基础字段
              ...product,         // 用增强字段覆盖
              category           // 确保分类字段正确
            };
            
            productMap.set(product.variantId, mergedProduct);
            newItems++; // 计为新增（实际是增强）
          } else {
            duplicateItems++;
          }
        }
      }
      
      return { newItems, duplicateItems, totalFound: products.length };
      
    } catch (error) {
      console.log(`⚠️  商品收集器异常: ${error.message}`);
      return { newItems: 0, duplicateItems: 0, totalFound: 0 };
    }
  };
  
  // 🎯 智能按钮猎手 - 高精度检测与点击
  const tryClickLoadMore = async () => {
    try {
      const result = await page.evaluate(() => {
        const outcome = { clicked: false, buttonText: '', buttonType: '', attemptedButtons: [] };
        
        // 高优先级按钮定位策略
        const buttonSelectors = [
          'button[class*="load"], button[class*="more"], button[class*="show"]',
          'a[class*="load"], a[class*="more"], a[class*="show"]',
          'button, input[type="button"], [role="button"]',
          'a[href*="#"], a[href*="javascript"]',
          '.btn, .button, [class*="btn-"], [class*="button-"]'
        ];
        
        // 日文关键词优先级检测
        const japaneseKeywords = [
          'さらに表示', 'もっと見る', 'もっと表示', '続きを見る', 
          '全て見る', 'すべて見る', '次のページ', '次へ',
          'さらに', '続き', '表示', 'もっと'
        ];
        
        const englishKeywords = [
          'load more', 'show more', 'view more', 'see more',
          'more products', 'more items', 'load', 'more', 'next'
        ];
        
        // 策略1: 精确文本匹配
        for (const selector of buttonSelectors) {
          const elements = document.querySelectorAll(selector);
          
          for (const el of elements) {
            if (!el.offsetParent || el.disabled) continue;
            
            const text = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
            if (!text) continue;
            
            outcome.attemptedButtons.push({ text, selector });
            
            // 优先匹配日文关键词
            const matchedJapanese = japaneseKeywords.find(keyword => text.includes(keyword));
            if (matchedJapanese) {
              outcome.buttonText = el.innerText || el.textContent || '';
              outcome.buttonType = 'japanese-keyword';
              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
              setTimeout(() => el.click(), 100);
              outcome.clicked = true;
              return outcome;
            }
            
            // 次优匹配英文关键词
            const matchedEnglish = englishKeywords.find(keyword => text.includes(keyword));
            if (matchedEnglish) {
              outcome.buttonText = el.innerText || el.textContent || '';
              outcome.buttonType = 'english-keyword';
              el.scrollIntoView({ behavior: 'smooth', block: 'center' });
              setTimeout(() => el.click(), 100);
              outcome.clicked = true;
              return outcome;
            }
          }
        }
        
        // 策略2: 模糊匹配兜底
        const allClickable = document.querySelectorAll('button, a, [role="button"], input[type="button"]');
        for (const el of allClickable) {
          if (!el.offsetParent || el.disabled) continue;
          
          const text = (el.innerText || el.textContent || el.value || '').toLowerCase().trim();
          if (text.length < 2 || text.length > 50) continue;
          
          const hasLoadingWords = /show|load|more|view|see|next|続|表示|もっと|さらに|全|次/.test(text);
          if (hasLoadingWords) {
            outcome.buttonText = el.innerText || el.textContent || '';
            outcome.buttonType = 'fuzzy-match';
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => el.click(), 100);
            outcome.clicked = true;
            return outcome;
          }
        }
        
        return outcome;
      });
      
      if (result.clicked) {
        console.log(`🎯 成功点击按钮: "${result.buttonText}" (类型: ${result.buttonType})`);
      } else if (result.attemptedButtons.length > 0) {
        console.log(`🔍 扫描到 ${result.attemptedButtons.length} 个按钮，但无匹配项`);
      }
      
      return result;
      
    } catch (error) {
      console.log(`⚠️  按钮猎手异常: ${error.message}`);
      return { clicked: false, buttonText: '', buttonType: 'error' };
    }
  };
  
  // 🚀 开始抓取流程
  console.log('📊 执行初始页面扫描...');
  let harvestResult = await collectVisibleProducts();
  totalHarvested += harvestResult.newItems;
  
  if (harvestResult.newItems > 0) {
    console.log(`✅ 初始扫描: 发现 ${harvestResult.totalFound} 个商品，新增 ${harvestResult.newItems} 个，重复 ${harvestResult.duplicateItems} 个`);
    console.log(`📈 当前累计: ${uniqueProductIds.size}/${expectedCount} (${((uniqueProductIds.size/expectedCount)*100).toFixed(1)}%)`);
  }
  
  // 🔄 主循环: 智能滚动与点击
  while (uniqueProductIds.size < expectedCount) {
    const elapsedMs = Date.now() - startedAt;
    const progressPercent = ((uniqueProductIds.size / expectedCount) * 100).toFixed(1);
    
    // 时间限制检查
    if (elapsedMs > maxDurationMs) {
      console.log(`⏰ 已达时间上限 ${Math.round(elapsedMs/1000)}秒，强制停止`);
      break;
    }
    
    // 性能检查（每30秒报告一次）
    if (elapsedMs - lastPerformanceCheck > 30000) {
      const speed = totalHarvested / (elapsedMs / 60000); // 每分钟抓取数
      console.log(`⚡ 性能报告: 已运行 ${Math.round(elapsedMs/1000)}秒，抓取速度 ${speed.toFixed(1)}/分钟，完成度 ${progressPercent}%`);
      lastPerformanceCheck = elapsedMs;
    }
    
    const beforeCount = uniqueProductIds.size;
    
    // 智能滚动策略
    try {
      await page.evaluate(() => {
        // 多层级滚动策略
        const currentY = window.pageYOffset;
        const maxY = document.body.scrollHeight - window.innerHeight;
        
        if (currentY < maxY * 0.3) {
          // 前30%: 快速滚动
          window.scrollBy(0, window.innerHeight * 1.5);
        } else if (currentY < maxY * 0.7) {
          // 中间40%: 标准滚动
          window.scrollBy(0, window.innerHeight);
        } else {
          // 后30%: 慢速滚动，确保不遗漏
          window.scrollBy(0, window.innerHeight * 0.7);
        }
        
        // 延迟滚动到底部，触发可能的懒加载
        setTimeout(() => {
          if (window.pageYOffset < maxY) {
            window.scrollTo(0, document.body.scrollHeight);
          }
        }, 200);
      });
      
      await page.waitForTimeout(500); // 给页面足够时间渲染
      scrollCount++;
      
    } catch (scrollError) {
      console.log(`⚠️  滚动异常: ${scrollError.message}`);
      await page.waitForTimeout(300);
    }
    
    // 收集滚动后的新商品
    harvestResult = await collectVisibleProducts();
    totalHarvested += harvestResult.newItems;
    
    const currentCount = uniqueProductIds.size;
    const gained = currentCount - beforeCount;
    
    if (gained > 0) {
      idleCycles = 0;
      console.log(`📈 滚动第${scrollCount}次: 新增 ${gained} 个商品，累计 ${currentCount}/${expectedCount} (${((currentCount/expectedCount)*100).toFixed(1)}%)`);
    } else {
      idleCycles++;
      if (idleCycles % 5 === 0) {
        console.log(`⏳ 连续 ${idleCycles} 轮无新增，继续搜索...`);
      }
    }
    
    // 提前完成检查
    if (currentCount >= expectedCount) {
      console.log(`🎉 已达到预期数量! (${currentCount}/${expectedCount})`);
      break;
    }
    
    // 智能按钮点击策略
    if (idleCycles >= 2) {
      if (clickAttempts >= maxClickAttempts) {
        console.log(`🛑 已达最大点击次数 (${maxClickAttempts})，停止按钮点击`);
        
        // 最后尝试滚动策略
        if (idleCycles < maxIdleCycles) {
          continue;
        } else {
          break;
        }
      }
      
      console.log(`🔍 尝试查找加载更多按钮... (第${clickAttempts + 1}次)`);
      
      const prevDomCount = await page.evaluate(() => document.querySelectorAll('a[href*="?pid="]').length);
      const loadResult = await tryClickLoadMore();
      
      if (loadResult.clicked) {
        clickAttempts++;
        idleCycles = 0;
        
        console.log(`✅ 按钮点击成功 (${clickAttempts}/${maxClickAttempts}): "${loadResult.buttonText}"`);
        
        // 智能等待新内容加载
        try {
          await Promise.race([
            page.waitForFunction(
              previous => document.querySelectorAll('a[href*="?pid="]').length > previous,
              prevDomCount,
              { timeout: 10000 }
            ),
            page.waitForTimeout(3000) // 最短等待时间
          ]);
          
          console.log('📦 检测到新内容加载');
          
        } catch (waitError) {
          console.log('⏰ 等待新内容超时，继续处理现有内容');
        }
        
        await page.waitForTimeout(1000); // 额外稳定时间
        
        // 立即收集点击后的新商品
        const postClickHarvest = await collectVisibleProducts();
        if (postClickHarvest.newItems > 0) {
          totalHarvested += postClickHarvest.newItems;
          console.log(`📈 点击后立即收获 ${postClickHarvest.newItems} 个新商品`);
        } else {
          console.log('📭 点击后暂无新商品，等待后续滚动发现');
          idleCycles = 1; // 适度增加空闲计数
        }
        
        continue;
      } else {
        console.log('❌ 未找到可点击的加载按钮');
      }
    }
    
    // 最终退出条件
    if (idleCycles >= maxIdleCycles) {
      console.log(`🏁 连续 ${idleCycles} 轮无新增商品，结束兜底抓取`);
      break;
    }
  }
  
  // 📊 最终统计报告
  const finalElapsedMs = Date.now() - startedAt;
  const finalProgressPercent = ((uniqueProductIds.size / expectedCount) * 100).toFixed(1);
  const avgSpeed = totalHarvested / (finalElapsedMs / 60000);
  
  console.log('\n🎯 ===== GLM 4.6 滚动兜底完成报告 =====');
  console.log(`⏱️  总耗时: ${Math.round(finalElapsedMs/1000)}秒 / ${Math.round(finalElapsedMs/60000 * 10)/10}分钟`);
  console.log(`🔄 滚动次数: ${scrollCount}`);
  console.log(`🎯 按钮点击: ${clickAttempts}/${maxClickAttempts}`);
  console.log(`📈 商品收获: ${totalHarvested}个新商品`);
  console.log(`🏆 最终结果: ${uniqueProductIds.size}/${expectedCount} (${finalProgressPercent}%)`);
  console.log(`⚡ 平均速度: ${avgSpeed.toFixed(1)}商品/分钟`);
  console.log(`🎖️  性能评级: ${finalProgressPercent >= 90 ? 'S级优秀' : finalProgressPercent >= 80 ? 'A级良好' : finalProgressPercent >= 70 ? 'B级一般' : 'C级需优化'}`);
  
  return {
    clickAttempts,
    scrollCount,
    totalHarvested,
    finalProgress: finalProgressPercent,
    elapsedSeconds: Math.round(finalElapsedMs/1000)
  };
}

async function findLatestRawFile(category) {
  const resultsDir = path.join(__dirname, '../results');
  try {
    const files = await fs.readdir(resultsDir);
    const timestampRegex = new RegExp(`^raw_links_${category}_(\\d{4}-\\d{2}-\\d{2}T\\d{2}-\\d{2}-\\d{2}-\\d{3}Z)\\.json$`);
    const latestRegex = new RegExp(`^raw_links_${category}_latest\\.json$`);

    const candidates = [];
    for (const fileName of files) {
      const timestampMatch = fileName.match(timestampRegex);
      if (timestampMatch) {
        candidates.push({
          name: fileName,
          sortKey: timestampMatch[1],
          type: 'timestamp'
        });
        continue;
      }
      if (latestRegex.test(fileName)) {
        const fullPath = path.join(resultsDir, fileName);
        const stat = await fs.stat(fullPath);
        candidates.push({
          name: fileName,
          sortKey: stat.mtime.toISOString(),
          type: 'latest'
        });
      }
    }

    if (!candidates.length) {
      return null;
    }

    candidates.sort((a, b) => (a.sortKey > b.sortKey ? -1 : 1));
    const chosen = candidates[0];
    const filePath = path.join(resultsDir, chosen.name);
    const content = await fs.readFile(filePath, 'utf-8');
    return {
      path: filePath,
      data: JSON.parse(content),
      type: chosen.type
    };
  } catch (err) {
    return null;
  }
}

async function scrapeCategory(url, category) {
  console.log(`\n开始抓取分类: ${category}`);
  console.log(`URL: ${url}`);
  console.log(`开始时间: ${new Date().toISOString()}`);

  const startTime = Date.now();
  let paginationRequestCount = 0;
  let usedPaginationApi = false;
  let usedFallbackMethod = false;
  let existingSnapshot = null;

  if (skipIfUnchanged) {
    existingSnapshot = await findLatestRawFile(category);
    if (existingSnapshot) {
      console.log(`📦 检测到已存在的抓取文件: ${path.basename(existingSnapshot.path)}`);
    }
  }

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });
    
    const page = await context.newPage();
    
    // 用于存储所有商品的数据结构，使用Map进行去重
    const productMap = new Map(); // key: variantId, value: productInfo
    const uniqueProductIds = new Set(); // 用于统计独特商品数量
    
    // 访问页面
    console.log('正在访问页面...');
    await page.goto(url, { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 
    });
    
    // 更充分的等待时间，确保页面完全加载
    await page.waitForTimeout(8000);
    
    // 等待内容加载
    try {
      await page.waitForSelector('.c-productCard, [class*="product"], a[href*="?pid="]', { timeout: 15000 });
    } catch (e) {
      console.log('等待商品卡片加载超时，继续执行...');
    }
    
    // 增强版预期商品数量获取
    console.log('正在获取预期商品数量...');
    
    let expectedCount = await page.evaluate(() => {
      // 打印页面关键信息用于调试
      console.log('当前页面URL:', window.location.href);
      console.log('页面标题:', document.title);
      
      // 优先精确查找 "222 検索結果" 模式
      const allElements = document.querySelectorAll('*');
      
      // 收集所有文本内容
      const allTexts = [];
      for (const el of allElements) {
        const text = (el.innerText || el.textContent || '').trim();
        if (text && text.length < 200 && text.match(/\d/)) {
          allTexts.push(text);
        }
      }
      
      console.log('页面中包含数字的文本样本:', allTexts.slice(0, 30));
      
      // 多种正则模式，按优先级排序
      const patterns = [
        /(\d+)\s*検索結果/,
        /検索結果[:：\s]*(\d+)/,
        /(\d+)\s*件/,
        /(\d+)\s*商品/,
        /(\d+)\s*items?/i,
        /(\d+)\s*products?/i,
        /(\d+)\s*結果/,
        /(\d+)\s*個/,
        /全\s*(\d+)\s*件/,
        /合計\s*(\d+)/,
        /total[:\s]*(\d+)/i,
        /(\d+)\s*アイテム/,
        /(\d+)\s*点/
      ];
      
      // 依次匹配，找到第一个符合条件的数值后立即返回
      for (const text of allTexts) {
        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match) {
            const num = parseInt(match[1]);
            // 限定在50-1000区间
            if (num >= 50 && num <= 1000) {
              console.log(`匹配成功: "${text}" -> ${num} (模式: ${pattern.source})`);
              return num;
            }
          }
        }
      }
      
      return null;
    });
    
    if (!expectedCount) {
      console.log('未找到检索数量，无法继续，请检查页面结构');
      await browser.close();
      process.exit(1);
    }
    
    console.log(`预期商品数量: ${expectedCount}`);
    
    // 添加日志提示但不修改数值
    if (expectedCount === 222) {
      console.log('✅ 成功匹配到页面显示的222个商品');
    } else {
      console.log(`⚠️ 检测到${expectedCount}个商品，与预期可能不同`);
    }

    if (skipIfUnchanged && existingSnapshot) {
      const previousExpected = existingSnapshot.data?.expectedCount;
      const previousActual = existingSnapshot.data?.actualCount;
      if (previousExpected === expectedCount && previousActual === expectedCount) {
        console.log('🔁 页面商品数量与最近一次抓取一致，跳过本次抓取。');
        console.log(`输出文件: ${existingSnapshot.path} (复用现有数据)`);
        await browser.close();
        return existingSnapshot.data;
      }
    }
    
    // 第一步：解析 __NEXT_DATA__ 中的首批商品数据
    console.log('步骤1: 解析 __NEXT_DATA__ 中的首批商品数据...');
    let nextDataProducts = [];
    
    try {
      const nextData = await page.evaluate(() => {
        const nextDataEl = document.getElementById('__NEXT_DATA__');
        if (nextDataEl) {
          return JSON.parse(nextDataEl.textContent);
        }
        return null;
      });
      
      if (nextData && nextData.props && nextData.props.pageProps) {
        // 更全面的数据路径搜索
        const possiblePaths = [
          'data.search.results.hits',
          'searchResults.hits', 
          'products',
          'data.products',
          'pageProps.searchResults',
          'initialProps.products',
          'data.searchResults.products',
          'searchData.products',
          'pageProps.data.products',
          'props.products',
          'catalog.products',
          'items'
        ];
        
        for (const path of possiblePaths) {
          let products = nextData.props.pageProps;
          const keys = path.split('.');
          
          for (const key of keys) {
            if (products && products[key]) {
              products = products[key];
            } else {
              products = null;
              break;
            }
          }
          
          if (products && Array.isArray(products) && products.length > 0) {
            console.log(`从 __NEXT_DATA__ 中找到商品: ${products.length}个 (路径: ${path})`);
            nextDataProducts = products;
            break;
          }
        }
        
        // 将首批数据添加到产品映射中
        for (const rawProduct of nextDataProducts) {
          const productInfo = extractProductInfo(rawProduct, category);
          if (productInfo && productInfo.productId) {
            productMap.set(productInfo.variantId, productInfo);
            uniqueProductIds.add(productInfo.productId);
          }
        }
        
        console.log(`首批数据: ${productMap.size} 个变体，${uniqueProductIds.size} 个独特商品`);
      }
    } catch (e) {
      console.log('解析 __NEXT_DATA__ 失败:', e.message);
    }
    
    // 第二步：尝试通过分页接口获取更多商品数据
    console.log('步骤2: 尝试调用分页接口获取更多商品...');
    
    try {
      // 增强的分页接口发现逻辑
      const paginationApiInfo = await page.evaluate(async () => {
        const possibleApiPatterns = [
          '/api/search',
          '/api/products', 
          '/api/catalog',
          '/search',
          '_next/data',
          'algolia',
          'elasticsearch',
          'graphql',
          '/api/v1',
          '/api/v2',
          '/api/search-api'
        ];
        
        // 检查脚本中的API端点
        const scripts = Array.from(document.querySelectorAll('script'));
        for (const script of scripts) {
          const content = script.textContent || '';
          
          for (const pattern of possibleApiPatterns) {
            if (content.includes(pattern)) {
              // 多种URL提取模式
              const urlPatterns = [
                new RegExp(`["']([^"']*${pattern}[^"']*)["']`, 'gi'),
                new RegExp(`url["'\\s]*:["'\\s]*([^"']*${pattern}[^"']*)`, 'gi'),
                new RegExp(`endpoint["'\\s]*:["'\\s]*([^"']*${pattern}[^"']*)`, 'gi'),
                new RegExp(`baseURL["'\\s]*:["'\\s]*([^"']*${pattern}[^"']*)`, 'gi')
              ];
              
              for (const urlPattern of urlPatterns) {
                const matches = [...content.matchAll(urlPattern)];
                for (const match of matches) {
                  if (match[1] && (match[1].startsWith('http') || match[1].startsWith('/'))) {
                    console.log(`发现潜在API端点: ${match[1]}`);
                    const fullUrl = match[1].startsWith('http') ? match[1] : 
                                   `${window.location.origin}${match[1]}`;
                    return {
                      apiUrl: fullUrl,
                      pattern: pattern
                    };
                  }
                }
              }
            }
          }
        }
        
        return null;
      });
      
      // 如果找到了分页信息，尝试调用API
      if (paginationApiInfo) {
        console.log('找到分页配置:', paginationApiInfo);
        paginationRequestCount = await callPaginationApi(page, paginationApiInfo.apiUrl, productMap, uniqueProductIds, category);
        if (paginationRequestCount > 0) {
          usedPaginationApi = true;
        }
      } else {
        console.log('未找到分页接口信息，将使用滚动方法');
      }
    } catch (e) {
      console.log('分页接口调用失败:', e.message);
    }
    
    // 第三步：滚动+点击按钮的兜底逻辑
    if (!usedPaginationApi || uniqueProductIds.size < expectedCount * 0.7) {
      if (!usedPaginationApi) {
        console.log('步骤3: 未能调用分页接口，回退到滚动抓取');
        usedFallbackMethod = true;
      } else {
        console.log(`步骤3: 分页接口数据不足 (${uniqueProductIds.size}/${expectedCount})，补充滚动抓取`);
        usedFallbackMethod = true;
      }
      
      await fallbackScrollMethod(page, productMap, uniqueProductIds, expectedCount, category);
    }
    
    // 最终统计
    const actualCount = uniqueProductIds.size;
    const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log('\n========== 抓取完成 ==========');
    console.log(`耗时(秒): ${elapsedTime}`);
    console.log(`分页请求次数: ${paginationRequestCount}`);
    console.log(`expectedCount: ${expectedCount}`);
    console.log(`actualCount: ${actualCount}`);
    console.log(`使用分页接口: ${usedPaginationApi ? '是' : '否'}`);
    console.log(`使用滚动兜底: ${usedFallbackMethod ? '是' : '否'}`);
    console.log(`完成度: ${((actualCount / expectedCount) * 100).toFixed(1)}%`);
    
    // 准备输出数据
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // 为每个链接添加category字段，确保结构一致 - 包含所有增强字段
    const linksWithCategory = Array.from(productMap.values()).map(link => ({
      ...link,  // 🚀 保留所有字段包括增强字段 (priceText, mainImage, promotionText, etc.)
      category: category  // 确保分类字段正确
    }));
    
    const outputData = {
      category: category,
      url: url,
      expectedCount: expectedCount,
      actualCount: actualCount,
      links: linksWithCategory
    };
    
    // 保存结果
    const outputDir = path.join(__dirname, '../results');
    await fs.mkdir(outputDir, { recursive: true });
    
    const outputFileName = overwriteLatest
      ? `raw_links_${category}_latest.json`
      : `raw_links_${category}_${timestamp}.json`;
    const outputFile = path.join(outputDir, outputFileName);
    await fs.writeFile(outputFile, JSON.stringify(outputData, null, 2));
    
    console.log(`输出文件: ${outputFile}`);
    
    // 仅在数量不足时保存调试信息
    if (actualCount < expectedCount * 0.8) {
      console.log('\n⚠️ 警告: 实际抓取数量少于预期的80%');
      console.log(`缺少: ${expectedCount - actualCount} 个商品`);
      
      const screenshotFile = path.join(outputDir, `error_${category}_${timestamp}.png`);
      await page.screenshot({ path: screenshotFile, fullPage: true });
      console.log(`已保存调试截图: ${screenshotFile}`);
      
      const htmlContent = await page.content();
      const htmlFile = path.join(outputDir, `error_${category}_${timestamp}.html`);
      await fs.writeFile(htmlFile, htmlContent);
      console.log(`已保存调试页面: ${htmlFile}`);
    }
    
    await browser.close();
    return outputData;
    
  } catch (error) {
    console.error('抓取过程出错:', error);
    await browser.close();
    process.exit(1);
  }
}

// 执行主函数
(async () => {
  await scrapeCategory(argv.url, argv.category);
})();
