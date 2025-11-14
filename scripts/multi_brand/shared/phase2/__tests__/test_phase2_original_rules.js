#!/usr/bin/env node

/**
 * Phase 2 原版规则系统测试
 * 对比测试数据，验证与原系统的一致性
 */

const Feishu13FieldsAssembler = require('../feishu_13_fields_assembler');
const fs = require('fs');
const path = require('path');

class Phase2OriginalRulesTester {
    constructor() {
        this.assembler = new Feishu13FieldsAssembler();
        this.testDataPath = path.join(__dirname, 'fixtures', 'test_data.json');
        this.outputPath = path.join(__dirname, 'reports', 'phase2_test_results.json');
    }

    /**
     * 运行完整测试
     */
    async runFullTest() {
        console.log('🧪 开始Phase 2原版规则系统测试');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        try {
            // 确保输出目录存在
            const reportsDir = path.dirname(this.outputPath);
            if (!fs.existsSync(reportsDir)) {
                fs.mkdirSync(reportsDir, { recursive: true });
            }

            // 读取测试数据
            const testDataList = this.loadTestData();
            console.log(`📊 加载测试数据: ${testDataList.length} 条`);

            // 批量处理
            const results = await this.assembler.batchProcess(testDataList);

            // 生成对比报告
            const report = this.generateReport(results);

            // 保存结果
            this.saveResults(report);

            // 显示结果
            this.displayResults(report);

            return report;

        } catch (error) {
            console.error('❌ 测试失败:', error.message);
            throw error;
        }
    }

    /**
     * 加载测试数据
     */
    loadTestData() {
        // 如果有预存测试数据文件，直接读取
        if (fs.existsSync(this.testDataPath)) {
            const data = JSON.parse(fs.readFileSync(this.testDataPath, 'utf8'));
            return Array.isArray(data) ? data : [data];
        }

        // 否则创建基于现有测试数据的测试用例
        return this.createTestFixtures();
    }

    /**
     * 创建测试数据
     */
    createTestFixtures() {
        console.log('📝 创建测试数据...');

        // 基于Le Coq的现有测试数据创建
        const lecoqgolfDataPath = '../../../brands/lecoqgolf/golf_content/lecoqgolf/single_url_test_2025-11-13T03-23-50-402Z.json';
        const testDataList = [];

        if (fs.existsSync(path.join(__dirname, lecoqgolfDataPath))) {
            const testData = JSON.parse(fs.readFileSync(path.join(__dirname, lecoqgolfDataPath), 'utf8'));

            // 转换为Phase 1格式
            const scrapedData = {
                brand: 'le coq sportif golf',
                url: testData.sourceUrl,
                rawData: this.convertToRawData(testData.data)
            };

            testDataList.push(scrapedData);
            console.log(`✅ 创建测试数据: 1条 (Le Coq)`);
        } else {
            // 创建默认测试数据
            const defaultData = {
                brand: 'le coq sportif golf',
                url: 'https://example.com/test',
                rawData: {
                    title: 'テスト商品',
                    images: {
                        all: [
                            { src: 'https://example.com/img1.jpg' },
                            { src: 'https://example.com/img2.jpg' }
                        ]
                    },
                    colors: [
                        { name: 'ネイビー' },
                        { name: 'ブラック' }
                    ],
                    sizes: [
                        { size: 'S' },
                        { size: 'M' },
                        { size: 'L' }
                    ],
                    sizeChart: {
                        html: '<table><tr><td>サイズ</td></tr></table>',
                        text: 'サイズ表'
                    },
                    description: '商品説明文',
                    price: '￥19,800',
                    productCode: 'LG5FWB50M'
                }
            };
            testDataList.push(defaultData);
            console.log(`✅ 创建默认测试数据: 1条`);
        }

        // 保存测试数据
        fs.writeFileSync(this.testDataPath, JSON.stringify(testDataList, null, 2), 'utf8');
        return testDataList;
    }

