const axios = require('axios');
const fs = require('fs');
const path = require('path');

/**
 * 通知服务
 * 支持多种通知方式：邮件、钉钉、企业微信、飞书等
 */
class NotificationService {
  constructor() {
    this.config = this.loadConfig();
  }

  /**
   * 加载配置
   */
  loadConfig() {
    const configPath = path.resolve(process.cwd(), 'notification-config.json');

    // 默认配置
    const defaultConfig = {
      enabled: false,
      channels: {
        email: {
          enabled: false,
          smtp: {
            host: '',
            port: 587,
            secure: false,
            auth: {
              user: '',
              pass: ''
            }
          },
          from: '',
          to: []
        },
        dingtalk: {
          enabled: false,
          webhook: '',
          secret: ''
        },
        wechat: {
          enabled: false,
          webhook: ''
        },
        feishu: {
          enabled: false,
          webhook: ''
        },
        console: {
          enabled: true,
          color: true
        }
      },
      templates: {
        success: {
          title: '商品发布成功',
          body: '商品 {productId} "{title}" 已成功发布到淘宝\n链接: {url}'
        },
        error: {
          title: '商品发布失败',
          body: '商品 {productId} "{title}" 发布失败\n错误: {error}'
        },
        warning: {
          title: '商品发布警告',
          body: '商品 {productId} "{title}" 发布过程中有警告\n警告: {warnings}'
        }
      }
    };

    // 加载用户配置
    if (fs.existsSync(configPath)) {
      try {
        const userConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        return { ...defaultConfig, ...userConfig };
      } catch (error) {
        console.warn(`加载通知配置失败: ${error.message}`);
      }
    }

    return defaultConfig;
  }

  /**
   * 发送通知
   */
  async send(notification) {
    if (!this.config.enabled) {
      console.log('通知服务未启用');
      return;
    }

    const { type, productId, title, duration, summary, taobaoUrl, message } = notification;

    // 控制台输出
    if (this.config.channels.console.enabled) {
      this.sendToConsole(notification);
    }

    // 邮件通知
    if (this.config.channels.email.enabled) {
      await this.sendEmail(notification).catch(error => {
        console.error('邮件通知失败:', error.message);
      });
    }

    // 钉钉通知
    if (this.config.channels.dingtalk.enabled) {
      await this.sendDingTalk(notification).catch(error => {
        console.error('钉钉通知失败:', error.message);
      });
    }

    // 企业微信通知
    if (this.config.channels.wechat.enabled) {
      await this.sendWeChat(notification).catch(error => {
        console.error('企业微信通知失败:', error.message);
      });
    }

    // 飞书通知
    if (this.config.channels.feishu.enabled) {
      await this.sendFeishu(notification).catch(error => {
        console.error('飞书通知失败:', error.message);
      });
    }
  }

  /**
   * 控制台通知
   */
  sendToConsole(notification) {
    const { type, productId, title, duration, taobaoUrl } = notification;
    const colors = this.config.channels.console.color;

    if (colors) {
      const color = type === 'success' ? '\x1b[32m' : type === 'error' ? '\x1b[31m' : '\x1b[33m';
      const reset = '\x1b[0m';

      console.log(`\n${color}=== 通知 ===${reset}`);
      console.log(`${color}类型: ${type}${reset}`);
      console.log(`${color}商品ID: ${productId}${reset}`);
      console.log(`${color}标题: ${title}${reset}`);
      console.log(`${color}耗时: ${duration}${reset}`);
      if (taobaoUrl) {
        console.log(`${color}链接: ${taobaoUrl}${reset}`);
      }
      console.log(`${color}时间: ${new Date().toLocaleString()}${reset}`);
    } else {
      console.log('\n=== 通知 ===');
      console.log(`类型: ${type}`);
      console.log(`商品ID: ${productId}`);
      console.log(`标题: ${title}`);
      console.log(`耗时: ${duration}`);
      if (taobaoUrl) {
        console.log(`链接: ${taobaoUrl}`);
      }
      console.log(`时间: ${new Date().toLocaleString()}`);
    }
  }

  /**
   * 邮件通知
   */
  async sendEmail(notification) {
    const config = this.config.channels.email;
    const template = this.config.templates[notification.type];

    const subject = this.formatTemplate(template.title, notification);
    const body = this.formatTemplate(template.body, notification);

    const emailData = {
      from: config.from,
      to: config.to.join(','),
      subject: subject,
      text: body,
      html: `<pre>${body}</pre>`
    };

    // 这里需要安装nodemailer: npm install nodemailer
    try {
      const nodemailer = require('nodemailer');
      const transporter = nodemailer.createTransporter(config.smtp);

      await transporter.sendMail(emailData);
      console.log('邮件通知已发送');
    } catch (error) {
      if (error.code === 'MODULE_NOT_FOUND') {
        console.warn('未安装nodemailer，跳过邮件通知');
        console.warn('请运行: npm install nodemailer');
      } else {
        throw error;
      }
    }
  }

