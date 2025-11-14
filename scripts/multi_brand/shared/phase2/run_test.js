#!/usr/bin/env node

/**
 * Phase 2 测试运行器
 * 一键测试原版规则系统
 */

const Phase2OriginalRulesTester = require('./__tests__/test_phase2_original_rules');

console.log('🚀 启动Phase 2原版规则系统测试');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

const tester = new Phase2OriginalRulesTester();

tester.runFullTest()
    .then(() => {
        console.log('\n✅ 所有测试完成！');
        console.log('📊 详细报告请查看: __tests__/reports/phase2_test_results.json');
    })
    .catch(error => {
        console.error('\n❌ 测试失败:', error.message);
        console.error('🔧 请检查Python环境和依赖');
        process.exit(1);
    });