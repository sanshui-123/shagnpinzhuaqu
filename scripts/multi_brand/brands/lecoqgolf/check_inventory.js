#!/usr/bin/env node

/**
 * 库存巡检脚本 - Le Coq Golf
 *
 * 从输入文件读取商品列表，抓取库存信息
 * 复用 UnifiedDetailScraper.extractVariantInventory
 *
 * 使用方式:
 * node check_inventory.js --input products.json --output inventory.json --limit 50
 * node check_inventory.js --input products.json --output inventory.json --concurrent 2
 */

const UnifiedDetailScraper = require('./unified_detail_scraper');
const fs = require('fs');
const path = require('path');

// 品牌配置 - 方便后续扩展到其他品牌
const BRAND_CONFIG = {
    lecoqgolf: {
        name: 'Le Coq Golf',
        baseUrl: 'https://store.descente.co.jp',
        colorSelector: '#color-selector li, .color-selector li',
        sizeListSelector: '.shopping_cantrol.commoditySizelist, .commoditySizelist'
    }
};

class InventoryChecker {
    constructor(options = {}) {
        this.brand = options.brand || 'lecoqgolf';
        this.brandConfig = BRAND_CONFIG[this.brand];
        this.limit = options.limit || 0; // 0 = no limit
        this.concurrent = options.concurrent || 1;
        this.delay = options.delay || 1000; // 请求间隔（默认1秒）

        this.scraper = new UnifiedDetailScraper({
            headless: true,
            debug: false,
            timeout: 60000
        });

        this.results = [];
        this.errors = [];
    }

    /**
     * 从输入文件读取商品列表
     */
    loadProducts(inputPath) {
        const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

        let products = [];

        // 支持多种输入格式
        if (Array.isArray(data)) {
            // 直接是数组
            products = data;
        } else if (data.products) {
            // { products: [...] } 或 { products: { id: {...} } }
            if (Array.isArray(data.products)) {
                products = data.products;
            } else {
                // 对象格式转数组
                products = Object.entries(data.products).map(([id, product]) => ({
                    productId: id,
                    url: product.url || product.detailUrl,
                    ...product
                }));
            }
        } else if (data.records) {
            // 飞书导出格式
            products = data.records;
        }

        // 标准化产品数据
        products = products.map(p => ({
            productId: p.productId || p.product_id || p.id || '',
            url: p.url || p.detailUrl || p.detail_url || p.商品链接 || '',
            stockStatusText: p.stockStatusText || p.库存状态 || ''
        })).filter(p => p.url);

        // 应用限制
        if (this.limit > 0 && products.length > this.limit) {
            products = products.slice(0, this.limit);
        }

        return products;
    }

