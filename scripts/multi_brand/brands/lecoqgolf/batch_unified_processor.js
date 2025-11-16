#!/usr/bin/env node

/**
 * 批量统一处理器 - 使用统一抓取器
 * 集成高级尺码表抓取功能，批量处理所有商品
 */

const fs = require('fs');
const path = require('path');
const UnifiedDetailScraper = require('./unified_detail_scraper');

class BatchUnifiedProcessor {
    constructor(options = {}) {
        // 🎯 使用统一抓取器 - 后台模式，适合批量处理
        this.scraper = new UnifiedDetailScraper({
            headless: true, // 批量处理使用后台模式
            debug: false,   // 批量处理关闭调试输出
            timeout: 45000,
            ...options
        });

        this.inputFile = './golf_content/lecoqgolf/lecoqgolf_products_2025-11-12T16-18-23-072Z.json';
        this.outputDir = './golf_content/lecoqgolf/';
        this.results = {};
        this.processedCount = 0;
        this.totalProducts = 0;
        this.errors = [];

        // 状态管理
        this.statusFile = './batch_unified_status.json';
        this.loadStatus();
    }

    // 状态管理方法
    loadStatus() {
        try {
            if (fs.existsSync(this.statusFile)) {
                const statusData = JSON.parse(fs.readFileSync(this.statusFile, 'utf8'));
                this.processedUrls = new Set(statusData.processedUrls || []);
                this.failedUrls = new Map(statusData.failedUrls || []);
                console.log(`📊 加载状态: 已处理 ${this.processedUrls.size} 个URL，失败 ${this.failedUrls.size} 个`);
            } else {
                this.processedUrls = new Set();
                this.failedUrls = new Map();
            }
        } catch (error) {
            console.log('⚠️ 状态文件加载失败，使用全新状态');
            this.processedUrls = new Set();
            this.failedUrls = new Map();
        }
    }

    saveStatus() {
        try {
            const statusData = {
                processedUrls: Array.from(this.processedUrls),
                failedUrls: Array.from(this.failedUrls.entries()),
                lastUpdate: new Date().toISOString(),
                processedCount: this.processedCount,
                totalCount: this.totalProducts
            };
            fs.writeFileSync(this.statusFile, JSON.stringify(statusData, null, 2));
        } catch (error) {
            console.warn('⚠️ 状态文件保存失败:', error.message);
        }
    }

    isUrlProcessed(url) {
        return this.processedUrls.has(url);
    }

    markUrlProcessed(url) {
        this.processedUrls.add(url);
        this.failedUrls.delete(url);
        this.saveStatus();
    }

    markUrlFailed(url, error) {
        const failCount = this.failedUrls.get(url) || 0;
        this.failedUrls.set(url, failCount + 1);
        this.saveStatus();
    }

