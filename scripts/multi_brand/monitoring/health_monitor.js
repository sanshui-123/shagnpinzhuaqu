/**
 * 健康监控系统
 * 负责监控多品牌系统的健康状态和性能指标
 */

const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

class HealthMonitor extends EventEmitter {
    constructor() {
        super();
        this.baseDir = path.join(__dirname, '..', '..');
        this.healthData = new Map();
        this.alerts = [];
    }

    /**
     * 执行完整健康检查
     */
    async performFullCheck() {
        console.log('🔍 执行系统健康检查...');

        const results = {};
        const startTime = Date.now();

        try {
            // 1. 检查文件系统
            results.fileSystem = await this.checkFileSystem();

            // 2. 检查依赖模块
            results.dependencies = await this.checkDependencies();

            // 3. 检查品牌配置
            results.brandConfigs = await this.checkBrandConfigs();

            // 4. 检查磁盘空间
            results.diskSpace = await this.checkDiskSpace();

            // 5. 检查网络连接
            results.network = await this.checkNetworkConnectivity();

            // 6. 检查历史记录
            results.history = await this.checkHistoryHealth();

            // 7. 计算总体健康度
            const overall = this.calculateOverallHealth(results);

            const healthReport = {
                timestamp: new Date().toISOString(),
                duration: Date.now() - startTime,
                overall: overall,
                results: results,
                alerts: this.alerts,
                recommendations: this.generateRecommendations(results)
            };

            // 保存健康报告
            await this.saveHealthReport(healthReport);

            // 发出健康检查完成事件
            this.emit('healthCheckComplete', healthReport);

            return healthReport;

        } catch (error) {
            console.error('❌ 健康检查失败:', error.message);

            const errorReport = {
                timestamp: new Date().toISOString(),
                error: error.message,
                overall: 0,
                critical: true
            };

            this.emit('healthCheckError', errorReport);
            return errorReport;
        }
    }

    /**
     * 检查文件系统
     */
    async checkFileSystem() {
        const checks = [
            { path: this.baseDir, name: '根目录', required: true },
            { path: path.join(this.baseDir, 'core'), name: '核心模块', required: true },
            { path: path.join(this.baseDir, 'brands'), name: '品牌目录', required: false },
            { path: path.join(this.baseDir, 'monitoring'), name: '监控模块', required: true }
        ];

        let healthy = true;
        const missing = [];

        for (const check of checks) {
            if (!fs.existsSync(check.path)) {
                if (check.required) {
                    healthy = false;
                    missing.push(check.name);
                }
                console.warn(`⚠️ ${check.name} 不存在: ${check.path}`);
            }
        }

        return {
            healthy: healthy && missing.length === 0,
            message: healthy ? '文件系统正常' : `缺失必需目录: ${missing.join(', ')}`,
            details: { missing, checked: checks.map(c => c.name) }
        };
    }

    /**
     * 检查依赖模块
     */
    async checkDependencies() {
        const requiredModules = [
            'puppeteer',
            'commander',
            'fs',
            'path',
            'events'
        ];

        const missing = [];
        const installed = [];

        for (const module of requiredModules) {
            try {
                require.resolve(module);
                installed.push(module);
            } catch (error) {
                missing.push(module);
            }
        }

        const healthy = missing.length === 0;

        return {
            healthy: healthy,
            message: healthy ? '所有依赖正常' : `缺失依赖: ${missing.join(', ')}`,
            details: { installed, missing }
        };
    }

    /**
     * 检查品牌配置
     */
    async checkBrandConfigs() {
        try {
            const ConfigManager = require('../core/config_manager');
            const configManager = new ConfigManager();
            const brands = await configManager.getAllBrands();

            let healthyCount = 0;
            let totalCount = brands.length;
            const brandStatus = {};

            for (const brand of brands) {
                try {
                    const config = await configManager.getBrandConfig(brand);
                    const isHealthy = config && config.enabled;
                    brandStatus[brand] = {
                        healthy: isHealthy,
                        hasConfig: !!config,
                        enabled: config?.enabled || false
                    };

                    if (isHealthy) healthyCount++;

                } catch (error) {
                    brandStatus[brand] = {
                        healthy: false,
                        error: error.message
                    };
                }
            }

            const healthRatio = totalCount > 0 ? healthyCount / totalCount : 0;
            const healthy = healthRatio >= 0.8; // 80%以上品牌配置正常

            return {
                healthy: healthy,
                message: `${healthyCount}/${totalCount} 品牌配置正常`,
                details: {
                    total: totalCount,
                    healthy: healthyCount,
                    healthRatio: Math.round(healthRatio * 100),
                    brandStatus
                }
            };

        } catch (error) {
            return {
                healthy: false,
                message: `品牌配置检查失败: ${error.message}`,
                error: error.message
            };
        }
    }

