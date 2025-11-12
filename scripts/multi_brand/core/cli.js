#!/usr/bin/env node

/**
 * 多品牌数据抓取系统 - 统一CLI入口
 * 零影响设计：完全独立于现有卡拉威系统
 */

const path = require('path');
const fs = require('fs');

// 使用yargs替代commander
const yargs = require('yargs');
const { hideBin } = require('yargs/helpers');

// 导入核心模块
const ConfigManager = require('./config_manager');
const ScraperEngine = require('./scraper_engine');
const HealthMonitor = require('../monitoring/health_monitor');

class MultiBrandCLI {
    constructor() {
        this.configManager = new ConfigManager();
        this.scraperEngine = new ScraperEngine();
        this.healthMonitor = new HealthMonitor();
        this.baseDir = path.join(__dirname, '..', '..');
    }

    /**
     * 运行所有品牌
     */
    async runAllBrands() {
        console.log('🚀 开始运行所有品牌数据抓取...');

        try {
            const brands = await this.configManager.getAllBrands();
            const results = [];

            // 按组分批运行，避免并发冲突
            const groups = this.groupBrandsForScheduling(brands);

            for (let i = 0; i < groups.length; i++) {
                const group = groups[i];
                console.log(`\n📅 执行第 ${i + 1}/${groups.length} 组品牌: ${group.join(', ')}`);

                const groupResults = await Promise.allSettled(
                    group.map(brand => this.runSingleBrand(brand))
                );

                results.push(...groupResults.map(r => r.status === 'fulfilled' ? r.value : { error: r.reason }));

                // 组间休息时间
                if (i < groups.length - 1) {
                    console.log('⏱️ 组间休息 2 分钟...');
                    await this.sleep(120000); // 2分钟
                }
            }

            this.displayResults(results);
        } catch (error) {
            console.error('❌ 运行所有品牌失败:', error.message);
            process.exit(1);
        }
    }

