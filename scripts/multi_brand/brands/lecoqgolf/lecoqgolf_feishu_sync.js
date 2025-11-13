#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 飞书数据同步器
 * 基于卡拉威的飞书处理逻辑，适配Le Coq Sportif Golf的12字段数据结构
 */

const fs = require('fs');
const path = require('path');
const csv = require('csv-writer');
const CompleteTitleGenerator = require('../../shared/title_generator_complete');

class LeCoqGolfFeishuSync {
    constructor() {
        this.inputDir = './golf_content/lecoqgolf/';
        this.outputDir = './golf_content/lecoqgolf/';
        this.titleGenerator = new CompleteTitleGenerator();

        // Le Coq Sportif Golf 的12个字段映射到飞书列名
        this.fieldMapping = {
            '商品链接': '商品链接',          // 原样映射
            '商品ID': '商品id',             // 映射到飞书的"商品id"列
            '商品标题': '商品标题',          // 原样映射
            '品牌名': '品牌',              // 映射到飞书的"品牌"列
            '价格': '价格',                // 原样映射
            '性别': '性别',                // 原样映射
            '颜色': '颜色',                // 原样映射
            '尺码': '尺码',                // 原样映射
            '衣服分类': '衣服分类',        // 原样映射
            '图片总数': '图片数量',        // 映射到飞书的"图片数量"列
            '图片链接': '图片URL',         // 映射到飞书的"图片URL"列
            '详情页文字': '详情页文字',     // 原样映射
            '尺码表': '尺码表'             // 原样映射
        };

        // 飞书列名顺序（用于CSV生成）
        this.feishuColumns = [
            '商品链接',
            '商品id',
            '商品标题',
            '品牌',
            '价格',
            '性别',
            '颜色',
            '尺码',
            '衣服分类',
            '图片数量',
            '图片URL',
            '详情页文字',
            '尺码表'
        ];
    }

    /**
     * 处理单个产品的数据转换
     */
    async processProduct(rawData) {
        const processed = {};

        // 按照飞书列顺序处理数据
        for (const feishuColumn of this.feishuColumns) {
            // 找到对应的源字段
            const sourceField = this.findSourceField(feishuColumn);
            let value = this.extractFieldValue(rawData, sourceField);

            // 特殊处理商品标题 - 使用智能标题生成器
            if (feishuColumn === '商品标题') {
                try {
                    const titleResult = await this.titleGenerator.generateTitle(rawData);
                    value = titleResult.generated;
                    console.log(`✅ 智能标题生成: ${value} (${value.length}字)`);
                } catch (error) {
                    console.warn(`⚠️ 标题生成失败，使用原标题: ${error.message}`);
                    value = this.extractFieldValue(rawData, sourceField);
                }
            } else {
                // 数据清理和格式化
                value = this.formatFieldValue(feishuColumn, value);
            }

            processed[feishuColumn] = value;
        }

        return processed;
    }