    /**
     * 检查磁盘空间
     */
    async checkDiskSpace() {
        try {
            const stats = fs.statSync(this.baseDir);
            const freeSpace = await this.getFreeSpace(this.baseDir);

            // 检查是否有至少1GB可用空间
            const minSpace = 1024 * 1024 * 1024; // 1GB
            const healthy = freeSpace > minSpace;

            return {
                healthy: healthy,
                message: healthy ? '磁盘空间充足' : '磁盘空间不足',
                details: {
                    freeSpaceGB: Math.round(freeSpace / (1024 * 1024 * 1024) * 100) / 100,
                    minSpaceGB: Math.round(minSpace / (1024 * 1024 * 1024) * 100) / 100
                }
            };

        } catch (error) {
            return {
                healthy: false,
                message: `磁盘空间检查失败: ${error.message}`,
                error: error.message
            };
        }
    }

    /**
     * 获取可用空间（简化实现）
     */
    async getFreeSpace(dirPath) {
        try {
            // 这是一个简化的实现，实际应该使用更准确的方法
            const exec = require('child_process').execSync;
            const output = exec(`df -h "${dirPath}"`, { encoding: 'utf8' });
            const lines = output.split('\n');
            if (lines.length >= 2) {
                const parts = lines[1].split(/\s+/);
                const availableStr = parts[parts.length - 2]; // 倒数第二列是可用空间
                const availableNum = parseFloat(availableStr);
                const unit = availableStr.replace(/[\d.]/g, '');
                const multiplier = unit === 'G' ? 1024 * 1024 * 1024 :
                                 unit === 'M' ? 1024 * 1024 :
                                 unit === 'K' ? 1024 : 1;
                return Math.round(availableNum * multiplier);
            }
            return 10 * 1024 * 1024 * 1024; // 默认10GB
        } catch (error) {
            return 10 * 1024 * 1024 * 1024; // 默认10GB
        }
    }

    /**
     * 检查网络连接
     */
    async checkNetworkConnectivity() {
        const testUrls = [
            'https://www.google.com',
            'https://www.callawaygolf.com'
        ];

        const results = [];

        for (const url of testUrls) {
            try {
                const response = await fetch(url, {
                    method: 'HEAD',
                    timeout: 10000
                });
                results.push({
                    url: url,
                    success: response.ok,
                    status: response.status
                });
            } catch (error) {
                results.push({
                    url: url,
                    success: false,
                    error: error.message
                });
            }
        }

        const successCount = results.filter(r => r.success).length;
        const healthy = successCount >= Math.ceil(testUrls.length * 0.5); // 至少50%成功

        return {
            healthy: healthy,
            message: `${successCount}/${testUrls.length} 网络连接正常`,
            details: { results }
        };
    }

    /**
     * 检查历史记录健康度
     */
    async checkHistoryHealth() {
        try {
            const historyPath = path.join(this.baseDir, 'run_history.json');

            if (!fs.existsSync(historyPath)) {
                return {
                    healthy: true,
                    message: '暂无历史记录',
                    details: { hasHistory: false }
                };
            }

            const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
            const recentRuns = history.slice(-10); // 最近10次运行

            if (recentRuns.length === 0) {
                return {
                    healthy: true,
                    message: '暂无最近运行记录',
                    details: { hasHistory: false }
                };
            }

            const successCount = recentRuns.filter(run => run.successful > 0).length;
            const successRate = successCount / recentRuns.length;
            const healthy = successRate >= 0.7; // 70%以上成功率

            return {
                healthy: healthy,
                message: `最近成功率: ${Math.round(successRate * 100)}%`,
                details: {
                    totalRuns: recentRuns.length,
                    successCount: successCount,
                    successRate: Math.round(successRate * 100),
                    hasHistory: true
                }
            };

        } catch (error) {
            return {
                healthy: false,
                message: `历史记录检查失败: ${error.message}`,
                error: error.message
            };
        }
    }

