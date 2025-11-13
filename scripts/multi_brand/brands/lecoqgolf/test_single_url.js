#!/usr/bin/env node

/**
 * 测试单个URL处理
 * 只处理第一个商品，生成完整字段数据
 */

const fs = require('fs');
const path = require('path');
const EnhancedDetailScraper = require('./enhanced_detail_scraper');

class SingleUrlTester {
    constructor() {
        this.scraper = new EnhancedDetailScraper();
        this.inputFile = './golf_content/lecoqgolf/lecoqgolf_products_2025-11-12T16-18-23-072Z.json';
        this.outputDir = './golf_content/lecoqgolf/';
    }

    async testSingleUrl() {
        console.log('🚀 测试单个URL处理...');
        console.log('🌐 运行模式：纯后台模式（无界面）');

        try {
            // 1. 读取商品列表
            const productData = await this.loadProductList();
            const products = this.extractProductUrls(productData);

            console.log(`📋 从文件加载 ${products.length} 个商品`);

            if (products.length === 0) {
                console.log('❌ 未找到商品URL');
                return;
            }

            // 2. 只处理第一个商品
            const firstProduct = products[0];
            console.log(`\n🔍 测试第一个商品:`);
            console.log(`   标题: ${firstProduct.title}`);
            console.log(`   URL: ${firstProduct.url}`);

            // 3. 处理详情页
            console.log('\n🔄 开始处理详情页...');
            const detailData = await this.scraper.scrapeDetailPage(firstProduct.url);

            // 4. 显示提取的字段
            console.log('\n✅ 处理完成！提取的字段：');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            Object.entries(detailData).forEach(([key, value]) => {
                let displayValue = value;
                if (typeof value === 'object') {
                    if (Array.isArray(value)) {
                        displayValue = `[${value.length}个] ${JSON.stringify(value).substring(0, 100)}...`;
                    } else {
                        displayValue = JSON.stringify(value).substring(0, 100) + '...';
                    }
                } else if (typeof value === 'string' && value.length > 100) {
                    displayValue = value.substring(0, 100) + '...';
                }
                console.log(`${key}: ${displayValue}`);
            });

            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // 5. 保存测试结果
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const testFile = path.join(this.outputDir, `single_url_test_${timestamp}.json`);

            const testData = {
                testType: 'single_url_processing',
                timestamp: new Date().toISOString(),
                sourceUrl: firstProduct.url,
                sourceTitle: firstProduct.title,
                totalFields: Object.keys(detailData).length,
                fields: Object.keys(detailData),
                data: detailData
            };

            // 确保输出目录存在
            if (!fs.existsSync(this.outputDir)) {
                fs.mkdirSync(this.outputDir, { recursive: true });
            }

            fs.writeFileSync(testFile, JSON.stringify(testData, null, 2));
            console.log(`\n💾 测试结果已保存: ${testFile}`);

            // 6. 启动HTTP服务器提供文件访问
            console.log('\n🌐 启动HTTP服务器...');
            const http = require('http');
            const url = require('url');
            const os = require('os');

            const port = 8082;
            const server = http.createServer((req, res) => {
                const parsedUrl = url.parse(req.url, true);

                // 设置CORS头
                res.setHeader('Access-Control-Allow-Origin', '*');
                res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
                res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

                if (parsedUrl.pathname === '/') {
                    // 生成文件列表页面
                    const files = fs.readdirSync(this.outputDir)
                        .filter(f => f.endsWith('.json'))
                        .sort((a, b) => fs.statSync(path.join(this.outputDir, b)).mtime - fs.statSync(path.join(this.outputDir, a)).mtime);

                    const html = this.generateFileListHTML(files, this.outputDir);
                    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                    res.end(html);
                } else if (parsedUrl.pathname.endsWith('.json')) {
                    // 提供JSON文件下载
                    const filePath = path.join(this.outputDir, path.basename(parsedUrl.pathname));
                    if (fs.existsSync(filePath)) {
                        const content = fs.readFileSync(filePath, 'utf8');
                        res.writeHead(200, {
                            'Content-Type': 'application/json; charset=utf-8',
                            'Content-Disposition': `attachment; filename="${path.basename(filePath)}"`
                        });
                        res.end(content);
                    } else {
                        res.writeHead(404);
                        res.end('File not found');
                    }
                } else {
                    res.writeHead(404);
                    res.end('Not found');
                }
            });

            server.listen(port, () => {
                const localIp = 'localhost';
                console.log(`\n📱 本地访问地址:`);
                console.log(`   http://${localIp}:${port}/`);
                console.log(`\n📋 您可以:`);
                console.log(`   1. 访问主页面查看文件列表`);
                console.log(`   2. 点击下载 single_url_test_${timestamp}.json`);
                console.log(`   3. 查看完整的产品字段数据`);
            });

            // 保持服务器运行
            process.on('SIGINT', () => {
                console.log('\n🛑 服务器已关闭');
                server.close();
                process.exit(0);
            });

        } catch (error) {
            console.error('❌ 测试失败:', error.message);
            console.error(error.stack);
        }
    }

