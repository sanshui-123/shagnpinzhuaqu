#!/usr/bin/env node

/**
 * 多品牌系统安装脚本
 * 初始化所有必需的依赖和配置
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class MultiBrandSetup {
    constructor() {
        this.baseDir = path.join(__dirname, '..');
        this.packageJsonPath = path.join(this.baseDir, 'package.json');
        this.errors = [];
        this.warnings = [];
    }

    /**
     * 执行完整安装
     */
    async install() {
        console.log('🚀 开始安装多品牌数据抓取系统...\n');

        try {
            // 1. 检查Node.js版本
            this.checkNodeVersion();

            // 2. 检查系统依赖
            await this.checkSystemDependencies();

            // 3. 安装npm依赖
            await this.installDependencies();

            // 4. 创建必要目录
            this.createDirectories();

            // 5. 验证安装
            await this.validateInstallation();

            // 6. 生成启动脚本
            this.generateScripts();

            // 7. 显示安装结果
            this.showInstallationResult();

            if (this.errors.length === 0) {
                console.log('\n🎉 多品牌系统安装完成！');
                this.showNextSteps();
            } else {
                console.log('\n❌ 安装过程中发现问题，请查看错误信息');
                process.exit(1);
            }

        } catch (error) {
            console.error('\n❌ 安装失败:', error.message);
            process.exit(1);
        }
    }

    /**
     * 检查Node.js版本
     */
    checkNodeVersion() {
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);

        if (majorVersion < 16) {
            this.errors.push(`Node.js版本过低 (${nodeVersion})，需要 >= 16.0.0`);
        } else {
            console.log(`✅ Node.js版本检查通过: ${nodeVersion}`);
        }
    }

    /**
     * 检查系统依赖
     */
    async checkSystemDependencies() {
        console.log('🔍 检查系统依赖...');

        try {
            // 检查Puppeteer依赖
            execSync('npm list puppeteer', { stdio: 'pipe' });
            console.log('✅ Puppeteer依赖正常');
        } catch (error) {
            this.warnings.push('Puppeteer未安装，将在后续步骤中安装');
        }

        // 检查命令行工具
        const commands = ['node', 'npm'];
        for (const cmd of commands) {
            try {
                execSync(`${cmd} --version`, { stdio: 'pipe' });
                console.log(`✅ ${cmd} 可用`);
            } catch (error) {
                this.errors.push(`${cmd} 命令不可用，请确保已正确安装`);
            }
        }
    }

    /**
     * 安装npm依赖
     */
    async installDependencies() {
        console.log('\n📦 安装npm依赖...');

        const requiredPackages = [
            'puppeteer',
            'commander',
            'node-cron',
            'express',
            'cors'
        ];

        try {
            for (const pkg of requiredPackages) {
                try {
                    execSync(`npm list ${pkg}`, { stdio: 'pipe' });
                    console.log(`✅ ${pkg} 已安装`);
                } catch (error) {
                    console.log(`📥 安装 ${pkg}...`);
                    execSync(`npm install ${pkg}`, { stdio: 'inherit' });
                    console.log(`✅ ${pkg} 安装完成`);
                }
            }
        } catch (error) {
            this.errors.push(`依赖安装失败: ${error.message}`);
        }
    }

    /**
     * 创建必要目录
     */
    createDirectories() {
        console.log('\n📁 创建目录结构...');

        const directories = [
            'logs',
            'health_reports',
            'data',
            'golf_content',
            'brands',
            'temp'
        ];

        for (const dir of directories) {
            const dirPath = path.join(this.baseDir, dir);
            if (!fs.existsSync(dirPath)) {
                fs.mkdirSync(dirPath, { recursive: true });
                console.log(`✅ 创建目录: ${dir}`);
            } else {
                console.log(`ℹ️  目录已存在: ${dir}`);
            }
        }
    }

    /**
     * 验证安装
     */
    async validateInstallation() {
        console.log('\n🔧 验证安装...');

        // 检查核心文件
        const coreFiles = [
            'core/cli.js',
            'core/config_manager.js',
            'core/scraper_engine.js',
            'monitoring/health_monitor.js',
            'monitoring/scheduler.js',
            'utils/logger.js',
            'utils/validator.js'
        ];

        for (const file of coreFiles) {
            const filePath = path.join(this.baseDir, file);
            if (!fs.existsSync(filePath)) {
                this.errors.push(`核心文件缺失: ${file}`);
            }
        }

        // 检查品牌配置
        const brandsDir = path.join(this.baseDir, 'brands');
        if (fs.existsSync(brandsDir)) {
            const brandDirs = fs.readdirSync(brandsDir)
                .filter(item => {
                    const itemPath = path.join(brandsDir, item);
                    return fs.statSync(itemPath).isDirectory();
                });

            if (brandDirs.length > 0) {
                console.log(`✅ 找到 ${brandDirs.length} 个品牌配置`);
            } else {
                this.warnings.push('未找到品牌配置，请运行配置创建脚本');
            }
        }
    }

    /**
     * 生成启动脚本
     */
    generateScripts() {
        console.log('\n📜 生成启动脚本...');

        // 生成主启动脚本
        const startScript = `#!/bin/bash
# 多品牌系统启动脚本

echo "🚀 启动多品牌数据抓取系统..."

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 设置环境变量
export NODE_ENV=production

# 启动主控制器
cd "$(dirname "$0")"
node core/cli.js "$@"
`;

        const startScriptPath = path.join(this.baseDir, 'start.sh');
        fs.writeFileSync(startScriptPath, startScript);

        try {
            fs.chmodSync(startScriptPath, '755');
            console.log('✅ 生成启动脚本: start.sh');
        } catch (error) {
            this.warnings.push('无法设置启动脚本执行权限');
        }

        // 生成系统服务脚本
        const serviceScript = `#!/bin/bash
# 多品牌系统服务管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/multi_brand.pid"
LOG_FILE="$SCRIPT_DIR/logs/service.log"

case "$1" in
    start)
        echo "🚀 启动多品牌服务..."
        if [ -f "$PID_FILE" ]; then
            if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
                echo "⚠️ 服务已在运行"
                exit 1
            else
                rm -f "$PID_FILE"
            fi
        fi
        nohup node "$SCRIPT_DIR/monitoring/scheduler.js" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ 服务已启动"
        ;;
    stop)
        echo "⏹️ 停止多品牌服务..."
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null
            rm -f "$PID_FILE"
            echo "✅ 服务已停止"
        else
            echo "⚠️ 服务未运行"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ 服务运行中 (PID: $(cat "$PID_FILE"))"
        else
            echo "❌ 服务未运行"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "使用方法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
`;

        const serviceScriptPath = path.join(this.baseDir, 'service.sh');
        fs.writeFileSync(serviceScriptPath, serviceScript);

        try {
            fs.chmodSync(serviceScriptPath, '755');
            console.log('✅ 生成服务脚本: service.sh');
        } catch (error) {
            this.warnings.push('无法设置服务脚本执行权限');
        }
    }

    /**
     * 显示安装结果
     */
    showInstallationResult() {
        console.log('\n📊 安装结果:');
        console.log(`   错误: ${this.errors.length}`);
        console.log(`   警告: ${this.warnings.length}`);

        if (this.errors.length > 0) {
            console.log('\n❌ 错误详情:');
            this.errors.forEach(error => console.log(`   - ${error}`));
        }

        if (this.warnings.length > 0) {
            console.log('\n⚠️ 警告详情:');
            this.warnings.forEach(warning => console.log(`   - ${warning}`));
        }
    }

    /**
     * 显示后续步骤
     */
    showNextSteps() {
        console.log('\n📋 后续步骤:');
        console.log('\n1. 测试系统:');
        console.log('   node core/cli.js --help');
        console.log('\n2. 检查系统健康:');
        console.log('   node core/cli.js health-check');
        console.log('\n3. 查看品牌状态:');
        console.log('   node core/cli.js status');
        console.log('\n4. 运行单个品牌测试:');
        console.log('   node core/cli.js run --brand taylormade');
        console.log('\n5. 启动调度服务:');
        console.log('   ./service.sh start');
        console.log('\n📚 更多信息请查看 README.md');
    }
}

// 主执行逻辑
if (require.main === module) {
    const setup = new MultiBrandSetup();
    setup.install().catch(error => {
        console.error('❌ 安装失败:', error);
        process.exit(1);
    });
}

module.exports = MultiBrandSetup;