/**
 * 配置验证器
 * 验证品牌配置的完整性和正确性
 */

class ConfigValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
    }

    /**
     * 验证品牌配置
     */
    validateBrandConfig(brandName, config) {
        this.errors = [];
        this.warnings = [];

        // 验证必需字段
        this.validateRequiredFields(brandName, config);

        // 验证URL格式
        this.validateUrls(brandName, config);

        // 验证选择器
        this.validateSelectors(brandName, config);

        // 验证调度配置
        this.validateSchedule(brandName, config);

        // 验证输出配置
        this.validateOutput(brandName, config);

        return {
            valid: this.errors.length === 0,
            errors: this.errors,
            warnings: this.warnings
        };
    }

    /**
     * 验证必需字段
     */
    validateRequiredFields(brandName, config) {
        const requiredFields = ['name', 'domain', 'baseUrl', 'enabled', 'schedule', 'scraper', 'selectors'];

        requiredFields.forEach(field => {
            if (!config[field]) {
                this.errors.push(`品牌 ${brandName} 缺少必需字段: ${field}`);
            }
        });

        // 验证嵌套对象
        if (config.schedule && !config.schedule.interval) {
            this.errors.push(`品牌 ${brandName} schedule 缺少 interval 字段`);
        }

        if (config.scraper && !config.scraper.type) {
            this.errors.push(`品牌 ${brandName} scraper 缺少 type 字段`);
        }

        if (config.selectors && !config.selectors.productGrid) {
            this.errors.push(`品牌 ${brandName} selectors 缺少 productGrid 字段`);
        }
    }

    /**
     * 验证URL格式
     */
    validateUrls(brandName, config) {
        if (config.baseUrl && !this.isValidUrl(config.baseUrl)) {
            this.errors.push(`品牌 ${brandName} baseUrl 格式无效: ${config.baseUrl}`);
        }

        if (config.domain && !this.isValidDomain(config.domain)) {
            this.errors.push(`品牌 ${brandName} domain 格式无效: ${config.domain}`);
        }

        // 检查baseUrl和domain是否匹配
        if (config.baseUrl && config.domain) {
            const baseUrlDomain = new URL(config.baseUrl).hostname;
            if (baseUrlDomain !== config.domain) {
                this.warnings.push(`品牌 ${brandName} baseUrl 域名 (${baseUrlDomain}) 与 domain (${config.domain}) 不匹配`);
            }
        }
    }

    /**
     * 验证选择器
     */
    validateSelectors(brandName, config) {
        if (!config.selectors) return;

        const requiredSelectors = ['productGrid', 'productName', 'productUrl', 'productPrice'];

        requiredSelectors.forEach(selector => {
            if (!config.selectors[selector]) {
                this.errors.push(`品牌 ${brandName} 缺少选择器: ${selector}`);
            }
        });

        // 验证选择器语法
        if (config.selectors.productGrid) {
            this.validateSelectorSyntax(brandName, 'productGrid', config.selectors.productGrid);
        }

        // 检查选择器是否过于通用
        if (config.selectors.productGrid && config.selectors.productGrid.includes('*')) {
            this.warnings.push(`品牌 ${brandName} productGrid 选择器过于通用，可能影响性能`);
        }
    }

    /**
     * 验证选择器语法
     */
    validateSelectorSyntax(brandName, selectorName, selector) {
        try {
            // 简单的CSS选择器语法检查
            if (typeof selector === 'string') {
                document.querySelector(selector);
            } else if (Array.isArray(selector)) {
                selector.forEach(s => {
                    if (typeof s === 'string') {
                        document.querySelector(s);
                    }
                });
            }
        } catch (error) {
            this.errors.push(`品牌 ${brandName} 选择器 ${selectorName} 语法无效: ${selector}`);
        }
    }

    /**
     * 验证调度配置
     */
    validateSchedule(brandName, config) {
        if (!config.schedule) return;

        const validIntervals = ['10-days', 'daily', 'weekly', 'monthly'];
        if (config.schedule.interval && !validIntervals.includes(config.schedule.interval)) {
            this.errors.push(`品牌 ${brandName} schedule.interval 无效: ${config.schedule.interval}`);
        }

        if (config.schedule.dayOfMonth && (config.schedule.dayOfMonth < 1 || config.schedule.dayOfMonth > 31)) {
            this.errors.push(`品牌 ${brandName} schedule.dayOfMonth 无效: ${config.schedule.dayOfMonth}`);
        }
    }

    /**
     * 验证输出配置
     */
    validateOutput(brandName, config) {
        if (!config.output) return;

        const validFormats = ['json', 'csv', 'xml'];
        if (config.output.format && !validFormats.includes(config.output.format)) {
            this.warnings.push(`品牌 ${brandName} output.format 建议使用标准格式: ${validFormats.join(', ')}`);
        }

        if (config.output.path && config.output.path.includes('..')) {
            this.errors.push(`品牌 ${brandName} output.path 包含不安全路径: ${config.output.path}`);
        }
    }

    /**
     * 验证URL有效性
     */
    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * 验证域名有效性
     */
    isValidDomain(domain) {
        const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*$/;
        return domainRegex.test(domain);
    }

    /**
     * 验证所有品牌配置
     */
    async validateAllBrands(configManager) {
        const brands = await configManager.getAllBrands();
        const results = {};

        for (const brand of brands) {
            const config = await configManager.getBrandConfig(brand);
            if (config) {
                results[brand] = this.validateBrandConfig(brand, config);
            } else {
                results[brand] = {
                    valid: false,
                    errors: [`品牌 ${brand} 配置不存在`],
                    warnings: []
                };
            }
        }

        return results;
    }

    /**
     * 生成验证报告
     */
    generateReport(validationResults) {
        const totalBrands = Object.keys(validationResults).length;
        const validBrands = Object.values(validationResults).filter(r => r.valid).length;
        const totalErrors = Object.values(validationResults).reduce((sum, r) => sum + r.errors.length, 0);
        const totalWarnings = Object.values(validationResults).reduce((sum, r) => sum + r.warnings.length, 0);

        return {
            summary: {
                total: totalBrands,
                valid: validBrands,
                invalid: totalBrands - validBrands,
                errorCount: totalErrors,
                warningCount: totalWarnings,
                healthPercentage: Math.round((validBrands / totalBrands) * 100)
            },
            details: validationResults,
            recommendations: this.generateRecommendations(validationResults)
        };
    }

    /**
     * 生成改进建议
     */
    generateRecommendations(validationResults) {
        const recommendations = [];

        const commonErrors = {};
        const commonWarnings = {};

        // 统计常见错误
        Object.entries(validationResults).forEach(([brand, result]) => {
            result.errors.forEach(error => {
                const key = error.split(':').pop().trim();
                commonErrors[key] = (commonErrors[key] || 0) + 1;
            });

            result.warnings.forEach(warning => {
                const key = warning.split(':').pop().trim();
                commonWarnings[key] = (commonWarnings[key] || 0) + 1;
            });
        });

        // 生成建议
        if (commonErrors['缺少必需字段: selectors'] > 0) {
            recommendations.push('多个品牌缺少选择器配置，建议检查配置完整性');
        }

        if (commonErrors['baseUrl 格式无效'] > 0) {
            recommendations.push('检查品牌URL格式，确保使用完整的URL（包含协议）');
        }

        if (commonWarnings['选择器过于通用'] > 0) {
            recommendations.push('优化产品选择器，使用更具体的CSS选择器以提高准确性');
        }

        return recommendations;
    }
}

module.exports = ConfigValidator;