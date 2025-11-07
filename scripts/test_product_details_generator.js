#!/usr/bin/env node
/**
 * 测试产品详情数据生成器
 * 用于验证 product_details JSON 格式和后续处理流程
 */

const fs = require('fs').promises;
const path = require('path');

async function generateTestProductDetails() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5) + 'Z';
    const outputPath = path.join(__dirname, '../results', `product_details_test_${timestamp}.json`);
    
    // 生成测试数据，符合 scrape_product_detail.js 的输出格式
    const testData = {
        "scrapeInfo": {
            "timestamp": new Date().toISOString(),
            "version": "2.0.0",
            "url": "https://www.callawaygolf.jp/mens/tops/outer/C25215107_.html?pid=C25215107_1030_M",
            "productId": "C25215107",
            "totalVariants": 24,
            "totalImages": 15,
            "ossUploadCount": 15,
            "processingTimeMs": 45230
        },
        "product": {
            "productId": "C25215107",
            "title": "スターストレッチ2WAY中綿ブルゾン (MENS)",
            "category": "MENS > TOPS > OUTER",
            "brand": "Callaway",
            "description": "スターストレッチ素材を使用した2WAY仕様の中綿ブルゾン。軽量で保温性に優れ、ゴルフプレーから普段使いまで幅広くお使いいただけます。",
            "basePrice": 27500,
            "currency": "JPY",
            "priceText": "￥27,500 (税込)",
            "promotionText": "10%OFF",
            "isOnSale": true,
            "mainImageUrl": "https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_Mhknyh47yUN01XV7.jpg%3F1758202534&w=3000&q=75",
            "features": [
                "スターストレッチ素材",
                "2WAY仕様",
                "軽量",
                "保温性",
                "撥水加工"
            ],
            "materials": "表地：ポリエステル100%、裏地：ポリエステル100%、中綿：ポリエステル100%",
            "careInstructions": "洗濯機洗い可能（ネット使用）、タンブラー乾燥不可"
        },
        "variants": [
            {
                "variantId": "C25215107_1030_S",
                "productId": "C25215107",
                "color": "Navy",
                "colorName": "Navy",
                "colorCode": "1030",
                "size": "S",
                "sizeName": "S",
                "sizeCode": "S",
                "isAvailable": true,
                "stock": "在庫あり",
                "price": 27500,
                "sku": "C25215107-1030-S"
            },
            {
                "variantId": "C25215107_1030_M",
                "productId": "C25215107",
                "color": "Navy",
                "colorName": "Navy",
                "colorCode": "1030",
                "size": "M",
                "sizeName": "M",
                "sizeCode": "M",
                "isAvailable": true,
                "stock": "在庫あり",
                "price": 27500,
                "sku": "C25215107-1030-M"
            },
            {
                "variantId": "C25215107_1030_L",
                "productId": "C25215107",
                "color": "Navy",
                "colorName": "Navy",
                "colorCode": "1030",
                "size": "L",
                "sizeName": "L",
                "sizeCode": "L",
                "isAvailable": true,
                "stock": "在庫あり",
                "price": 27500,
                "sku": "C25215107-1030-L"
            },
            {
                "variantId": "C25215107_1030_XL",
                "productId": "C25215107",
                "color": "Navy",
                "colorName": "Navy",
                "colorCode": "1030",
                "size": "XL",
                "sizeName": "XL",
                "sizeCode": "XL",
                "isAvailable": false,
                "stock": "在庫切れ",
                "price": 27500,
                "sku": "C25215107-1030-XL"
            },
            {
                "variantId": "C25215107_2010_S",
                "productId": "C25215107",
                "color": "White",
                "colorName": "White",
                "colorCode": "2010",
                "size": "S",
                "sizeName": "S",
                "sizeCode": "S",
                "isAvailable": true,
                "stock": "在庫あり",
                "price": 27500,
                "sku": "C25215107-2010-S"
            },
            {
                "variantId": "C25215107_2010_M",
                "productId": "C25215107",
                "color": "White", 
                "colorName": "White",
                "colorCode": "2010",
                "size": "M",
                "sizeName": "M",
                "sizeCode": "M",
                "isAvailable": true,
                "stock": "在庫あり",
                "price": 27500,
                "sku": "C25215107-2010-M"
            }
        ],
        "images": {
            "product": [
                "https://cdn2.webdamdb.com/1280_Mhknyh47yUN01XV7.jpg?1758202534",
                "https://cdn2.webdamdb.com/1280_xyz123abc.jpg?1758202534"
            ],
            "variants": [
                {
                    "imageId": "main_1030",
                    "originalUrl": "https://cdn2.webdamdb.com/1280_Mhknyh47yUN01XV7.jpg?1758202534",
                    "imageType": "main",
                    "colorCode": "1030",
                    "variantId": "C25215107_1030",
                    "order": 1
                },
                {
                    "imageId": "detail_1030_01",
                    "originalUrl": "https://cdn2.webdamdb.com/1280_xyz123abc.jpg?1758202534",
                    "imageType": "detail",
                    "colorCode": "1030",
                    "variantId": "C25215107_1030",
                    "order": 2
                },
                {
                    "imageId": "main_2010",
                    "originalUrl": "https://cdn2.webdamdb.com/1280_DefGhi789Jkl.jpg?1758202534",
                    "imageType": "main",
                    "colorCode": "2010",
                    "variantId": "C25215107_2010",
                    "order": 1
                }
            ]
        },
        "ossLinks": {
            "productImages": [
                "https://callaway-images.oss-cn-hangzhou.aliyuncs.com/callaway/C25215107/main_image_001.jpg",
                "https://callaway-images.oss-cn-hangzhou.aliyuncs.com/callaway/C25215107/detail_image_001.jpg"
            ],
            "variantImages": {
                "C25215107_1030": [
                    "https://callaway-images.oss-cn-hangzhou.aliyuncs.com/callaway/C25215107/C25215107_1030/main_image_001.jpg",
                    "https://callaway-images.oss-cn-hangzhou.aliyuncs.com/callaway/C25215107/C25215107_1030/detail_image_001.jpg"
                ],
                "C25215107_2010": [
                    "https://callaway-images.oss-cn-hangzhou.aliyuncs.com/callaway/C25215107/C25215107_2010/main_image_001.jpg"
                ]
            }
        },
        "sizingChart": {
            "title": "サイズ表",
            "headers": ["サイズ", "胸囲(cm)", "着丈(cm)", "肩幅(cm)", "袖丈(cm)"],
            "rows": [
                ["S", "92", "65", "42", "61"],
                ["M", "96", "67", "44", "62"],
                ["L", "100", "69", "46", "63"],
                ["XL", "104", "71", "48", "64"]
            ]
        },
        "analytics": {
            "totalColors": 2,
            "totalSizes": 4,
            "totalVariants": 8,
            "availableVariants": 6,
            "stockStatus": "中等",
            "colorOptions": ["Navy", "White"],
            "sizeOptions": ["S", "M", "L", "XL"],
            "priceRange": {
                "min": 27500,
                "max": 27500,
                "currency": "JPY"
            }
        }
    };
    
    // 保存测试数据
    await fs.writeFile(outputPath, JSON.stringify(testData, null, 2), 'utf8');
    
    console.log(`✅ 测试产品详情数据已生成: ${outputPath}`);
    console.log(`📊 数据统计:`);
    console.log(`   - 产品ID: ${testData.product.productId}`);
    console.log(`   - 变体数量: ${testData.analytics.totalVariants}`);
    console.log(`   - 颜色选项: ${testData.analytics.colorOptions.join(', ')}`);
    console.log(`   - 尺码选项: ${testData.analytics.sizeOptions.join(', ')}`);
    console.log(`   - 图片数量: ${testData.images.length}`);
    console.log(`   - OSS链接数: ${testData.scrapeInfo.ossUploadCount}`);
    
    return outputPath;
}

if (require.main === module) {
    generateTestProductDetails()
        .then(outputPath => {
            console.log(`\n🎯 请使用以下命令验证数据格式:`);
            console.log(`jq '.product.title' ${outputPath}`);
            console.log(`jq '.variants | length' ${outputPath}`);
            console.log(`jq '.images[0].ossUrl' ${outputPath}`);
        })
        .catch(error => {
            console.error('❌ 生成测试数据失败:', error);
            process.exit(1);
        });
}

module.exports = { generateTestProductDetails };