    async loadProductList() {
        if (!fs.existsSync(this.inputFile)) {
            throw new Error(`商品列表文件不存在: ${this.inputFile}`);
        }

        const content = fs.readFileSync(this.inputFile, 'utf8');
        return JSON.parse(content);
    }

    extractProductUrls(productData) {
        console.log('🔍 数据结构分析:', Object.keys(productData));

        if (productData.results && Array.isArray(productData.results)) {
            console.log('✅ 找到 results 数组');
            // 从results中提取第一个collection的products
            if (productData.results[0] && productData.results[0].products) {
                console.log(`✅ 找到 ${productData.results[0].products.length} 个商品`);
                return productData.results[0].products;
            }
        } else if (Array.isArray(productData)) {
            return productData;
        } else if (productData.products && Array.isArray(productData.products)) {
            return productData.products;
        } else if (productData.data && Array.isArray(productData.data)) {
            return productData.data;
        }

        console.warn('⚠️ 未知的数据格式，尝试转换为数组');
        return Array.isArray(productData) ? productData : [productData];
    }

    generateFileListHTML(files, outputDir) {
        const fileRows = files.map(file => {
            const stats = fs.statSync(path.join(outputDir, file));
            const size = (stats.size / 1024).toFixed(2) + ' KB';
            const time = stats.mtime.toLocaleString('zh-CN');

            return `
                <tr>
                    <td><a href="/${file}" download="${file}">${file}</a></td>
                    <td>${size}</td>
                    <td>${time}</td>
                    <td><a href="/${file}" target="_blank">查看</a></td>
                </tr>
            `;
        }).join('');

        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Le Coq Sportif Golf 测试结果</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; text-align: center; margin-bottom: 30px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f8f9fa; font-weight: bold; }
                    tr:hover { background-color: #f5f5f5; }
                    a { color: #007bff; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                    .download-btn { background-color: #28a745; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; }
                    .download-btn:hover { background-color: #218838; }
                    .view-btn { background-color: #17a2b8; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; margin-left: 10px; }
                    .view-btn:hover { background-color: #138496; }
                    .info-box { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #007bff; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏌️ Le Coq Sportif Golf 单个URL测试结果</h1>

                    <div class="info-box">
                        <strong>测试说明：</strong>当前显示了处理第一个商品的完整字段数据。
                        <br>您可以直接下载JSON文件查看所有提取的字段和值。
                    </div>

                    <table>
                        <thead>
                            <tr>
                                <th>文件名</th>
                                <th>大小</th>
                                <th>修改时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fileRows}
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
        `;
    }
}

// 运行测试
if (require.main === module) {
    const tester = new SingleUrlTester();
    tester.testSingleUrl().catch(error => {
        console.error('❌ 单URL测试失败:', error);
        process.exit(1);
    });
}

module.exports = SingleUrlTester;