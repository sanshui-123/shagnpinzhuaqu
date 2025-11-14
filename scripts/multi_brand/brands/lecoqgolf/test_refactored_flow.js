#!/usr/bin/env node

/**
 * 测试重构后的两阶段流程
 * 阶段1: data_scraper.js - 纯数据抓取
 * 阶段2: universal_field_processor.js - 统一处理
 */

const LeCoqGolfDataScraper = require('./data_scraper');
const UniversalFieldProcessor = require('../../shared/universal_field_processor');
const fs = require('fs');
const path = require('path');

class RefactoredFlowTester {
    constructor() {
        this.scraper = new LeCoqGolfDataScraper();
        this.processor = new UniversalFieldProcessor();
        this.outputDir = './golf_content/lecoqgolf';
        this.ensureOutputDir();
    }

    ensureOutputDir() {
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
    }

    /**
     * 测试完整的两阶段流程
     */
    async testCompleteFlow(url) {
        console.log('🚀 开始测试重构后的两阶段流程');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`🔍 测试URL: ${url}`);

        try {
            // 阶段1: 数据抓取
            console.log('\n📋 阶段1: 数据抓取...');
            const scrapedData = await this.scraper.scrapeProductData(url);
            console.log(`   ✅ 抓取完成，品牌: ${scrapedData.brand}`);
            console.log(`   📊 抓取字段数: ${Object.keys(scrapedData.rawData).length}`);

            // 阶段2: 数据处理
            console.log('\n⚙️ 阶段2: 数据处理...');
            const processedData = await this.processor.processProduct(scrapedData);
            console.log(`   ✅ 处理完成，生成13个飞书字段`);

            // 显示结果
            console.log('\n📊 处理结果:');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

            // 基本信息
            console.log(`商品链接: ${processedData['商品链接']}`);
            console.log(`商品ID: ${processedData['商品ID']}`);
            console.log(`品牌名: ${processedData['品牌名']}`);
            console.log(`价格: ${processedData['价格']}`);

            // 智能处理字段
            console.log(`商品标题: ${processedData['商品标题']} (${processedData['商品标题'].length}字)`);
            console.log(`性别: ${processedData['性别']}`);
            console.log(`衣服分类: ${processedData['衣服分类']}`);

            // 图片处理
            console.log(`图片总数: ${processedData['图片总数']}`);
            console.log(`图片链接: ${processedData['图片链接'].split('\n').length}个链接`);

            // 尺码和颜色
            console.log(`颜色: ${processedData['颜色']}`);
            console.log(`尺码: ${processedData['尺码']}`);

            // 翻译和格式化
            console.log(`详情页文字: ${processedData['详情页文字'] ? '已翻译' : '未处理'}`);
            console.log(`尺码表: ${processedData['尺码表'] ? '已格式化' : '未处理'}`);

            // 调试信息
            if (processedData._debug) {
                console.log('\n🔧 调试信息:');
                console.log(`   品牌配置: ${processedData._debug.brand.shortName}`);
                console.log(`   标题验证: ${processedData._debug.titleValidation}`);
                console.log(`   图片数量: ${processedData._debug.imageCount}`);
            }

            // 保存结果
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const resultFile = path.join(this.outputDir, `refactored_test_${timestamp}.json`);
            fs.writeFileSync(resultFile, JSON.stringify({
                testType: 'refactored_flow_test',
                timestamp: timestamp,
                url: url,
                stage1: { scraped: scrapedData },
                stage2: { processed: processedData }
            }, null, 2), 'utf8');

            console.log(`\n💾 测试结果已保存: ${resultFile}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('✅ 重构流程测试成功！');

            return processedData;

        } catch (error) {
            console.error('❌ 测试失败:', error.message);
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

        const missing = requiredFields.filter(field => !data[field]);
        const empty = requiredFields.filter(field => data[field] === '' || data[field] === null || data[field] === undefined);

        console.log('\n📋 13字段验证:');
        console.log(`   ✅ 完整字段: ${requiredFields.length - missing.length}/${requiredFields.length}`);
        console.log(`   ✅ 非空字段: ${requiredFields.length - empty.length}/${requiredFields.length}`);

        if (missing.length > 0) {
            console.log(`   ❌ 缺失字段: ${missing.join(', ')}`);
        }
        if (empty.length > 0) {
            console.log(`   ⚠️ 空字段: ${empty.join(', ')}`);
        }

        return missing.length === 0 && empty.length <= 2; // 允许少数空字段
    }
}

module.exports = RefactoredFlowTester;

// 如果直接运行此文件
if (require.main === module) {
    const tester = new RefactoredFlowTester();
    const testUrl = process.argv[2] || 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';

    tester.testCompleteFlow(testUrl)
        .then(data => {
            const isValid = tester.validate13Fields(data);
            if (isValid) {
                console.log('\n🎉 重构成功！13个字段验证通过！');
            } else {
                console.log('\n⚠️ 字段验证有问题，需要检查');
            }
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}