    /**
     * 从原始数据中提取字段值
     */
    extractFieldValue(rawData, sourceField) {
        // 处理嵌套的对象结构和不同的字段名
        switch (sourceField) {
            case '商品链接':
                return rawData.url || rawData['商品链接'] || '';

            case '商品ID':
                return rawData.productCode || rawData['商品ID'] || '';

            case '商品标题':
                if (rawData.title) {
                    if (rawData.title.translated) {
                        return rawData.title.translated;
                    }
                    return rawData.title.original || rawData.title || '';
                }
                return rawData['商品标题'] || '';

            case '品牌名':
                return rawData.brand || rawData['品牌名'] || '';

            case '价格':
                return rawData.price || rawData['价格'] || '';

            case '性别':
                return rawData.gender || rawData['性别'] || '';

            case '颜色':
                if (rawData.colors && Array.isArray(rawData.colors)) {
                    return rawData.colors.map(c => c.name).join(', ');
                }
                return rawData.colors || rawData['颜色'] || '';

            case '尺码':
                if (rawData.sizes && Array.isArray(rawData.sizes)) {
                    // 如果尺码是对象数组，提取尺码名称
                    if (typeof rawData.sizes[0] === 'object') {
                        return rawData.sizes.map(size => size.name || size.size || size).join(', ');
                    }
                    return rawData.sizes.join(', ');
                } else if (rawData.sizeChart && rawData.sizeChart.sizes) {
                    // 从尺码表中提取尺码
                    if (Array.isArray(rawData.sizeChart.sizes)) {
                        return rawData.sizeChart.sizes.map(size => size.size || size).join(', ');
                    }
                }
                return rawData.sizes || rawData['尺码'] || '';

            case '衣服分类':
                // 从商品名推断衣服分类
                const productName = rawData.title?.original || '';
                if (productName.includes('ジャケット') || productName.includes('jacket')) {
                    return '外套';
                } else if (productName.includes('ベスト') || productName.includes('vest')) {
                    return '背心';
                } else if (productName.includes('パンツ') || productName.includes('pants')) {
                    return '长裤';
                } else if (productName.includes('ポロ') || productName.includes('polo') || productName.includes('シャツ')) {
                    return '上衣';
                }
                return '服装';

            case '图片总数':
                if (rawData.images && rawData.images.total) {
                    return rawData.images.total.toString();
                }
                return '0';

            case '图片链接':
                if (rawData.images && rawData.images.urls && Array.isArray(rawData.images.urls)) {
                    return rawData.images.urls.join('\n');
                }
                return '';

            case '详情页文字':
                if (rawData.detailDescription) {
                    if (rawData.detailDescription.translated) {
                        return rawData.detailDescription.translated;
                    }
                    return rawData.detailDescription.original || rawData.detailDescription || '';
                }
                return rawData['详情页文字'] || '';

            case '尺码表':
                if (rawData.sizeChart) {
                    // 如果尺码表是对象，格式化为文本
                    if (typeof rawData.sizeChart === 'object' && rawData.sizeChart !== null) {
                        let chartText = '';

                        // 添加性别信息
                        if (rawData.sizeChart.gender) {
                            chartText += `性别: ${rawData.sizeChart.gender}\n`;
                        }

                        // 添加尺码表格
                        if (rawData.sizeChart.sizes && Array.isArray(rawData.sizeChart.sizes)) {
                            chartText += '尺码信息:\n';
                            rawData.sizeChart.sizes.forEach(size => {
                                if (typeof size === 'object') {
                                    chartText += `- ${size.size || ''}: ${size.height || ''} ${size.chest || ''} ${size.waist || ''}\n`;
                                }
                            });
                        }

                        // 添加原文信息
                        if (rawData.sizeChart.original) {
                            chartText += `\n详细尺码表:\n${rawData.sizeChart.original}`;
                        }

                        return chartText.trim();
                    }

                    // 如果是字符串，直接返回
                    return rawData.sizeChart;
                }
                return rawData['尺码表'] || '';

            default:
                return rawData[sourceField] || '';
        }
    }

    /**
     * 根据飞书列名找到对应的源字段
     */
    findSourceField(feishuColumn) {
        for (const [sourceField, targetColumn] of Object.entries(this.fieldMapping)) {
            if (targetColumn === feishuColumn) {
                return sourceField;
            }
        }
        return feishuColumn; // 如果没找到映射，返回原列名
    }

    /**
     * 格式化字段值
     */
    formatFieldValue(fieldName, value) {
        if (!value) return '';

        switch (fieldName) {
            case '价格':
                // 确保价格格式正确
                if (typeof value === 'string') {
                    return value.replace(/[¥￥,]/g, '').trim();
                }
                return String(value);

            case '图片数量':
                // 确保图片数量是数字
                const num = parseInt(value) || 0;
                return num.toString();

            case '颜色':
            case '尺码':
                // 如果是数组，转换为逗号分隔的字符串
                if (Array.isArray(value)) {
                    return value.join(', ');
                }
                return String(value);

            case '图片URL':
                // 如果是数组，转换为换行分隔的字符串
                if (Array.isArray(value)) {
                    return value.join('\n');
                }
                return String(value);

            default:
                return String(value);
        }
    }

    /**
     * 生成CSV文件用于飞书导入
     */
    async generateCSV(data, filename) {
        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('数据为空或格式不正确');
        }

        const csvFilePath = path.join(this.outputDir, filename);

        const csvWriter = csv.createObjectCsvWriter({
            path: csvFilePath,
            header: this.feishuColumns.map(col => ({id: col, title: col}))
        });

        // 异步处理所有产品数据
        const processedData = [];
        for (let i = 0; i < data.length; i++) {
            console.log(`处理产品 ${i + 1}/${data.length}...`);
            const processed = await this.processProduct(data[i]);
            processedData.push(processed);
        }

        await csvWriter.writeRecords(processedData);

        console.log(`✅ CSV文件已生成: ${csvFilePath}`);
        console.log(`📊 处理了 ${processedData.length} 个产品`);

