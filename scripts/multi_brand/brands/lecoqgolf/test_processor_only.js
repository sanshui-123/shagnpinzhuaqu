#!/usr/bin/env node

/**
 * 测试通用处理器 (阶段2)
 * 使用已有的测试数据，只测试处理器部分
 */

const Universal13FieldProcessor = require('../../shared/universal_13field_processor');
const fs = require('fs');
const path = require('path');

class ProcessorTester {
    constructor() {
        this.processor = new Universal13FieldProcessor();
    }

    /**
     * 测试通用处理器 (使用卡拉威完整规则)
     */
    async testProcessor(scrapedData) {
        console.log('🧪 测试13字段处理器 (卡拉威完整规则)');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            console.log(`🔍 输入数据品牌: ${scrapedData.brand}`);

            // 使用卡拉威完整规则处理数据
            const processedData = await this.processor.processRawData(scrapedData);
            console.log(`   ✅ 卡拉威规则处理完成`);

            // 显示结果
            console.log('\n📊 处理结果 (13个飞书字段):');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // 必填的13个字段
            const feishuFields = [
                '商品链接', '商品ID', '商品标题', '品牌名', '价格',
                '性别', '衣服分类', '图片总数', '图片链接',
                '颜色', '尺码', '详情页文字', '尺码表'
            ];

            for (const field of feishuFields) {
                const value = processedData[field];
                const status = value ? '✅' : '❌';

                // 特殊处理复杂数据类型
                let displayValue;
                if (field === '商品标题' && typeof value === 'object' && value.translated) {
                    displayValue = value.translated.length > 50
                        ? value.translated.substring(0, 50) + '...'
                        : value.translated;
                } else if (field === '图片链接' && Array.isArray(value)) {
                    displayValue = `${value.length}个链接`;
                } else if (field === '颜色' && Array.isArray(value)) {
                    displayValue = value.map(c => c.name || c).join(', ').substring(0, 50) + (value.length > 3 ? '...' : '');
                } else if (field === '尺码' && Array.isArray(value)) {
                    displayValue = value.map(s => s.size || s).join(', ');
                } else if (field === '尺码表' && typeof value === 'object' && value.translatedText) {
                    displayValue = value.translatedText.length > 50
                        ? value.translatedText.substring(0, 50) + '...'
                        : value.translatedText;
                } else if (field === '详情页文字' && typeof value === 'object' && value.translated) {
                    displayValue = value.translated.length > 50
                        ? value.translated.substring(0, 50) + '...'
                        : value.translated;
                } else {
                    displayValue = typeof value === 'string' && value.length > 50
                        ? value.substring(0, 50) + '...'
                        : value || '(空)';
                }

                console.log(`${status} ${field}: ${displayValue}`);
            }

            // 验证13字段完整性
            this.validate13Fields(processedData);

            return processedData;

        } catch (error) {
            console.error('❌ 处理器测试失败:', error.message);
            throw error;
        }
    }

    /**
     * 验证13个字段完整性
     */
    validate13Fields(data) {
        const requiredFields = [
            '商品链接', '商品ID', '商品标题', '品牌名', '价格',
            '性别', '衣服分类', '图片总数', '图片链接',
            '颜色', '尺码', '详情页文字', '尺码表'
        ];

        const missing = requiredFields.filter(field => !(field in data));
        const empty = requiredFields.filter(field => !data[field] || data[field] === '');

        console.log('\n📋 13字段验证:');
        console.log(`   ✅ 字段存在: ${requiredFields.length - missing.length}/${requiredFields.length}`);
        console.log(`   ✅ 非空字段: ${requiredFields.length - empty.length}/${requiredFields.length}`);

        if (missing.length > 0) {
            console.log(`   ❌ 缺失字段: ${missing.join(', ')}`);
        }
        if (empty.length > 0) {
            console.log(`   ⚠️ 空字段: ${empty.join(', ')}`);
        }

        const success = missing.length === 0 && empty.length <= 2; // 允许少数空字段
        if (success) {
            console.log('🎉 13字段验证通过！');
        } else {
            console.log('⚠️ 字段验证有问题');
        }

        return success;
    }

    /**
     * 测试已有数据
     */
    async testWithExistingData() {
        // 使用之前的测试数据
        const testDataPath = './golf_content/lecoqgolf/single_url_test_2025-11-13T03-23-50-402Z.json';

        if (!fs.existsSync(testDataPath)) {
            console.log('❌ 找不到测试数据文件，请先运行原始抓取器生成数据');
            return;
        }

        console.log(`📂 使用现有测试数据: ${testDataPath}`);
        const testData = JSON.parse(fs.readFileSync(testDataPath, 'utf8'));

        // 转换为新的数据格式
        const scrapedData = {
            brand: 'le coq sportif golf',
            url: testData.sourceUrl || '',
            rawData: this.convertOldData(testData.data)
        };

        return await this.testProcessor(scrapedData);
    }

    /**
     * 转换旧数据格式为新格式
     */
    convertOldData(oldData) {
        return {
            title: oldData.title?.original || oldData.title || '',
            url: oldData.url || oldData['商品链接'] || '',
            productCode: oldData['商品ID'] || '',
            originalPrice: oldData['价格'] || '',
            brand: oldData['品牌名'] || '',

            // 处理图片数据
            images: {
                all: oldData['图片链接'] ?
                    (Array.isArray(oldData['图片链接']) ?
                        oldData['图片链接'].map(url => ({ src: url })) :
                        [oldData['图片链接']].filter(Boolean).map(url => ({ src: url }))) : [],
                productImages: oldData['图片链接'] || []
            },

            // 处理颜色数据
            colors: Array.isArray(oldData['颜色']) ?
                oldData['颜色'].map(c =>
                    typeof c === 'object' ? c : { name: c, selected: false }
                ) : [],

            // 处理尺码数据
            sizes: Array.isArray(oldData['尺码']) ?
                oldData['尺码'].map(s =>
                    typeof s === 'object' ? s : { size: s, available: true }
                ) : [],

            // 处理尺码表数据 - 保留原始对象结构
            sizeChart: oldData['尺码表'] || {
                text: '',
                html: ''
            },

            // 描述信息
            description: oldData['详情页文字']?.original || oldData['详情页文字'] || ''
        };
    }
}

module.exports = ProcessorTester;

// 如果直接运行此文件
if (require.main === module) {
    const tester = new ProcessorTester();
    tester.testWithExistingData()
        .then(() => {
            console.log('\n🎉 通用处理器测试完成！');
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}