    /**
     * 计算总体健康度
     */
    calculateOverallHealth(results) {
        const weights = {
            fileSystem: 20,
            dependencies: 20,
            brandConfigs: 25,
            diskSpace: 15,
            network: 10,
            history: 10
        };

        let totalScore = 0;
        let totalWeight = 0;

        for (const [component, weight] of Object.entries(weights)) {
            if (results[component]) {
                const score = results[component].healthy ? 100 : 0;
                totalScore += score * weight;
                totalWeight += weight;
            }
        }

        return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0;
    }

    /**
     * 生成健康建议
     */
    generateRecommendations(results) {
        const recommendations = [];

        if (results.fileSystem && !results.fileSystem.healthy) {
            recommendations.push('修复缺失的目录结构');
        }

        if (results.dependencies && !results.dependencies.healthy) {
            recommendations.push('安装缺失的依赖模块');
        }

        if (results.brandConfigs && !results.brandConfigs.healthy) {
            recommendations.push('检查和修复品牌配置文件');
        }

        if (results.diskSpace && !results.diskSpace.healthy) {
            recommendations.push('清理磁盘空间，确保至少有1GB可用空间');
        }

        if (results.network && !results.network.healthy) {
            recommendations.push('检查网络连接和防火墙设置');
        }

        if (results.history && !results.history.healthy) {
            recommendations.push('检查最近的运行记录，分析失败原因');
        }

        return recommendations;
    }

    /**
     * 保存健康报告
     */
    async saveHealthReport(healthReport) {
        try {
            const reportPath = path.join(this.baseDir, 'health_reports');
            if (!fs.existsSync(reportPath)) {
                fs.mkdirSync(reportPath, { recursive: true });
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const reportFile = path.join(reportPath, `health_${timestamp}.json`);

            fs.writeFileSync(reportFile, JSON.stringify(healthReport, null, 2));

            // 更新最新报告链接
            const latestReport = path.join(reportPath, 'latest_health.json');
            if (fs.existsSync(latestReport)) {
                fs.unlinkSync(latestReport);
            }
            fs.symlinkSync(path.basename(reportFile), latestReport);

            console.log(`💾 健康报告已保存: ${reportFile}`);

        } catch (error) {
            console.error('❌ 保存健康报告失败:', error.message);
        }
    }

    /**
     * 获取整体健康状态
     */
    async getOverallHealth() {
        try {
            const latestReportPath = path.join(this.baseDir, 'health_reports', 'latest_health.json');

            if (!fs.existsSync(latestReportPath)) {
                return {
                    overall: 0,
                    activeBrands: 0,
                    totalBrands: 0,
                    lastUpdate: '无数据'
                };
            }

            const report = JSON.parse(fs.readFileSync(latestReportPath, 'utf8'));

            return {
                overall: report.overall,
                activeBrands: report.results?.brandConfigs?.details?.healthy || 0,
                totalBrands: report.results?.brandConfigs?.details?.total || 0,
                lastUpdate: report.timestamp,
                critical: report.overall < 50
            };

        } catch (error) {
            return {
                overall: 0,
                activeBrands: 0,
                totalBrands: 0,
                lastUpdate: '读取失败',
                error: error.message
            };
        }
    }

    /**
     * 获取最近运行记录
     */
    async getRecentRuns(limit = 10) {
        try {
            const historyPath = path.join(this.baseDir, 'run_history.json');

            if (!fs.existsSync(historyPath)) {
                return [];
            }

            const history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
            return history.slice(-limit).reverse(); // 最新的在前

        } catch (error) {
            console.error('获取运行记录失败:', error.message);
            return [];
        }
    }

    /**
     * 监控系统指标
     */
    startMonitoring() {
        console.log('🔍 启动健康监控...');

        // 每30分钟执行一次健康检查
        this.monitoringInterval = setInterval(async () => {
            try {
                const healthReport = await this.performFullCheck();

                if (healthReport.overall < 70) {
                    console.warn(`⚠️ 系统健康度较低: ${healthReport.overall}%`);
                    this.emit('healthAlert', healthReport);
                }

            } catch (error) {
                console.error('❌ 监控检查失败:', error.message);
            }
        }, 30 * 60 * 1000); // 30分钟

        console.log('✅ 健康监控已启动 (每30分钟检查一次)');
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
            console.log('⏹️ 健康监控已停止');
        }
    }
}

module.exports = HealthMonitor;