    /**
     * 转换数据格式
     */
    convertToRawData(oldData) {
        return {
            title: oldData['商品标题']?.original || oldData['商品标题'] || '',
            url: oldData['商品链接'] || '',
            images: {
                all: oldData['图片链接'] ?
                    (Array.isArray(oldData['图片链接']) ?
                        oldData['图片链接'].map(url => ({ src: url })) :
                        [oldData['图片链接']].filter(Boolean).map(url => ({ src: url }))) : []
            },
            colors: Array.isArray(oldData['颜色']) ?
                oldData['颜色'].map(c =>
                    typeof c === 'object' ? c : { name: c, selected: false }) : [],
            sizes: Array.isArray(oldData['尺码']) ?
                oldData['尺码'].map(s =>
                    typeof s === 'object' ? s : { size: s, available: true }) : [],
            sizeChart: oldData['尺码表'] || {
                text: '',
                html: ''
            },
            description: oldData['详情页文字']?.original || oldData['详情页文字'] || '',
            price: oldData['价格'] || '',
            productCode: oldData['商品ID'] || ''
        };
    }

    /**
     * 生成对比报告
     */
    generateReport(results) {
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => r.failed);

        const report = {
            timestamp: new Date().toISOString(),
            totalTests: results.length,
            successful: successful.length,
            failed: failed.length,
            successRate: (successful.length / results.length * 100).toFixed(2) + '%',
            results: results,
            summary: {
                fieldCompleteness: this.analyzeFieldCompleteness(successful),
                titleGeneration: this.analyzeTitleGeneration(successful),
                errors: failed.map(f => f.error)
            }
        };

        return report;
    }

    /**
     * 分析字段完整性
     */
    analyzeFieldCompleteness(successfulResults) {
        const requiredFields = [
            '商品链接', '商品ID', '商品标题', '品牌名', '价格',
            '性别', '衣服分类', '图片总数', '图片链接',
            '颜色', '尺码', '详情页文字', '尺码表'
        ];

        const fieldStats = {};
        requiredFields.forEach(field => {
            fieldStats[field] = {
                present: 0,
                empty: 0,
                total: successfulResults.length
            };
        });

        successfulResults.forEach(result => {
            requiredFields.forEach(field => {
                const value = result.data[field];
                if (value !== undefined && value !== null) {
                    fieldStats[field].present++;
                }
                if (!value || (typeof value === 'string' && value.trim() === '')) {
                    fieldStats[field].empty++;
                }
            });
        });

        return fieldStats;
    }

    /**
     * 分析标题生成
     */
    analyzeTitleGeneration(successfulResults) {
        const titles = successfulResults.map(r => r.data['商品标题']).filter(Boolean);
        return {
            generated: titles.length,
            avgLength: titles.length > 0 ? Math.round(titles.reduce((sum, t) => sum + t.length, 0) / titles.length) : 0,
            samples: titles.slice(0, 3)
        };
    }

    /**
     * 保存结果
     */
    saveResults(report) {
        fs.writeFileSync(this.outputPath, JSON.stringify(report, null, 2), 'utf8');
        console.log(`💾 测试结果已保存: ${this.outputPath}`);
    }

    /**
     * 显示结果
     */
    displayResults(report) {
        console.log('\n📊 测试结果报告');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`📈 总测试数: ${report.totalTests}`);
        console.log(`✅ 成功: ${report.successful}`);
        console.log(`❌ 失败: ${report.failed}`);
        console.log(`📊 成功率: ${report.successRate}`);

        if (report.summary.fieldCompleteness) {
            console.log('\n📋 字段完整性分析:');
            Object.entries(report.summary.fieldCompleteness).forEach(([field, stats]) => {
                const rate = ((stats.present - stats.empty) / stats.total * 100).toFixed(1);
                console.log(`   ${field}: ${stats.present}/${stats.total} (${rate}%)`);
            });
        }

        if (report.summary.titleGeneration) {
            console.log('\n📝 标题生成分析:');
            console.log(`   生成数量: ${report.summary.titleGeneration.generated}`);
            console.log(`   平均长度: ${report.summary.titleGeneration.avgLength}字符`);
        }

        if (report.summary.errors.length > 0) {
            console.log('\n❌ 错误统计:');
            report.summary.errors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error}`);
            });
        }
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const tester = new Phase2OriginalRulesTester();
    tester.runFullTest()
        .then(() => {
            console.log('\n🎉 Phase 2原版规则系统测试完成！');
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}

module.exports = Phase2OriginalRulesTester;