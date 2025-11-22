#!/usr/bin/env node

/**
 * 库存巡检脚本 - Penguin by Munsingwear / 万星威
 *
 * 复用本品牌 unified_detail_scraper.js 的抓取逻辑，只提取 variantInventory
 *
 * 使用方式:
 *   node check_inventory.js --input golf_content/munsingwear/munsingwear_products_xxx.json \
 *        --output results/munsingwear_inventory_xxx.json --limit 20
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');
const path = require('path');

const BRAND_CONFIG = {
    munsingwear: {
        name: 'Penguin by Munsingwear / 万星威',
        label: '万星威'
    }
};

class InventoryChecker {
    constructor(options = {}) {
        this.brand = options.brand || 'munsingwear';
        this.brandConfig = BRAND_CONFIG[this.brand];
        if (!this.brandConfig) {
            throw new Error(`未知品牌配置: ${this.brand}`);
        }

        this.limit = options.limit || 0;
        this.concurrent = options.concurrent || 2;
        this.delay = options.delay || 800;
        this.retry = options.retry || 1;  // 单个商品失败时的重试次数，默认1次

        this.scraper = new UnifiedDetailScraper({
            headless: true,
            debug: false,
            timeout: 60000
        });
    }

    loadProducts(inputPath) {
        const raw = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
        let products = [];

        if (Array.isArray(raw)) {
            products = raw;
        } else if (raw.products) {
            if (Array.isArray(raw.products)) {
                products = raw.products;
            } else {
                products = Object.entries(raw.products).map(([id, p]) => ({
                    productId: id,
                    ...p
                }));
            }
        } else if (raw.records) {
            products = raw.records;
        }

        products = products.map(p => ({
            productId: p.productId || p.product_id || p.id || '',
            url: p.detailUrl || p.detail_url || p.url || p.商品链接 || '',
            stockStatusText: p.stockStatusText || p.库存状态 || ''
        })).filter(p => p.url);

        if (this.limit > 0 && products.length > this.limit) {
            return products.slice(0, this.limit);
        }
        return products;
    }

    async checkSingleProduct(product) {
        const { productId, url } = product;
        console.log(`\n🔍 检查库存: ${productId || url}`);

        // 带重试机制的抓取
        for (let attempt = 0; attempt <= this.retry; attempt++) {
            try {
                const result = await this.scraper.scrapeDetailPage(url, { productId });
                if (!result.success) {
                    if (attempt < this.retry) {
                        console.log(`  ⚠️ 抓取失败，正在重试 (${attempt + 1}/${this.retry}): ${result.error}`);
                        await new Promise(resolve => setTimeout(resolve, 2000));  // 重试前等待2秒
                        continue;
                    }
                    console.log(`  ❌ 抓取失败（已重试 ${this.retry} 次）: ${result.error}`);
                    return {
                        productId,
                        detailUrl: url,
                        error: result.error,
                        timestamp: new Date().toISOString()
                    };
                }

                const variantInventory = result.variantInventory || [];
                const inventoryData = {
                    productId: result.productId || productId,
                    detailUrl: url,
                    variantInventory,
                    stockStatus: this.calculateStockStatus(variantInventory),
                    colors: result.colors || [],
                    sizes: result.sizes || [],
                    timestamp: new Date().toISOString()
                };

                const inStockCount = variantInventory.filter(v => v.inStock).length;
                console.log(`  ✅ ${variantInventory.length} 个变体，其中 ${inStockCount} 个有货`);
                if (attempt > 0) {
                    console.log(`  ✅ 重试成功 (尝试 ${attempt + 1} 次)`);
                }
                return inventoryData;
            } catch (error) {
                if (attempt < this.retry) {
                    console.log(`  ⚠️ 错误，正在重试 (${attempt + 1}/${this.retry}): ${error.message}`);
                    await new Promise(resolve => setTimeout(resolve, 2000));  // 重试前等待2秒
                    continue;
                }
                console.log(`  ❌ 错误（已重试 ${this.retry} 次）: ${error.message}`);
                return {
                    productId,
                    detailUrl: url,
                    error: error.message,
                    timestamp: new Date().toISOString()
                };
            }
        }
    }

    calculateStockStatus(variants) {
        if (!variants || variants.length === 0) {
            return 'unknown';
        }
        const hasStock = variants.some(v => v.inStock);
        const allInStock = variants.every(v => v.inStock);
        if (!hasStock) return 'out_of_stock';
        if (allInStock) return 'in_stock';
        return 'partial_stock';
    }

    async checkInventory(inputPath, outputPath) {
        console.log('📦 开始库存巡检...');
        console.log(`📄 输入文件: ${inputPath}`);
        console.log(`📁 输出文件: ${outputPath}`);

        const products = this.loadProducts(inputPath);
        if (!products.length) {
            console.log('⚠️ 没有可处理的商品');
            return;
        }

        const results = [];
        const errors = [];
        const skipped = [];

        const toProcess = [];
        for (const product of products) {
            if (product.stockStatusText === '都缺货') {
                console.log(`⏭️ SKIP: ${product.productId} 已标记都缺货`);
                skipped.push({
                    productId: product.productId,
                    detailUrl: product.url,
                    reason: '已标记都缺货',
                    timestamp: new Date().toISOString()
                });
            } else {
                toProcess.push(product);
            }
        }

        console.log(`📋 实际需要抓取: ${toProcess.length} 条`);

        for (let i = 0; i < toProcess.length; i += this.concurrent) {
            const batch = toProcess.slice(i, i + this.concurrent);
            const batchNum = Math.floor(i / this.concurrent) + 1;
            const totalBatches = Math.ceil(toProcess.length / this.concurrent);
            console.log(`\n[批次 ${batchNum}/${totalBatches}] 处理 ${batch.length} 个商品`);

            const batchResults = await Promise.all(batch.map((product, idx) => {
                console.log(`  [${i + idx + 1}/${toProcess.length}] ${product.productId || product.url}`);
                return this.checkSingleProduct(product);
            }));

            batchResults.forEach(res => {
                if (res.error) {
                    errors.push(res);
                } else {
                    results.push(res);
                }
            });

            if (i + this.concurrent < toProcess.length) {
                await new Promise(resolve => setTimeout(resolve, this.delay));
            }
        }

        const summary = {
            brand: this.brandConfig.name,
            timestamp: new Date().toISOString(),
            summary: {
                total: products.length,
                success: results.length,
                failed: errors.length,
                skipped: skipped.length,
                inStock: results.filter(r => r.stockStatus === 'in_stock').length,
                partialStock: results.filter(r => r.stockStatus === 'partial_stock').length,
                outOfStock: results.filter(r => r.stockStatus === 'out_of_stock').length
            },
            products: results,
            errors,
            skipped
        };

        fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2), 'utf8');
        console.log('\n' + '='.repeat(50));
        console.log('📊 巡检完成');
        console.log(`  总计: ${summary.summary.total}`);
        console.log(`  成功: ${summary.summary.success}`);
        console.log(`  失败: ${summary.summary.failed}`);
        console.log(`  跳过: ${summary.summary.skipped}`);
        console.log(`  全部有货: ${summary.summary.inStock}`);
        console.log(`  部分缺货: ${summary.summary.partialStock}`);
        console.log(`  全部缺货: ${summary.summary.outOfStock}`);
        console.log('='.repeat(50));
        console.log(`💾 输出: ${outputPath}`);
    }
}

async function main() {
    const args = process.argv.slice(2);
    const options = {
        input: null,
        output: null,
        limit: 0,
        concurrent: 2,
        delay: 800,
        retry: 1,
        brand: 'munsingwear'
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--input':
            case '-i':
                options.input = args[++i];
                break;
            case '--output':
            case '-o':
                options.output = args[++i];
                break;
            case '--limit':
            case '-l':
                options.limit = parseInt(args[++i]) || 0;
                break;
            case '--concurrent':
                options.concurrent = parseInt(args[++i]) || options.concurrent;
                break;
            case '--delay':
                options.delay = parseInt(args[++i]) || options.delay;
                break;
            case '--retry':
                options.retry = parseInt(args[++i]) || options.retry;
                break;
            case '--brand':
                options.brand = args[++i];
                break;
            case '--help':
            case '-h':
                console.log(`
库存巡检脚本 - Munsingwear / 万星威

示例:
  node check_inventory.js --input golf_content/munsingwear/munsingwear_products_xxx.json \\
       --output results/munsingwear_inventory_xxx.json --limit 20

可选参数:
  --concurrent <n>   并发数量 (默认2，建议小批测试时用1-2)
  --delay <ms>       批次间延迟 (默认800ms，全量建议1000-2000ms避免限流)
  --retry <n>        单个商品失败重试次数 (默认1次)
  --limit <n>        仅处理前 n 个商品 (建议先用 --limit 5 小批测试)
`);
                process.exit(0);
        }
    }

    if (!options.input || !options.output) {
        console.error('❌ 必须指定 --input 和 --output');
        process.exit(1);
    }

    if (!fs.existsSync(options.input)) {
        console.error(`❌ 输入文件不存在: ${options.input}`);
        process.exit(1);
    }

    const checker = new InventoryChecker(options);
    await checker.checkInventory(options.input, options.output);
}

if (require.main === module) {
    main().catch(error => {
        console.error('❌ 库存巡检失败:', error);
        process.exit(1);
    });
}

module.exports = { InventoryChecker, BRAND_CONFIG };