  /**
   * 钉钉通知
   */
  async sendDingTalk(notification) {
    const config = this.config.channels.dingtalk;
    const template = this.config.templates[notification.type];

    const text = this.formatTemplate(`${template.title}\n\n${template.body}`, notification);

    const data = {
      msgtype: 'text',
      text: {
        content: text
      }
    };

    // 如果配置了密钥，需要签名
    if (config.secret) {
      const crypto = require('crypto');
      const timestamp = Date.now();
      const sign = crypto
        .createHmac('sha256', config.secret)
        .update(`${timestamp}\n${config.secret}`)
        .digest('base64');

      data.timestamp = timestamp;
      data.sign = sign;
    }

    const response = await axios.post(config.webhook, data);
    if (response.data.errcode === 0) {
      console.log('钉钉通知已发送');
    } else {
      throw new Error(response.data.errmsg);
    }
  }

  /**
   * 企业微信通知
   */
  async sendWeChat(notification) {
    const config = this.config.channels.wechat;
    const template = this.config.templates[notification.type];

    const content = this.formatTemplate(`${template.title}\n\n${template.body}`, notification);

    const data = {
      msgtype: 'text',
      text: {
        content: content
      }
    };

    const response = await axios.post(config.webhook, data);
    if (response.data.errcode === 0) {
      console.log('企业微信通知已发送');
    } else {
      throw new Error(response.data.errmsg);
    }
  }

  /**
   * 飞书通知
   */
  async sendFeishu(notification) {
    const config = this.config.channels.feishu;
    const template = this.config.templates[notification.type];

    const content = this.formatTemplate(`${template.title}\n\n${template.body}`, notification);

    const data = {
      msg_type: 'text',
      content: {
        text: content
      }
    };

    const response = await axios.post(config.webhook, data);
    if (response.data.code === 0) {
      console.log('飞书通知已发送');
    } else {
      throw new Error(response.data.msg);
    }
  }

  /**
   * 格式化模板
   */
  formatTemplate(template, notification) {
    let result = template;

    // 替换占位符
    const placeholders = {
      '{productId}': notification.productId || '',
      '{title}': notification.title || '',
      '{duration}': notification.duration || '',
      '{url}': notification.taobaoUrl || '',
      '{error}': notification.message || notification.summary?.errors?.join('; ') || '',
      '{warnings}': notification.summary?.warnings?.join('; ') || '',
      '{time}': new Date().toLocaleString()
    };

    for (const [placeholder, value] of Object.entries(placeholders)) {
      result = result.replace(new RegExp(placeholder, 'g'), value);
    }

    return result;
  }

  /**
   * 测试通知
   */
  async test() {
    const testNotification = {
      type: 'success',
      productId: 'TEST-001',
      title: '测试商品',
      duration: '2分30秒',
      taobaoUrl: 'https://item.taobao.com/item.htm?id=123456789',
      message: '这是一条测试通知'
    };

    await this.send(testNotification);
    console.log('测试通知已发送');
  }

  /**
   * 创建配置文件
   */
  createConfigFile() {
    const configPath = path.resolve(process.cwd(), 'notification-config.json');

    if (fs.existsSync(configPath)) {
      console.log('配置文件已存在:', configPath);
      return;
    }

    const exampleConfig = {
      enabled: true,
      channels: {
        email: {
          enabled: false,
          smtp: {
            host: 'smtp.example.com',
            port: 587,
            secure: false,
            auth: {
              user: 'your-email@example.com',
              pass: 'your-password'
            }
          },
          from: 'your-email@example.com',
          to: ['recipient@example.com']
        },
        dingtalk: {
          enabled: false,
          webhook: 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN',
          secret: 'YOUR_SECRET'
        },
        wechat: {
          enabled: false,
          webhook: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY'
        },
        feishu: {
          enabled: false,
          webhook: 'https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK'
        },
        console: {
          enabled: true,
          color: true
        }
      }
    };

    fs.writeFileSync(configPath, JSON.stringify(exampleConfig, null, 2));
    console.log('配置文件已创建:', configPath);
    console.log('请编辑配置文件并启用所需的通知渠道');
  }
}

// 创建单例实例
const notificationService = new NotificationService();

// 导出服务
module.exports = { notificationService, NotificationService };