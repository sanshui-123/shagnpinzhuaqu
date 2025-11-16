#!/usr/bin/env node

/**
 * Phase 2: 飞书13字段组装器
 * 基于原版卡拉威完整规则系统
 * 调用本地Python服务处理13个字段
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class Feishu13FieldsAssembler {
    constructor() {
        this.servicesPath = path.join(__dirname, 'services');
    }

    /**
     * 🎯 主入口：处理原始数据，生成13个飞书字段
     * 输入：phase1抓取的原始数据
     * 输出：13个飞书标准字段（原版规则）
     */
    async processRawData(scrapedData) {
        console.log('🔄 开始Phase 2处理（原版规则系统）...');
        console.log(`   品牌: ${scrapedData.brand}`);
        console.log(`   URL: ${scrapedData.url}`);

        try {
            // 调用原版Python服务处理
            const pythonScript = path.join(__dirname, 'process_13_fields.py');
            const inputData = {
                brand: scrapedData.brand,
                url: scrapedData.url,
                rawData: scrapedData.rawData
            };

            const result = await this.callPythonService(pythonScript, inputData);

            console.log(`✅ 原版规则处理完成`);
            console.log(`   标题生成: ${result.商品标题 ? result.商品标题.substring(0, 30) + '...' : '未生成'}`);
            console.log(`   13字段完整: ${Object.keys(result).length === 13 ? '✅' : '❌'}`);

            return result;

        } catch (error) {
            console.error('❌ Phase 2处理失败:', error.message);
            throw error;
        }
    }

    /**
     * 调用Python服务
     */
    async callPythonService(scriptPath, inputData) {
        return new Promise((resolve, reject) => {
            const python = spawn('python3', [scriptPath], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let stdout = '';
            let stderr = '';

            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            python.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            python.on('close', (code) => {
                if (code !== 0) {
                    console.error('Python服务错误:', stderr);
                    reject(new Error(`Python服务退出码: ${code}\n${stderr}`));
                    return;
                }

                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (parseError) {
                    console.error('JSON解析错误:', parseError.message);
                    console.error('Python输出:', stdout);
                    reject(new Error(`JSON解析失败: ${parseError.message}`));
                }
            });

            python.on('error', (error) => {
                reject(new Error(`Python服务启动失败: ${error.message}`));
            });

            // 发送输入数据
            python.stdin.write(JSON.stringify(inputData));
            python.stdin.end();
        });
    }

    /**
     * 验证13个字段完整性
     */
    validate13Fields(data) {
        const requiredFields = [
            '商品链接', '商品ID', '商品标题', '品牌名', '价格',
            '性别', '衣服分类', '图片数量', '图片链接',
            '颜色', '尺码', '详情页文字', '尺码表'
        ];

        const missing = requiredFields.filter(field => !(field in data));
        const empty = requiredFields.filter(field => {
            const value = data[field];
            return !value || (typeof value === 'string' && value.trim() === '');
        });

        console.log('\n📋 13字段验证:');
        console.log(`   ✅ 字段存在: ${requiredFields.length - missing.length}/${requiredFields.length}`);
        console.log(`   ✅ 非空字段: ${requiredFields.length - empty.length}/${requiredFields.length}`);

        if (missing.length > 0) {
            console.log(`   ❌ 缺失字段: ${missing.join(', ')}`);
        }
        if (empty.length > 0) {
            console.log(`   ⚠️ 空字段: ${empty.join(', ')}`);
        }

        return missing.length === 0;
    }

    /**
     * 批量处理测试数据
     */
    async batchProcess(testDataList) {
        console.log(`🚀 开始批量处理 ${testDataList.length} 条测试数据`);

        const results = [];
        for (let i = 0; i < testDataList.length; i++) {
            const testData = testDataList[i];
            console.log(`\n📋 处理进度: ${i + 1}/${testDataList.length}`);

            try {
                const result = await this.processRawData(testData);
                results.push({
                    index: i,
                    success: true,
                    data: result,
                    validation: this.validate13Fields(result)
                });
            } catch (error) {
                results.push({
                    index: i,
                    success: false,
                    error: error.message
                });
                console.error(`❌ 处理失败 (${i + 1}/${testDataList.length}):`, error.message);
            }
        }

        return results;
    }
}

module.exports = Feishu13FieldsAssembler;

// 如果直接运行此文件
if (require.main === module) {
    const assembler = new Feishu13FieldsAssembler();
    console.log('✅ 飞书13字段组装器已加载');
    console.log('📋 基于原版卡拉威完整规则系统');
    console.log('🎯 支持所有品牌的13字段处理');
}