    async processAllProducts() {
        console.log('🚀 开始批量统一处理Le Coq Sportif Golf详情页...');
        console.log('🌐 运行模式：纯后台模式（无界面，使用统一抓取器）');

        try {
            // 1. 读取商品列表
            const productData = await this.loadProductList();
            const products = this.extractProductUrls(productData);

            console.log(`📋 从文件加载 ${products.length} 个商品`);
            this.totalProducts = products.length;

            if (products.length === 0) {
                console.log('❌ 未找到商品URL');
                return;
            }

            // 过滤已处理的URL
            const unprocessedProducts = products.filter(product => {
                if (!product.url) {
                    console.log('⚠️ 商品缺少URL:', product.productId || product.name);
                    return false;
                }
                return !this.isUrlProcessed(product.url);
            });

            console.log(`🔄 过滤后需要处理 ${unprocessedProducts.length} 个商品`);

            if (unprocessedProducts.length === 0) {
                console.log('✅ 所有商品都已处理完成');
                return;
            }

            // 2. 批量处理
            console.log('\n🔄 开始批量处理详情页...\n');

            for (let i = 0; i < unprocessedProducts.length; i++) {
                const product = unprocessedProducts[i];
                const progress = Math.round(((i + 1) / unprocessedProducts.length) * 100);

                console.log(`\n📦 [${progress}%] 处理商品 ${i + 1}/${unprocessedProducts.length}`);
                console.log(`🆔 商品ID: ${product.productId}`);
                console.log(`🔗 URL: ${product.url}`);

                try {
                    // 🎯 使用统一抓取器处理单个商品
                    const result = await this.scraper.scrapeDetailPage(product.url, {
                        productId: product.productId,
                        name: product.name
                    });

                    if (result.success) {
                        // 转换为标准格式
                        const productData = this.convertToProductFormat(result);

                        this.results[result.productId || product.productId] = productData;
                        this.processedCount++;

                        this.markUrlProcessed(product.url);

                        console.log(`✅ 处理成功: ${result.productName}`);
                        console.log(`🎨 颜色: ${(result.colors || []).length}种`);
                        console.log(`📏 尺码: ${(result.sizes || []).length}个`);
                        console.log(`🖼️ 图片: ${(result.imageUrls || []).length}张`);

                        if (result.sizeChart && result.sizeChart.success) {
                            console.log(`📋 尺码表: ✅ (${result.sizeChart.method})`);
                        } else {
                            console.log(`📋 尺码表: ❌`);
                        }
                    } else {
                        console.log(`❌ 处理失败: ${result.error}`);
                        this.markUrlFailed(product.url, result.error);
                    }

                } catch (error) {
                    console.log(`❌ 处理异常: ${error.message}`);
                    this.markUrlFailed(product.url, error.message);
                }

                // 每5个商品保存一次中间结果
                if ((i + 1) % 5 === 0) {
                    await this.saveIntermediateResults();
                    console.log(`💾 已保存中间结果 (处理了 ${i + 1} 个商品)`);
                }

                // 简短的延迟，避免过于频繁请求
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // 3. 保存最终结果
            await this.saveFinalResults();

            console.log('\n🎉 批量处理完成!');
            console.log(`📊 处理统计: 成功 ${this.processedCount}/${this.totalProducts} 个商品`);
            console.log(`❌ 失败: ${this.failedUrls.size} 个商品`);

        } catch (error) {
            console.error('❌ 批量处理过程出错:', error);
        }
    }

    async loadProductList() {
        try {
            const rawData = fs.readFileSync(this.inputFile, 'utf8');
            return JSON.parse(rawData);
        } catch (error) {
            console.error('❌ 读取商品列表失败:', error);
            throw error;
        }
    }

    extractProductUrls(productData) {
        const products = [];

        // 支持多种数据格式
        if (productData.products && typeof productData.products === 'object') {
            // 对象格式: { "product_id": { ... } }
            Object.entries(productData.products).forEach(([productId, info]) => {
                products.push({
                    productId: productId,
                    url: info.url || info.detailUrl,
                    name: info.name || info.productName
                });
            });
        } else if (Array.isArray(productData)) {
            // 数组格式: [ { ... } ]
            productData.forEach(item => {
                products.push({
                    productId: item.id || item.productId,
                    url: item.url || item.detailUrl,
                    name: item.name || item.productName
                });
            });
        }

        return products.filter(product => product.url);
    }

    convertToProductFormat(result) {
        return {
            productId: result.productId,
            productName: result.productName,
            detailUrl: result.url,
            price: result.price,
            brand: result.brand,
            gender: result.gender,
            colors: result.colors || [],
            sizes: result.sizes || [],
            imageUrls: result.imageUrls || [],
            description: result.description,
            sizeChart: result.sizeChart && result.sizeChart.success ? {
                html: result.sizeChart.html || '',
                text: result.sizeChart.text || ''
            } : {},
            category: "",
            sku: "",
            status: "",
            priceText: result.price,
            mainImage: (result.imageUrls && result.imageUrls.length > 0) ? result.imageUrls[0] : "",
            originalPrice: "",
            currentPrice: "",
            _original_data: {
                商品链接: result.url,
                商品ID: result.productId,
                商品标题: result.productName,
                品牌名: result.brand,
                价格: result.price,
                性别: result.gender,
                颜色: result.colors || [],
                图片链接: result.imageUrls || [],
                尺码: result.sizes || [],
                详情页文字: result.description,
                尺码表: result.sizeChart,
                _scraper_info: result._scraper_info
            }
        };
    }

    async saveIntermediateResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const tempFile = path.join(this.outputDir, `temp_batch_unified_${timestamp}.json`);

        const outputData = {
            products: this.results,
            timestamp: new Date().toISOString(),
            processed_count: this.processedCount,
            total_count: this.totalProducts,
            status: 'intermediate'
        };

        fs.writeFileSync(tempFile, JSON.stringify(outputData, null, 2), 'utf8');
    }

    async saveFinalResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const finalFile = path.join(this.outputDir, `batch_unified_final_${timestamp}.json`);

        const outputData = {
            products: this.results,
            timestamp: new Date().toISOString(),
            processed_count: this.processedCount,
            total_count: this.totalProducts,
            failed_urls: Array.from(this.failedUrls.entries()),
            status: 'completed',
            scraper_info: {
                version: 'unified_v1.0',
                processing_mode: 'batch_headless',
                advanced_size_chart: true
            }
        };

        fs.writeFileSync(finalFile, JSON.stringify(outputData, null, 2), 'utf8');
        console.log(`💾 最终结果已保存: ${finalFile}`);
    }
}

// 主函数
async function main() {
    const processor = new BatchUnifiedProcessor();
    await processor.processAllProducts();
    process.exit(0);
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = BatchUnifiedProcessor;