    /**
     * 运行单个品牌
     */
    async runSingleBrand(brandName) {
        console.log(`\n🔄 开始运行品牌: ${brandName}`);

        try {
            // 检查品牌配置
            const config = await this.configManager.getBrandConfig(brandName);
            if (!config) {
                throw new Error(`品牌 ${brandName} 配置不存在`);
            }

            // 运行抓取引擎
            const result = await this.scraperEngine.runBrand(brandName, config);

            console.log(`✅ 品牌 ${brandName} 完成: ${result.articlesCount} 篇文章`);

            return {
                brand: brandName,
                success: true,
                articlesCount: result.articlesCount,
                duration: result.duration,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error(`❌ 品牌 ${brandName} 失败:`, error.message);

            return {
                brand: brandName,
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 显示运行状态
     */
    async showStatus() {
        console.log('📊 多品牌系统状态概览\n');

        try {
            const brands = await this.configManager.getAllBrands();
            const healthStatus = await this.healthMonitor.getOverallHealth();

            console.log('🏷️  支持的品牌:');
            brands.forEach(brand => {
                const config = this.configManager.getBrandConfigSync(brand);
                console.log(`  ✅ ${brand} - ${config ? config.name : '配置缺失'}`);
            });

            console.log('\n💊 系统健康状态:');
            console.log(`  整体健康度: ${healthStatus.overall}%`);
            console.log(`  活跃品牌数: ${healthStatus.activeBrands}/${brands.length}`);
            console.log(`  最后更新: ${healthStatus.lastUpdate}`);

            // 显示最近运行记录
            const recentRuns = await this.healthMonitor.getRecentRuns(5);
            if (recentRuns.length > 0) {
                console.log('\n📈 最近运行记录:');
                recentRuns.forEach(run => {
                    const status = run.success ? '✅' : '❌';
                    console.log(`  ${status} ${run.brand} - ${run.articlesCount} 篇 - ${new Date(run.timestamp).toLocaleString()}`);
                });
            }

        } catch (error) {
            console.error('❌ 获取状态失败:', error.message);
        }
    }

    /**
     * 系统健康检查
     */
    async performHealthCheck() {
        console.log('🔍 执行系统健康检查...\n');

        try {
            const healthCheck = await this.healthMonitor.performFullCheck();

            console.log('📋 检查结果:');
            Object.entries(healthCheck.results).forEach(([component, status]) => {
                const icon = status.healthy ? '✅' : '❌';
                console.log(`  ${icon} ${component}: ${status.message}`);
            });

            console.log(`\n🏥 总体健康度: ${healthCheck.overall}%`);

            if (healthCheck.overall < 80) {
                console.log('⚠️  警告: 系统健康度较低，建议检查配置和依赖');
            }

            // 生成健康报告
            const reportPath = path.join(this.baseDir, 'health_report.json');
            fs.writeFileSync(reportPath, JSON.stringify(healthCheck, null, 2));
            console.log(`📄 详细报告已保存: ${reportPath}`);

        } catch (error) {
            console.error('❌ 健康检查失败:', error.message);
        }
    }

    /**
     * 初始化新品牌
     */
    async initializeBrand(brandName) {
        console.log(`🏗️  初始化品牌: ${brandName}`);

        try {
            await this.configManager.createBrandTemplate(brandName);
            console.log(`✅ 品牌 ${brandName} 初始化完成`);
            console.log(`📝 请编辑配置文件: scripts/multi_brand/brands/${brandName}/config.json`);
        } catch (error) {
            console.error('❌ 初始化失败:', error.message);
        }
    }

    /**
     * 分组品牌避免时间冲突
     */
    groupBrandsForScheduling(brands) {
        // 按字母顺序分组，每组最多3个品牌
        const sortedBrands = brands.sort();
        const groups = [];

        for (let i = 0; i < sortedBrands.length; i += 3) {
            groups.push(sortedBrands.slice(i, i + 3));
        }

        return groups;
    }

    /**
     * 显示运行结果
     */
    displayResults(results) {
        console.log('\n🎉 多品牌运行完成!');
        console.log('='.repeat(50));

        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);

        console.log(`✅ 成功: ${successful.length} 个品牌`);
        console.log(`❌ 失败: ${failed.length} 个品牌`);

        if (successful.length > 0) {
            console.log('\n📊 成功品牌详情:');
            successful.forEach(result => {
                console.log(`  ✅ ${result.brand}: ${result.articlesCount} 篇文章 (用时 ${Math.round(result.duration/1000)}秒)`);
            });
        }

        if (failed.length > 0) {
            console.log('\n❌ 失败品牌详情:');
            failed.forEach(result => {
                console.log(`  ❌ ${result.brand}: ${result.error}`);
            });
        }

        // 保存运行记录
        const runRecord = {
            timestamp: new Date().toISOString(),
            totalBrands: results.length,
            successful: successful.length,
            failed: failed.length,
            totalArticles: successful.reduce((sum, r) => sum + r.articlesCount, 0),
            results: results
        };

        const recordPath = path.join(this.baseDir, 'run_history.json');
        const history = fs.existsSync(recordPath) ? JSON.parse(fs.readFileSync(recordPath, 'utf8')) : [];
        history.push(runRecord);

        // 只保留最近50次记录
        if (history.length > 50) {
            history.splice(0, history.length - 50);
        }

        fs.writeFileSync(recordPath, JSON.stringify(history, null, 2));
        console.log(`\n📝 运行记录已保存: ${recordPath}`);
    }

    /**
     * 工具方法：延迟
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 主执行函数
async function main() {
    const cli = new MultiBrandCLI();

    // 解析命令行参数
    const argv = yargs(hideBin(process.argv))
        .command('run', '运行数据抓取', (yargs) => {
            return yargs
                .option('all', {
                    alias: 'a',
                    type: 'boolean',
                    description: '运行所有品牌'
                })
                .option('brand', {
                    alias: 'b',
                    type: 'string',
                    description: '运行指定品牌'
                });
        }, async (argv) => {
            if (argv.all) {
                await cli.runAllBrands();
            } else if (argv.brand) {
                await cli.runSingleBrand(argv.brand);
            } else {
                console.error('❌ 请指定 --all 或 --brand <品牌名>');
                process.exit(1);
            }
        })
        .command('status', '显示系统状态', {}, async () => {
            await cli.showStatus();
        })
        .command('health-check', '执行系统健康检查', {}, async () => {
            await cli.performHealthCheck();
        })
        .command('init <brand>', '初始化新品牌配置', {}, async (argv) => {
            await cli.initializeBrand(argv.brand);
        })
        .demandCommand(1, '请指定要执行的命令')
        .help()
        .alias('help', 'h')
        .version('1.0.0')
        .alias('version', 'v')
        .strict()
        .argv;

    return argv;
}

// 错误处理
process.on('unhandledRejection', (reason, promise) => {
    console.error('未处理的Promise拒绝:', reason);
    process.exit(1);
});

// 执行CLI
if (require.main === module) {
    main().catch(error => {
        console.error('CLI执行失败:', error);
        process.exit(1);
    });
}

module.exports = MultiBrandCLI;