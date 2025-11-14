#!/usr/bin/env node

/**
 * 测试单个商品详情页数据同步到飞书
 */

const DetailPageScraper = require('./detail_page_scraper');
const fs = require('fs');
const path = require('path');

class FeishuSyncTester {
    constructor() {
        this.testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';
    }

    async testSingleSync() {
        console.log('🚀 开始测试单个商品飞书同步...');
        console.log('📱 测试URL:', this.testUrl);

        try {
            // 1. 抓取详情页数据
            console.log('\n📊 第一步：抓取详情页数据...');
            const scraper = new DetailPageScraper();
            const detailData = await scraper.scrapeDetailPage(this.testUrl);

            console.log('✅ 详情页数据抓取完成');

            // 2. 转换为飞书格式
            console.log('\n🔄 第二步：转换为飞书数据格式...');
            const feishuData = this.convertToFeishuFormat(detailData);
            console.log('✅ 飞书格式转换完成');

            // 3. 显示预览数据
            console.log('\n📋 第三步：飞书数据预览...');
            this.displayFeishuPreview(feishuData);

            // 4. 保存测试数据
            console.log('\n💾 第四步：保存测试数据...');
            this.saveTestData(detailData, feishuData);

            console.log('\n✅ 测试完成！请检查以上数据格式是否正确');

            return {
                detailData: detailData,
                feishuData: feishuData
            };

        } catch (error) {
            console.error('❌ 测试失败:', error.message);
            throw error;
        }
    }

    convertToFeishuFormat(detailData) {
        const feishuRecord = {
            // 基础信息
            '商品标题': detailData.title || '',
            '品牌': detailData.brand || '',
            '商品编号': detailData.productCode || '',
            '性别': detailData.gender || '',
            '价格': detailData.price || '',
            '详情页链接': detailData.url || '',

            // 分类信息
            '一级分类': detailData.categories[0] || '',
            '二级分类': detailData.categories[1] || '',
            '三级分类': detailData.categories[2] || '',
            '四级分类': detailData.categories[3] || '',
            '五级分类': detailData.categories[4] || '',

            // 产品规格
            '颜色选项': detailData.colors.map(c => c.name).join(', ') || '',
            '颜色数量': detailData.colors.length || 0,
            '首个颜色': detailData.colors.find(c => c.isFirstColor)?.name || '',
            '尺寸选项': detailData.sizes.map(s => s.size).join(', ') || '',
            '尺寸数量': detailData.sizes.length || 0,

            // 库存信息
            '总尺码数': detailData.inventoryStats.totalSizes || 0,
            '有库存尺码': detailData.inventoryStats.availableSizes || 0,
            '缺货尺码': detailData.inventoryStats.soldOutSizes || 0,
            '库存率(%)': detailData.inventoryStats.stockPercentage || 0,

            // 图片信息
            '图片总数': detailData.images.total || 0,
            '首个颜色图片数': detailData.images.firstColorImages.length || 0,
            '其他颜色图片数': detailData.images.otherColorsImages.length || 0,
            '主要图片链接': detailData.images.firstColorImages[0] || '',
            '所有图片链接': detailData.images.urls.join('\n') || '',

            // 功能特性
            '核心功能': detailData.description.features.slice(0, 3).join(', ') || '',
            '材质信息': detailData.description.materials.join(', ') || '',
            '所有功能': detailData.description.features.join('\n') || '',

            // 时间戳
            '抓取时间': detailData.scrapedAt || new Date().toISOString(),
            '更新时间': new Date().toISOString(),

            // 系统信息
            '数据来源': 'lecoqgolf',
            '状态': '待同步'
        };

        return feishuRecord;
    }

    displayFeishuPreview(feishuData) {
        console.log('\n=== 📊 飞书数据预览 ===\n');

        const displayFields = [
            '商品标题', '品牌', '商品编号', '性别', '价格',
            '颜色选项', '颜色数量', '尺寸选项', '尺寸数量',
            '库存率(%)', '图片总数', '主要图片链接', '核心功能'
        ];

        displayFields.forEach(field => {
            const value = feishuData[field];
            if (value && value.length > 100) {
                console.log(`${field}: ${value.substring(0, 100)}...`);
            } else {
                console.log(`${field}: ${value || '空'}`);
            }
        });

        console.log('\n📊 完整字段统计:');
        console.log(`总字段数: ${Object.keys(feishuData).length}个`);
        console.log(`有值字段数: ${Object.values(feishuData).filter(v => v && v.toString().trim()).length}个`);
    }

    saveTestData(detailData, feishuData) {
        // 确保输出目录存在
        const outputDir = './golf_content/lecoqgolf/';
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

        // 保存原始详情页数据
        const detailFile = `${outputDir}feishu_test_detail_${timestamp}.json`;
        fs.writeFileSync(detailFile, JSON.stringify(detailData, null, 2));
        console.log(`💾 详情页数据已保存: ${detailFile}`);

        // 保存飞书格式数据
        const feishuFile = `${outputDir}feishu_test_sync_${timestamp}.json`;
        fs.writeFileSync(feishuFile, JSON.stringify({
            records: [feishuData],
            total: 1,
            timestamp: new Date().toISOString(),
            brand: 'lecoqgolf'
        }, null, 2));
        console.log(`💾 飞书格式数据已保存: ${feishuFile}`);

        // 生成CSV预览（便于Excel查看）
        const csvFile = `${outputDir}feishu_test_preview_${timestamp}.csv`;
        const csvHeaders = Object.keys(feishuData).join(',');
        const csvValues = Object.values(feishuData).map(v => `"${v}"`).join(',');
        fs.writeFileSync(csvFile, `${csvHeaders}\n${csvValues}`);
        console.log(`💾 CSV预览数据已保存: ${csvFile}`);

        return {
            detailFile,
            feishuFile,
            csvFile
        };
    }
}

// 运行测试
if (require.main === module) {
    const tester = new FeishuSyncTester();

    tester.testSingleSync()
        .then(results => {
            console.log('\n🎉 测试成功完成！');
            console.log('\n📝 请检查以下文件：');
            console.log('- 详情页原始数据');
            console.log('- 飞书格式数据');
            console.log('- CSV预览文件');
        })
        .catch(error => {
            console.error('❌ 测试失败:', error.message);
            process.exit(1);
        });
}

module.exports = FeishuSyncTester;