    /**
     * 抓取单个商品的库存
     */
    async checkSingleProduct(product) {
        const { productId, url } = product;

        console.log(`\n🔍 检查库存: ${productId || url}`);

        try {
            // 复用 UnifiedDetailScraper 的完整抓取流程
            const result = await this.scraper.scrapeDetailPage(url, { productId });

            if (result.success) {
                // 只提取库存相关字段
                const inventoryData = {
                    productId: result.productId || productId,
                    detailUrl: url,
                    variantInventory: result.variantInventory || [],
                    stockStatus: this.calculateStockStatus(result.variantInventory),
                    colors: result.colors || [],
                    sizes: result.sizes || [],
                    timestamp: new Date().toISOString()
                };

                // 统计
                const totalVariants = inventoryData.variantInventory.length;
                const inStockCount = inventoryData.variantInventory.filter(v => v.inStock).length;
                console.log(`  ✅ ${totalVariants} 个变体, ${inStockCount} 个有货`);

                return inventoryData;
            } else {
                console.log(`  ❌ 抓取失败: ${result.error}`);
                return {
                    productId: productId,
                    detailUrl: url,
                    error: result.error,
                    timestamp: new Date().toISOString()
                };
            }
        } catch (error) {
            console.log(`  ❌ 错误: ${error.message}`);
            return {
                productId: productId,
                detailUrl: url,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 计算库存状态
     */
    calculateStockStatus(variantInventory) {
        if (!variantInventory || variantInventory.length === 0) {
            return 'unknown';
        }

        const hasStock = variantInventory.some(v => v.inStock);
        const allInStock = variantInventory.every(v => v.inStock);

        if (!hasStock) {
            return 'out_of_stock';
        } else if (allInStock) {
            return 'in_stock';
        } else {
            return 'partial_stock';
        }
    }

    /**
     * 批量检查库存
     */
    async checkInventory(inputPath, outputPath) {
        console.log('📦 开始库存巡检...');
        console.log(`📄 输入文件: ${inputPath}`);
        console.log(`📁 输出文件: ${outputPath}`);
        console.log(`⚡ 并发数: ${this.concurrent}, 延迟: ${this.delay}ms`);

        // 加载商品
        const products = this.loadProducts(inputPath);
        console.log(`\n📊 共 ${products.length} 个商品待检查`);

        if (products.length === 0) {
            console.log('⚠️ 没有找到需要检查的商品');
            return;
        }

        const results = [];
        const errors = [];
        const skipped = [];

        // 先过滤掉需要跳过的商品
        const toProcess = [];
        for (const product of products) {
            if (product.stockStatusText === '都缺货') {
                console.log(`⏭️ SKIP: ${product.productId} 已标记都缺货，跳过巡检`);
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

        console.log(`\n📋 实际需要检查: ${toProcess.length} 个商品`);

        // 并发处理
        let processed = 0;
        for (let i = 0; i < toProcess.length; i += this.concurrent) {
            const batch = toProcess.slice(i, i + this.concurrent);
            const batchNum = Math.floor(i / this.concurrent) + 1;
            const totalBatches = Math.ceil(toProcess.length / this.concurrent);

            console.log(`\n[批次 ${batchNum}/${totalBatches}] 处理 ${batch.length} 个商品...`);

            // 并发执行这一批
            const batchResults = await Promise.all(
                batch.map(async (product, idx) => {
                    const globalIdx = i + idx + 1;
                    console.log(`  [${globalIdx}/${toProcess.length}] 检查: ${product.productId}`);
                    return this.checkSingleProduct(product);
                })
            );

            // 收集结果
            for (const result of batchResults) {
                if (result.error) {
                    errors.push(result);
                } else {
                    results.push(result);
                }
            }

            processed += batch.length;

            // 批次间延迟
            if (i + this.concurrent < toProcess.length) {
                await new Promise(resolve => setTimeout(resolve, this.delay));
            }
        }

        // 生成输出
        const output = {
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
            errors: errors,
            skipped: skipped
        };

        // 保存结果
        fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf8');

        console.log('\n' + '='.repeat(50));
        console.log('📊 巡检完成汇总:');
        console.log(`  总计: ${output.summary.total}`);
        console.log(`  成功: ${output.summary.success}`);
        console.log(`  失败: ${output.summary.failed}`);
        console.log(`  跳过(都缺货): ${output.summary.skipped}`);
        console.log(`  全部有货: ${output.summary.inStock}`);
        console.log(`  部分缺货: ${output.summary.partialStock}`);
        console.log(`  全部缺货: ${output.summary.outOfStock}`);
        console.log('='.repeat(50));
        console.log(`\n💾 结果已保存: ${outputPath}`);

        return output;
    }
}

// CLI 入口
async function main() {
    const args = process.argv.slice(2);

    // 解析参数
    const options = {
        input: null,
        output: null,
        limit: 0,
        concurrent: 3,  // 默认并发3（优化后）
        delay: 500,     // 默认延迟500ms（优化后）
        brand: 'lecoqgolf'
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
            case '-c':
                options.concurrent = parseInt(args[++i]) || 1;
                break;
            case '--delay':
            case '-d':
                options.delay = parseInt(args[++i]) || 2000;
                break;
            case '--brand':
            case '-b':
                options.brand = args[++i];
                break;
            case '--help':
            case '-h':
                console.log(`
库存巡检脚本 - Le Coq Golf

使用方式:
  node check_inventory.js --input <file> --output <file> [options]

参数:
  --input, -i     输入文件路径（必需）
  --output, -o    输出文件路径（必需）
  --limit, -l     限制检查数量（默认: 全部）
  --concurrent    并发数（默认: 2）
  --delay, -d     请求间隔毫秒（默认: 1000）
  --brand, -b     品牌（默认: lecoqgolf）
  --help, -h      显示帮助

示例:
  node check_inventory.js --input products.json --output inventory.json
  node check_inventory.js --input products.json --output inventory.json --concurrent 3
  node check_inventory.js --input products.json --output inventory.json --delay 500
`);
                process.exit(0);
        }
    }

    // 验证参数
    if (!options.input || !options.output) {
        console.error('❌ 错误: 必须指定 --input 和 --output 参数');
        console.error('使用 --help 查看帮助');
        process.exit(1);
    }

    if (!fs.existsSync(options.input)) {
        console.error(`❌ 错误: 输入文件不存在: ${options.input}`);
        process.exit(1);
    }

    // 执行巡检
    const checker = new InventoryChecker(options);

    try {
        await checker.checkInventory(options.input, options.output);
    } catch (error) {
        console.error(`❌ 巡检失败: ${error.message}`);
        process.exit(1);
    }
}

// 导出供其他模块使用
module.exports = { InventoryChecker, BRAND_CONFIG };

// 直接运行
if (require.main === module) {
    main().catch(console.error);
}
