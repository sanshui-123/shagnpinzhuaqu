#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 详情页批量处理器
 * 纯后台运行，批量处理330个商品
 */

const fs = require('fs');
const path = require('path');
const EnhancedDetailScraper = require('./enhanced_detail_scraper');

class BatchDetailProcessor {
    constructor() {
        this.scraper = new EnhancedDetailScraper();
        this.inputFile = './golf_content/lecoqgolf/lecoqgolf_products_2025-11-12T16-18-23-072Z.json';
        this.outputDir = './golf_content/lecoqgolf/';
        this.results = [];
        this.processedCount = 0;
        this.totalProducts = 0;
        this.errors = [];
    }

    async processAllProducts() {
        console.log('🚀 开始批量处理Le Coq Sportif Golf详情页...');
        console.log('🌐 运行模式：纯后台模式（无界面）');

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

            // 2. 批量处理
            console.log('\n🔄 开始批量处理详情页...\n');

            // 处理全部商品
            console.log(`🚀 正式模式：处理全部 ${products.length} 个商品`);

            for (let i = 0; i < products.length; i++) {
                const product = products[i];
                await this.processProduct(product, i + 1, products.length);
            }

            // 3. 保存结果
            await this.saveResults();

            console.log('\n✅ 批量处理完成！');
            this.printSummary();

        } catch (error) {
            console.error('❌ 批量处理失败:', error.message);
            this.errors.push({ type: 'batch_error', message: error.message });
            await this.saveResults();
        }
    }

    async loadProductList() {
        if (!fs.existsSync(this.inputFile)) {
            console.log('📁 寻找最新的商品列表文件...');
            const files = fs.readdirSync(this.outputDir)
                .filter(file => file.startsWith('lecoqgolf_products_') && file.endsWith('.json'))
                .sort()
                .reverse();

            if (files.length > 0) {
                this.inputFile = path.join(this.outputDir, files[0]);
                console.log(`📁 使用文件: ${this.inputFile}`);
            } else {
                throw new Error('未找到商品列表文件');
            }
        }

        const content = fs.readFileSync(this.inputFile, 'utf8');
        return JSON.parse(content);
    }

    extractProductUrls(productData) {
        const products = [];

        if (productData.results && productData.results.length > 0) {
            productData.results.forEach(collection => {
                if (collection.products && collection.products.length > 0) {
                    collection.products.forEach(product => {
                        if (product.url && product.url.startsWith('http')) {
                            products.push({
                                id: product.id,
                                url: product.url,
                                title: product.title,
                                collection: collection.collection
                            });
                        }
                    });
                }
            });
        }

        return products;
    }

    async processProduct(product, index, total) {
        try {
            console.log(`[${index}/${total}] 📊 处理商品: ${product.title.substring(0, 50)}...`);

            // 抓取详情页数据
            const detailData = await this.scraper.scrapeDetailPage(product.url);

            // 转换为飞书格式
            const feishuData = this.convertToFeishuFormat(detailData, product);

            // 添加到结果列表
            this.results.push(feishuData);
            this.processedCount++;

            console.log(`✅ [${index}/${total}] 成功处理 - 商品编号: ${detailData.productCode}`);

            // 添加延迟避免过于频繁的请求
            if (index < total) {
                await this.delay(2000); // 2秒延迟
            }

        } catch (error) {
            console.log(`❌ [${index}/${total}] 处理失败: ${error.message}`);
            this.errors.push({
                product: product,
                error: error.message,
                index: index
            });

            // 即使失败也要继续处理下一个
            if (index < total) {
                await this.delay(3000); // 错误后延长延迟
            }
        }
    }

    convertToFeishuFormat(detailData, product) {
        const feishuRecord = {
            // 基础信息
            '商品标题': detailData.title.translated || detailData.title.original || '',
            '品牌': detailData.brand,
            '商品编号': detailData.productCode,
            '性别': detailData.gender,
            '价格': detailData.price,
            '详情页链接': detailData.url,

            // 分类信息
            '一级分类': detailData.categories[0] || '',
            '二级分类': detailData.categories[1] || '',
            '三级分类': detailData.categories[2] || '',
            '四级分类': detailData.categories[3] || '',
            '五级分类': detailData.categories[4] || '',

            // 产品规格
            '颜色选项': detailData.colors.map(c => c.name).join(', ') || '',
            '颜色数量': detailData.colors.length,
            '首个颜色': detailData.colors.find(c => c.isFirstColor)?.name || '',
            '尺寸选项': detailData.sizes.map(s => s.size).join(', ') || '',
            '尺寸数量': detailData.sizes.length,

            // 库存信息
            '总尺码数': detailData.inventoryStats.totalSizes || 0,
            '有库存尺码': detailData.inventoryStats.availableSizes || 0,
            '缺货尺码': detailData.inventoryStats.soldOutSizes || 0,
            '库存率(%)': detailData.inventoryStats.stockPercentage || 0,

            // 图片信息
            '图片总数': detailData.images.total || 0,
            '首个颜色图片数': detailData.images.firstColorImages.length || 0,
            '其他颜色图片数': detailData.images.otherColorsImages.length || 0,
            '主要图片链接': detailData.images.firstColorImages[0] || '',
            '所有图片链接': detailData.images.urls.slice(0, 10).join('\n') + (detailData.images.urls.length > 10 ? `\n... 还有 ${detailData.images.urls.length - 10} 张` : ''),

            // 功能特性（安全访问）
            '核心功能': ((detailData.description && detailData.description.features) ? detailData.description.features : []).slice(0, 3).join(', ') || '',
            '材质信息': ((detailData.description && detailData.description.materials) ? detailData.description.materials : []).join(', ') || '',
            '所有功能': ((detailData.description && detailData.description.features) ? detailData.description.features : []).slice(0, 5).join('\n') || '',

            // 翻译内容
            '详情页译文': detailData.detailDescription.translated || '',
            '尺码表译文': detailData.sizeChart.translatedText || '',

            // 原始内容
            '标题原文': detailData.title.original || '',
            '详情页原文': detailData.detailDescription.original || '',
            '尺码表原文': detailData.sizeChart.text || '',

            // 时间戳
            '抓取时间': detailData.scrapedAt || new Date().toISOString(),
            '更新时间': new Date().toISOString(),

            // 系统信息
            '数据来源': 'lecoqgolf',
            '状态': '待同步',
            '处理状态': 'success'
        };

        return feishuRecord;
    }

    async saveResults() {
        // 确保输出目录存在
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

        // 保存飞书格式数据
        const feishuFile = `${this.outputDir}batch_feishu_results_${timestamp}.json`;
        const outputData = {
            records: this.results,
            total: this.results.length,
            processed: this.processedCount,
            failed: this.errors.length,
            errors: this.errors,
            timestamp: new Date().toISOString(),
            brand: 'lecoqgolf',
            batchMode: true
        };

        fs.writeFileSync(feishuFile, JSON.stringify(outputData, null, 2));
        console.log(`💾 飞书格式数据已保存: ${feishuFile}`);

        // 保存处理报告
        const reportFile = `${this.outputDir}batch_processing_report_${timestamp}.txt`;
        const report = this.generateReport();
        fs.writeFileSync(reportFile, report);
        console.log(`📄 处理报告已保存: ${reportFile}`);

        return { feishuFile, reportFile };
    }

    generateReport() {
        const report = [
            `=== Le Coq Sportif Golf 批量详情页处理报告 ===`,
            ``,
            `处理时间: ${new Date().toISOString()}`,
            `运行模式: 纯后台模式`,
            ``,
            `📊 处理统计:`,
            `- 总商品数: ${this.totalProducts}`,
            `- 成功处理: ${this.processedCount}`,
            `- 处理失败: ${this.errors.length}`,
            `- 成功率: ${Math.round((this.processedCount / this.totalProducts) * 100)}%`,
            ``,
            `📋 数据质量统计:`,
            `- 平均图片数: ${this.calculateAverageImages()}`,
            `- 平均颜色数: ${this.calculateAverageColors()}`,
            `- 平均尺码数: ${this.calculateAverageSizes()}`,
            ``,
            `❌ 错误记录:`,
            ...this.errors.map((err, i) => [
                `${i + 1}. 商品ID: ${err.product.id}`,
                `   URL: ${err.product.url}`,
                `   错误: ${err.error}`
            ]).flat()
        ].join('\n');

        return report;
    }

    calculateAverageImages() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['图片总数'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    calculateAverageColors() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['颜色数量'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    calculateAverageSizes() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, r) => sum + parseInt(r['尺寸数量'] || 0), 0);
        return Math.round(total / this.results.length);
    }

    printSummary() {
        console.log('\n📊 处理总结:');
        console.log(`✅ 成功处理: ${this.processedCount} 个商品`);
        console.log(`❌ 处理失败: ${this.errors.length} 个商品`);
        console.log(`📈 成功率: ${Math.round((this.processedCount / this.totalProducts) * 100)}%`);
        console.log(`🖼️ 平均图片: ${this.calculateAverageImages()} 张/商品`);
        console.log(`🎨 平均颜色: ${this.calculateAverageColors()} 个/商品`);
        console.log(`📏 平均尺码: ${this.calculateAverageSizes()} 个/商品`);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 运行批量处理
if (require.main === module) {
    const processor = new BatchDetailProcessor();

    processor.processAllProducts()
        .then(() => {
            console.log('\n🎉 批量处理完成！');
            console.log('📁 检查输出目录以获取飞书格式数据');
        })
        .catch(error => {
            console.error('❌ 批量处理失败:', error);
            process.exit(1);
        });
}

module.exports = BatchDetailProcessor;