        return csvFilePath;
    }

    /**
     * 生成JSON文件用于API调用
     */
    async generateJSON(data, filename) {
        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('数据为空或格式不正确');
        }

        const processedData = [];
        for (let i = 0; i < data.length; i++) {
            console.log(`处理产品 ${i + 1}/${data.length}...`);
            const processed = await this.processProduct(data[i]);
            processedData.push({
                fields: processed,
                // 保留原始数据以备查用
                rawData: data[i]
            });
        }

        const jsonFilePath = path.join(this.outputDir, filename);
        fs.writeFileSync(jsonFilePath, JSON.stringify({
            brand: 'Le Coq Sportif Golf',
            timestamp: new Date().toISOString(),
            totalProducts: processedData.length,
            products: processedData
        }, null, 2), 'utf8');

        console.log(`✅ JSON文件已生成: ${jsonFilePath}`);
        console.log(`📊 处理了 ${processedData.length} 个产品`);

        return jsonFilePath;
    }

    /**
     * 读取最新的产品数据文件
     */
    readLatestProductData() {
        const files = fs.readdirSync(this.inputDir)
            .filter(f => {
                // 查找包含产品数据的JSON文件
                return (f.includes('product_details') ||
                       f.includes('single_url_test') ||
                       f.includes('enhanced_detail') ||
                       f.includes('batch_feishu_results')) &&
                       f.endsWith('.json');
            })
            .sort((a, b) => {
                const statA = fs.statSync(path.join(this.inputDir, a));
                const statB = fs.statSync(path.join(this.inputDir, b));
                return statB.mtime - statA.mtime;
            });

        if (files.length === 0) {
            throw new Error('未找到产品数据文件');
        }

        const latestFile = files[0];
        const filePath = path.join(this.inputDir, latestFile);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

        console.log(`📂 读取数据文件: ${latestFile}`);

        // 从数据结构中提取产品数组
        if (data.products && Array.isArray(data.products)) {
            return data.products;
        } else if (data.data && Array.isArray(data.data)) {
            return data.data;
        } else if (Array.isArray(data)) {
            return data;
        } else if (data.data && data.data.data && Array.isArray(data.data.data)) {
            // 处理 single_url_test 的嵌套结构
            return data.data.data;
        } else if (data.data) {
            // 如果 data.data 是单个产品对象，转换为数组
            return [data.data];
        } else {
            throw new Error(`无法识别数据格式，文件: ${latestFile}`);
        }
    }

    /**
     * 执行完整的同步流程
     */
    async sync() {
        console.log('🚀 开始Le Coq Sportif Golf飞书数据同步...');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            // 1. 读取产品数据
            const productData = this.readLatestProductData();
            console.log(`📋 加载了 ${productData.length} 个产品数据`);

            // 2. 生成时间戳
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

            // 3. 生成CSV文件（用于飞书表格导入）
            const csvFile = `lecoqgolf_feishu_sync_${timestamp}.csv`;
            await this.generateCSV(productData, csvFile);

            // 4. 生成JSON文件（用于API调用）
            const jsonFile = `lecoqgolf_feishu_sync_${timestamp}.json`;
            await this.generateJSON(productData, jsonFile);

            // 5. 生成同步报告
            await this.generateSyncReport(productData, csvFile, jsonFile, timestamp);

            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('✅ Le Coq Sportif Golf飞书数据同步完成！');
            console.log('\n📋 生成的文件:');
            console.log(`   - CSV导入文件: ${csvFile}`);
            console.log(`   - JSON API文件: ${jsonFile}`);
            console.log(`   - 同步报告: lecoqgolf_sync_report_${timestamp}.txt`);

            return {
                csvFile,
                jsonFile,
                totalProducts: productData.length
            };

        } catch (error) {
            console.error('❌ 飞书同步失败:', error.message);
            throw error;
        }
    }

    /**
     * 生成同步报告
     */
    async generateSyncReport(productData, csvFile, jsonFile, timestamp) {
        const reportContent = `
Le Coq Sportif Golf 飞书数据同步报告
=====================================

同步时间: ${new Date().toLocaleString('zh-CN')}
产品数量: ${productData.length}

字段映射:
${this.feishuColumns.map(col => {
    const sourceField = this.findSourceField(col);
    return `  ${sourceField} → ${col}`;
}).join('\n')}

数据统计:
- 总产品数: ${productData.length}
- 包含价格的产品: ${productData.filter(p => p.价格).length}
- 包含图片的产品: ${productData.filter(p => p.图片总数 > 0).length}
- 有尺码信息的产品: ${productData.filter(p => p.尺码 && p.尺码.length > 0).length}

生成文件:
- CSV导入: ${csvFile}
- JSON API: ${jsonFile}

使用说明:
1. CSV导入: 将CSV文件直接导入飞书表格
2. API调用: 使用JSON文件通过飞书API写入数据
3. 字段对应: 确保飞书表格列名与生成的CSV列名一致
`;

        const reportFile = path.join(this.outputDir, `lecoqgolf_sync_report_${timestamp}.txt`);
        fs.writeFileSync(reportFile, reportContent, 'utf8');
        console.log(`📄 同步报告已生成: reportFile`);
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const sync = new LeCoqGolfFeishuSync();
    sync.sync().catch(error => {
        console.error('❌ 同步失败:', error);
        process.exit(1);
    });
}

module.exports = LeCoqGolfFeishuSync;