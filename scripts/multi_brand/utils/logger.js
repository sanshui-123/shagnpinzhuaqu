/**
 * 统一日志系统
 * 为多品牌系统提供标准化日志记录
 */

const fs = require('fs');
const path = require('path');

class Logger {
    constructor(name, options = {}) {
        this.name = name;
        this.level = options.level || 'info';
        this.baseDir = options.baseDir || path.join(__dirname, '..', '..', '..');
        this.logDir = path.join(this.baseDir, 'logs');
        this.logFile = path.join(this.logDir, `${name.toLowerCase()}_${this.getDateString()}.log`);

        this.ensureLogDir();
    }

    /**
     * 确保日志目录存在
     */
    ensureLogDir() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    /**
     * 获取日期字符串
     */
    getDateString() {
        return new Date().toISOString().split('T')[0];
    }

    /**
     * 获取时间戳
     */
    getTimestamp() {
        return new Date().toISOString().replace('T', ' ').split('.')[0];
    }

    /**
     * 格式化日志消息
     */
    formatMessage(level, message, data = null) {
        const timestamp = this.getTimestamp();
        const baseMessage = `[${timestamp}] [${level.toUpperCase()}] [${this.name}] ${message}`;

        if (data) {
            const dataStr = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
            return `${baseMessage}\n${dataStr}`;
        }

        return baseMessage;
    }

    /**
     * 写入日志文件
     */
    writeLog(formattedMessage) {
        try {
            fs.writeFileSync(this.logFile, formattedMessage + '\n', { flag: 'a' });
        } catch (error) {
            console.error('日志写入失败:', error.message);
        }
    }

    /**
     * 日志记录方法
     */
    log(level, message, data = null) {
        const formattedMessage = this.formatMessage(level, message, data);

        // 写入文件
        this.writeLog(formattedMessage);

        // 控制台输出
        if (this.shouldLogToConsole(level)) {
            console.log(formattedMessage);
        }
    }

    debug(message, data) {
        this.log('debug', message, data);
    }

    info(message, data) {
        this.log('info', message, data);
    }

    warn(message, data) {
        this.log('warn', message, data);
    }

    error(message, data) {
        this.log('error', message, data);
    }

    /**
     * 检查是否应该输出到控制台
     */
    shouldLogToConsole(level) {
        const levels = { debug: 0, info: 1, warn: 2, error: 3 };
        const currentLevel = levels[this.level] || 1;
        const messageLevel = levels[level] || 1;

        return messageLevel >= currentLevel;
    }

    /**
     * 创建子日志器
     */
    child(name, options = {}) {
        const childName = `${this.name}.${name}`;
        return new Logger(childName, { ...options, baseDir: this.baseDir });
    }

    /**
     * 清理旧日志文件
     */
    cleanup(daysToKeep = 7) {
        try {
            const files = fs.readdirSync(this.logDir);
            const cutoffTime = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);

            files.forEach(file => {
                const filePath = path.join(this.logDir, file);
                const stats = fs.statSync(filePath);

                if (stats.isFile() && stats.mtime.getTime() < cutoffTime) {
                    fs.unlinkSync(filePath);
                    console.log(`清理旧日志文件: ${file}`);
                }
            });

        } catch (error) {
            console.error('清理日志文件失败:', error.message);
        }
    }
}

module.exports = Logger;