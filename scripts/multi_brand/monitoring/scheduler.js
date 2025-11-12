/**
 * 任务调度系统
 * 负责10天循环的多品牌任务调度
 */

const cron = require('node-cron');
const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

class Scheduler extends EventEmitter {
    constructor() {
        super();
        this.baseDir = path.join(__dirname, '..', '..');
        this.configPath = path.join(this.baseDir, 'brands', 'brand_configs.json');
        this.scheduleConfig = this.loadScheduleConfig();
        this.runningTasks = new Map();
        this.completedTasks = new Map();
        this.failedTasks = new Map();
        this.cronJobs = new Map();
    }

    /**
     * 加载调度配置
     */
    loadScheduleConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
                return config.schedule || this.getDefaultScheduleConfig();
            }
        } catch (error) {
            console.warn('⚠️ 调度配置加载失败，使用默认配置:', error.message);
        }

        return this.getDefaultScheduleConfig();
    }

    /**
     * 获取默认调度配置
     */
    getDefaultScheduleConfig() {
        return {
            interval: '10-days',
            groups: [
                ['callaway', 'taylormade', 'titleist'],
                ['ping', 'cobra', 'bridgestone'],
                ['mizuno', 'srixon', 'pxg'],
                ['honma', 'wilson', 'adams'],
                ['cleveland', 'scotty', 'odyssey']
            ]
        };
    }

    /**
     * 启动调度器
     */
    start() {
        console.log('🚀 启动多品牌任务调度器...');

        // 每天凌晨2点检查任务
        const dailyCheck = cron.schedule('0 2 * * *', async () => {
            await this.checkAndRunScheduledTasks();
        }, {
            scheduled: false,
            timezone: 'Asia/Shanghai'
        });

        this.cronJobs.set('dailyCheck', dailyCheck);
        dailyCheck.start();

        // 每周日执行完整健康检查
        const weeklyHealthCheck = cron.schedule('0 3 * * 0', async () => {
            await this.performWeeklyHealthCheck();
        }, {
            scheduled: false,
            timezone: 'Asia/Shanghai'
        });

        this.cronJobs.set('weeklyHealthCheck', weeklyHealthCheck);
        weeklyHealthCheck.start();

        console.log('✅ 调度器已启动');
        console.log('📅 调度计划:');
        console.log('   - 每日检查: 02:00 (北京时间)');
        console.log('   - 健康检查: 每周日 03:00');
        console.log('   - 任务间隔: 10天循环');

        // 显示下次运行时间
        this.showNextRunTimes();
    }

    /**
     * 停止调度器
     */
    stop() {
        console.log('⏹️ 停止调度器...');

        for (const [name, job] of this.cronJobs) {
            job.stop();
            console.log(`   - 已停止: ${name}`);
        }

        this.cronJobs.clear();
        console.log('✅ 调度器已停止');
    }

    /**
     * 检查并运行计划任务
     */
    async checkAndRunScheduledTasks() {
        const today = new Date();
        const dayOfMonth = today.getDate();
        const dayOfWeek = today.getDay(); // 0 = 周日

        console.log(`\n📅 ${today.toLocaleDateString()} 检查计划任务...`);

        try {
            // 获取应该今天运行的品牌组
            const scheduledGroup = this.getScheduledGroup(dayOfMonth);

            if (scheduledGroup.length > 0) {
                console.log(`🔄 今天计划运行: ${scheduledGroup.join(', ')}`);

                // 检查是否在10天间隔内
                if (this.shouldRunToday()) {
                    await this.runBrandGroup(scheduledGroup);
                } else {
                    console.log('⏸️ 在10天间隔期内，跳过本次运行');
                }
            } else {
                console.log('ℹ️ 今天没有计划任务');
            }

            // 清理过期数据
            await this.cleanupOldData();

        } catch (error) {
            console.error('❌ 计划任务检查失败:', error.message);
            this.emit('schedulerError', { error: error.message, timestamp: today });
        }
    }

    /**
     * 获取应该今天运行的品牌组
     */
    getScheduledGroup(dayOfMonth) {
        const scheduleDays = {
            1: 0,  // 第1组
            2: 1,  // 第2组
            3: 2,  // 第3组
            4: 3,  // 第4组
            5: 4,  // 第5组
            6: 0,  // 第1组
            7: 1,  // 第2组
            8: 2,  // 第3组
            9: 3,  // 第4组
            10: 4, // 第5组
        };

        const groupIndex = scheduleDays[dayOfMonth];
        return groupIndex !== undefined ? this.scheduleConfig.groups[groupIndex] : [];
    }

    /**
     * 检查是否应该在今天运行（10天间隔逻辑）
     */
    shouldRunToday() {
        const today = new Date();
        const lastRunFile = path.join(this.baseDir, 'scheduler_state.json');

        try {
            if (fs.existsSync(lastRunFile)) {
                const state = JSON.parse(fs.readFileSync(lastRunFile, 'utf8'));
                const lastRun = new Date(state.lastRun);

                const daysDiff = Math.floor((today - lastRun) / (1000 * 60 * 60 * 24));

                // 如果上次运行距离现在不到10天，跳过
                return daysDiff >= 10;
            }
        } catch (error) {
            console.warn('⚠️ 读取调度状态失败，将执行运行:', error.message);
        }

        return true; // 默认运行
    }

    /**
     * 运行品牌组
     */
    async runBrandGroup(brands) {
        console.log(`\n🚀 开始运行品牌组: ${brands.join(', ')}`);

        const startTime = Date.now();
        const results = [];

        // 依次运行品牌（避免并发冲突）
        for (const brand of brands) {
            try {
                console.log(`\n🔄 运行品牌: ${brand}`);

                // 检查是否已在运行
                if (this.runningTasks.has(brand)) {
                    console.log(`⚠️ ${brand} 已在运行中，跳过`);
                    continue;
                }

                this.runningTasks.set(brand, { startTime: Date.now() });

                // 运行品牌抓取
                const result = await this.runBrandTask(brand);

                this.runningTasks.delete(brand);

                if (result.success) {
                    this.completedTasks.set(brand, result);
                    console.log(`✅ ${brand} 完成: ${result.articlesCount} 篇文章`);
                } else {
                    this.failedTasks.set(brand, result);
                    console.log(`❌ ${brand} 失败: ${result.error}`);
                }

                results.push(result);

                // 品牌间延迟
                await this.delay(60000); // 1分钟

            } catch (error) {
                this.runningTasks.delete(brand);
                const failedResult = {
                    brand: brand,
                    success: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                };

                this.failedTasks.set(brand, failedResult);
                results.push(failedResult);

                console.error(`❌ ${brand} 运行异常:`, error.message);
            }
        }

        // 保存运行状态
        await this.saveSchedulerState();

        // 记录结果
        const groupResult = {
            brands: brands,
            timestamp: new Date().toISOString(),
            duration: Date.now() - startTime,
            results: results,
            success: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length,
            totalArticles: results.reduce((sum, r) => sum + (r.articlesCount || 0), 0)
        };

        await this.saveGroupResult(groupResult);

        // 发出完成事件
        this.emit('groupCompleted', groupResult);

        console.log(`\n🎉 品牌组运行完成!`);
        console.log(`   成功: ${groupResult.success} 个`);
        console.log(`   失败: ${groupResult.failed} 个`);
        console.log(`   总文章: ${groupResult.totalArticles} 篇`);
        console.log(`   用时: ${Math.round(groupResult.duration / 1000)} 秒`);
    }

    /**
     * 运行单个品牌任务
     */
    async runBrandTask(brand) {
        try {
            // 使用统一CLI运行
            const { execSync } = require('child_process');
            const cliPath = path.join(this.baseDir, 'core', 'cli.js');

            const output = execSync(`node "${cliPath}" run --brand ${brand}`, {
                cwd: this.baseDir,
                encoding: 'utf8',
                timeout: 30 * 60 * 1000 // 30分钟超时
            });

            // 解析输出结果
            const articlesCount = this.parseOutputForArticleCount(output);

            return {
                brand: brand,
                success: true,
                articlesCount: articlesCount,
                output: output,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            return {
                brand: brand,
                success: false,
                error: error.message,
                output: error.stdout,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 解析输出中的文章数量
     */
    parseOutputForArticleCount(output) {
        const match = output.match(/(\d+)\s*篇文章|articles:\s*(\d+)/i);
        return match ? parseInt(match[1] || match[2]) : 0;
    }

    /**
     * 保存调度器状态
     */
    async saveSchedulerState() {
        try {
            const state = {
                lastRun: new Date().toISOString(),
                runningTasks: Array.from(this.runningTasks.keys()),
                completedTasks: Array.from(this.completedTasks.keys()),
                failedTasks: Array.from(this.failedTasks.keys())
            };

            const stateFile = path.join(this.baseDir, 'scheduler_state.json');
            fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));

        } catch (error) {
            console.error('❌ 保存调度状态失败:', error.message);
        }
    }

    /**
     * 保存组运行结果
     */
    async saveGroupResult(result) {
        try {
            const historyFile = path.join(this.baseDir, 'scheduler_history.json');
            let history = [];

            if (fs.existsSync(historyFile)) {
                history = JSON.parse(fs.readFileSync(historyFile, 'utf8'));
            }

            history.push(result);

            // 只保留最近50次记录
            if (history.length > 50) {
                history = history.slice(-50);
            }

            fs.writeFileSync(historyFile, JSON.stringify(history, null, 2));

        } catch (error) {
            console.error('❌ 保存组结果失败:', error.message);
        }
    }

    /**
     * 执行周度健康检查
     */
    async performWeeklyHealthCheck() {
        console.log('\n🏥 执行周度健康检查...');

        try {
            const HealthMonitor = require('./health_monitor');
            const healthMonitor = new HealthMonitor();

            const healthReport = await healthMonitor.performFullCheck();

            if (healthReport.overall < 70) {
                console.warn(`⚠️ 系统健康度较低: ${healthReport.overall}%`);
                this.emit('healthAlert', healthReport);
            }

            console.log(`✅ 健康检查完成，总体健康度: ${healthReport.overall}%`);

        } catch (error) {
            console.error('❌ 健康检查失败:', error.message);
        }
    }

    /**
     * 清理过期数据
     */
    async cleanupOldData() {
        try {
            const maxAge = 30 * 24 * 60 * 60 * 1000; // 30天
            const now = Date.now();

            // 清理过期的运行记录
            const historyFile = path.join(this.baseDir, 'scheduler_history.json');
            if (fs.existsSync(historyFile)) {
                const history = JSON.parse(fs.readFileSync(historyFile, 'utf8'));
                const filtered = history.filter(record => {
                    const recordTime = new Date(record.timestamp).getTime();
                    return (now - recordTime) < maxAge;
                });

                if (filtered.length !== history.length) {
                    fs.writeFileSync(historyFile, JSON.stringify(filtered, null, 2));
                    console.log(`🧹 清理了 ${history.length - filtered.length} 条过期记录`);
                }
            }

        } catch (error) {
            console.warn('⚠️ 清理过期数据失败:', error.message);
        }
    }

    /**
     * 显示下次运行时间
     */
    showNextRunTimes() {
        const now = new Date();
        console.log('\n⏰ 下次运行时间:');

        // 显示明天的检查时间
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(2, 0, 0, 0);
        console.log(`   - 下次检查: ${tomorrow.toLocaleString()}`);

        // 显示下次组运行时间
        const nextGroupDate = this.getNextGroupRunDate(now);
        if (nextGroupDate) {
            console.log(`   - 下次组运行: ${nextGroupDate.toLocaleString()}`);
        }
    }

    /**
     * 获取下次组运行日期
     */
    getNextGroupRunDate(currentDate) {
        const dayOfMonth = currentDate.getDate();
        let nextDay = dayOfMonth + 1;

        while (nextDay <= 31) {
            const scheduledGroup = this.getScheduledGroup(nextDay);
            if (scheduledGroup.length > 0) {
                const nextDate = new Date(currentDate);
                nextDate.setDate(nextDay);
                nextDate.setHours(9, 0, 0, 0); // 上午9点运行
                return nextDate;
            }
            nextDay++;
        }

        return null;
    }

    /**
     * 获取调度状态
     */
    getSchedulerStatus() {
        return {
            isRunning: this.cronJobs.size > 0,
            runningTasks: Array.from(this.runningTasks.keys()),
            completedToday: this.completedTasks.size,
            failedToday: this.failedTasks.size,
            activeJobs: Array.from(this.cronJobs.keys()),
            scheduleConfig: this.scheduleConfig
        };
    }

    /**
     * 手动触发运行
     */
    async manualRun(brands) {
        console.log(`\n🔧 手动触发运行: ${brands.join(', ')}`);

        try {
            await this.runBrandGroup(brands);
            return true;
        } catch (error) {
            console.error('❌ 手动运行失败:', error.message);
            return false;
        }
    }

    /**
     * 延迟工具
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = Scheduler;