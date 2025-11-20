#!/usr/bin/env node

/**
 * 简单的文件服务器 - 提供测试结果文件访问
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const url = require('url');

const port = 8083;
const outputDir = './golf_content/lecoqgolf/';

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url, true);

    // 设置CORS头
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (parsedUrl.pathname === '/') {
        // 生成文件列表页面
        const files = fs.readdirSync(outputDir)
            .filter(f => f.includes('single_url_test') && f.endsWith('.json'))
            .sort((a, b) => fs.statSync(path.join(outputDir, b)).mtime - fs.statSync(path.join(outputDir, a)).mtime);

        const html = generateFileListHTML(files, outputDir);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
    } else if (parsedUrl.pathname.endsWith('.json')) {
        // 提供JSON文件查看
        const filePath = path.join(outputDir, path.basename(parsedUrl.pathname));
        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf8');

            // 直接在页面显示JSON内容
            res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
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

function generateFileListHTML(files, outputDir) {
    if (files.length === 0) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>测试结果 - 无文件</title>
            </head>
            <body>
                <h1>🏌️ Le Coq Sportif Golf 测试结果</h1>
                <p>暂无测试文件</p>
            </body>
            </html>
        `;
    }

    const fileRows = files.map(file => {
        const stats = fs.statSync(path.join(outputDir, file));
        const size = (stats.size / 1024).toFixed(2) + ' KB';
        const time = stats.mtime.toLocaleString('zh-CN');

        return `
            <tr>
                <td><a href="/${file}" target="_blank">${file}</a></td>
                <td>${size}</td>
                <td>${time}</td>
                <td><a href="/${file}" target="_blank" style="background-color: #007bff; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px;">查看JSON</a></td>
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
                .view-btn { background-color: #007bff; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; }
                .view-btn:hover { background-color: #0056b3; }
                .info-box { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #007bff; }
                .field-highlight { background-color: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏌️ Le Coq Sportif Golf 单个URL测试结果</h1>

                <div class="info-box">
                    <strong>✅ 测试完成！</strong>第一个商品的详情页已成功抓取。
                    <br>点击"查看JSON"按钮可以查看完整的产品字段数据。
                    <br><br>
                    <strong>📊 提取的主要字段：</strong>
                    <div class="field-highlight">
                    • 商品标题 (含翻译)<br>
                    • 商品编号: LG5FWB50M<br>
                    • 品牌: le coq sportif golf<br>
                    • 价格: ￥19,800<br>
                    • 性别: 男<br>
                    • 颜色选项 (6个颜色)<br>
                    • 尺码选项 (4个尺码)<br>
                    • 图片总数 (48张)<br>
                    • 详情页文字 (含翻译)<br>
                    • 尺码表 (完整HTML格式)<br>
                    • 库存统计
                    </div>
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

                <div class="info-box" style="margin-top: 30px;">
                    <strong>📱 使用说明：</strong>
                    <ul>
                        <li>点击"查看JSON"直接在浏览器中查看数据结构</li>
                        <li>数据包含所有提取字段和完整的值</li>
                        <li>如需下载文件，请在JSON页面右键选择"另存为"</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
    `;
}

server.listen(port, () => {
    console.log(`\n📱 本地访问地址已启动:`);
    console.log(`   http://localhost:${port}/`);
    console.log(`\n📋 您可以:`);
    console.log(`   1. 访问主页面查看测试文件`);
    console.log(`   2. 点击查看JSON数据`);
    console.log(`   3. 查看完整的产品字段提取结果`);
});

// 保持服务器运行
process.on('SIGINT', () => {
    console.log('\n🛑 服务器已关闭');
    server.close();
    process.exit(0);
});