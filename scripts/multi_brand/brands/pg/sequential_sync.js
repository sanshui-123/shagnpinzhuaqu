#!/usr/bin/env node

/**
 * 顺序同步处理器 - Stage 2 Orchestrator
 * 实现"抓一个→同步一个"的流式处理流程
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SequentialSyncProcessor {
    constructor(options = {}) {
        // 将源文件路径转换为绝对路径
        this.sourceFile = path.isAbsolute(options.sourceFile)
            ? options.sourceFile
            : path.resolve(process.cwd(), options.sourceFile);
        this.brand = options.brand || 'PEARLY GATES';
        this.limit = options.limit || null;
        this.statusFile = './sequential_sync_status.json';
        this.tempDir = '/tmp';
        this.processedIds = new Set();
        this.failedIds = new Map();

        this.loadStatus();
    }

    loadStatus() {
        try {
            if (fs.existsSync(this.statusFile)) {
                const status = JSON.parse(fs.readFileSync(this.statusFile, 'utf8'));
                this.processedIds = new Set(status.processedIds || []);
                this.failedIds = new Map(status.failedIds || []);
                console.log(`📊 加载状态: 已处理 ${this.processedIds.size} 个，失败 ${this.failedIds.size} 个`);
            }
        } catch (error) {
            console.log('⚠️ 状态文件加载失败，使用全新状态');
        }
    }

    saveStatus() {
        try {
            const status = {
                processedIds: Array.from(this.processedIds),
                failedIds: Array.from(this.failedIds.entries()),
                lastUpdate: new Date().toISOString()
            };
            fs.writeFileSync(this.statusFile, JSON.stringify(status, null, 2));
        } catch (error) {
            console.warn('⚠️ 状态保存失败:', error.message);
        }
    }

    async execute() {
        console.log('🚀 开始顺序同步处理...');
        console.log(`📁 源文件: ${this.sourceFile}`);
        console.log(`🏷️ 品牌: ${this.brand}`);

        // 1. 读取源文件，构建 productId -> {url, name} 映射
        console.log('\n📋 步骤1: 读取源文件...');
        const productMap = this.loadProductMap();
        console.log(`✅ 加载了 ${productMap.size} 个产品`);

        // 2. 调用 Python 工具获取待处理的 product_id 列表
        console.log('\n🔍 步骤2: 查询飞书待处理产品...');
        const pendingIds = this.getPendingProducts();
        console.log(`✅ 待处理: ${pendingIds.length} 个产品`);

        if (pendingIds.length === 0) {
            console.log('🎉 所有产品都已处理完成！');
            return;
        }

        // 应用限制
        const toProcess = this.limit ? pendingIds.slice(0, this.limit) : pendingIds;
        console.log(`\n🔄 步骤3: 开始处理 ${toProcess.length} 个产品...\n`);

        // 3. 逐个处理
        let successCount = 0;
        let errorCount = 0;

        for (let i = 0; i < toProcess.length; i++) {
            const productId = toProcess[i];
            const progress = Math.round(((i + 1) / toProcess.length) * 100);

            console.log(`\n[${progress}%] 处理商品 ${i + 1}/${toProcess.length}`);
            console.log(`🆔 产品ID: ${productId}`);

            // 检查是否已处理
            if (this.processedIds.has(productId)) {
                console.log('⏭️ 已处理，跳过');
                continue;
            }

            // 获取产品信息
            const product = productMap.get(productId);
            if (!product) {
                console.log('⚠️ 未找到产品信息，跳过');
                this.failedIds.set(productId, 'Product not found in source file');
                this.saveStatus();
                continue;
            }

            console.log(`🔗 URL: ${product.url}`);

            try {
                // 3.1 抓取详情
                const tempFile = path.join(this.tempDir, `pending_${productId}.json`);
                console.log('📥 抓取详情...');

                const scrapeCmd = `cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf && node single_unified_processor.js "${product.url}" "${productId}" --output "${tempFile}"`;
                execSync(scrapeCmd, { encoding: 'utf8', stdio: 'inherit' });

                console.log('✅ 抓取成功');

                // 3.2 同步到飞书
                console.log('📤 同步到飞书...');

                const syncCmd = `cd /Users/sanshui/Desktop/CallawayJP && python3 -m tongyong_feishu_update.run_pipeline "${tempFile}" --verbose`;
                execSync(syncCmd, { encoding: 'utf8', stdio: 'inherit' });

                console.log('✅ 同步成功');

                // 清理临时文件
                if (fs.existsSync(tempFile)) {
                    fs.unlinkSync(tempFile);
                }

                // 标记为已处理
                this.processedIds.add(productId);
                this.failedIds.delete(productId);
                successCount++;
                this.saveStatus();

            } catch (error) {
                console.log(`❌ 处理失败: ${error.message}`);
                this.failedIds.set(productId, error.message);
                errorCount++;
                this.saveStatus();
            }

            // 短暂延迟
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        // 4. 输出汇总
        console.log('\n\n🎉 顺序同步处理完成!');
        console.log('=' .repeat(60));
        console.log(`📊 处理统计:`);
        console.log(`  ✅ 成功: ${successCount}`);
        console.log(`  ❌ 失败: ${errorCount}`);
        console.log(`  📦 总计: ${toProcess.length}`);
        console.log('=' .repeat(60));

        if (this.failedIds.size > 0) {
            console.log(`\n❌ 失败产品ID:`);
            for (const [id, error] of this.failedIds.entries()) {
                console.log(`  - ${id}: ${error}`);
            }
        }
    }

    loadProductMap() {
        const data = JSON.parse(fs.readFileSync(this.sourceFile, 'utf8'));
        const productMap = new Map();

        if (data.results && Array.isArray(data.results)) {
            // scrape_category.js 格式
            for (const result of data.results) {
                if (result.products && Array.isArray(result.products)) {
                    for (const item of result.products) {
                        const productId = item.productId;
                        if (productId) {
                            productMap.set(productId, {
                                url: item.url,
                                name: item.title || item.name
                            });
                        }
                    }
                }
            }
        }

        return productMap;
    }

    getPendingProducts() {
        try {
            const cmd = `cd /Users/sanshui/Desktop/CallawayJP && python3 -m tongyong_feishu_update.tools.export_pending_products --field "商品标题" --brand "${this.brand}" --source "${this.sourceFile}" --stdout`;
            const stdout = execSync(cmd, { encoding: 'utf8' });
            return JSON.parse(stdout || '[]');
        } catch (error) {
            console.error('❌ 获取待处理产品失败:', error.message);
            throw error;
        }
    }
}

// CLI
async function main() {
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
        console.log('用法: node sequential_sync.js --source <file> [选项]');
        console.log('');
        console.log('选项:');
        console.log('  --source <path>   源文件路径（必需）');
        console.log('  --brand <name>    品牌名称（默认：PEARLY GATES）');
        console.log('  --limit <n>       限制处理数量');
        console.log('  --help, -h        显示帮助');
        console.log('');
        console.log('示例:');
        console.log('  node sequential_sync.js --source "golf_content/pg/pg_products_xxx.json"');
        console.log('  node sequential_sync.js --source "..." --limit 10');
        process.exit(0);
    }

    const options = {};
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--source':
                options.sourceFile = args[++i];
                break;
            case '--brand':
                options.brand = args[++i];
                break;
            case '--limit':
                options.limit = parseInt(args[++i]);
                break;
        }
    }

    if (!options.sourceFile) {
        console.error('❌ 缺少必需参数: --source');
        process.exit(1);
    }

    const processor = new SequentialSyncProcessor(options);
    await processor.execute();
}

main().catch(error => {
    console.error('❌ 执行出错:', error);
    process.exit(1);
});
