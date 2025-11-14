#!/usr/bin/env node

/**
 * 通用13字段处理器
 * 基于卡拉威完整的13字段规则系统
 * 接收phase1的原始数据，输出标准的13个飞书字段
 */

const { chromium } = require('playwright');

class Universal13FieldProcessor {
    constructor() {
        this.processor = null;
    }

    /**
     * 🎯 主入口：处理原始数据，生成13个飞书字段
     * 输入：phase1抓取的原始数据
     * 输出：13个飞书标准字段
     */
    async processRawData(scrapedData) {
        console.log('🔄 开始13字段处理...');
        console.log(`   品牌: ${scrapedData.brand}`);
        console.log(`   URL: ${scrapedData.url}`);

        try {
            // 创建卡拉威处理器的实例
            const CallawayProcessor = require('./callaway_13field_processor');
            this.processor = new CallawayProcessor();

            // 使用卡拉威的完整规则处理数据
            const processedData = await this.processor.scrapeDetailPage(scrapedData.url);

            console.log(`✅ 13字段处理完成`);
            return processedData;

        } catch (error) {
            console.error('❌ 13字段处理失败:', error.message);
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

        return missing.length === 0;
    }
}

module.exports = Universal13FieldProcessor;

// 如果直接运行此文件
if (require.main === module) {
    const processor = new Universal13FieldProcessor();
    console.log('✅ 通用13字段处理器已加载');
    console.log('📋 基于卡拉威完整规则系统');
    console.log('🎯 支持所有品牌的13字段处理');
}