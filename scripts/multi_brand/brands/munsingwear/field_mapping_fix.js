/**
 * 字段映射修复脚本
 * 将JS输出的中文键名转换为Python期望的英文键名
 */

const fs = require('fs');

// 完整的字段映射表
const FIELD_MAPPING = {
  // 基本信息字段
  '商品ID': 'productId',
  'product_id': 'productId', // 兼容字段
  'productName': 'productName',
  '商品标题': 'productName',
  'detailUrl': 'detailUrl',
  '商品链接': 'detailUrl',
  'detail_url': 'detailUrl', // 兼容字段

  // 品牌和分类
  'brand': 'Le Coq Sportif Golf', // 固定品牌
  '品牌名': 'brand',
  'gender': 'gender',
  '性别': 'gender',

  // 价格相关
  'price': 'price',
  '价格': 'price',
  'priceText': 'priceText', // 兼容格式
  'originalPrice': 'originalPrice',
  'currentPrice': 'currentPrice',

  // 产品属性
  'colors': 'colors',
  '颜色': 'colors',
  'sizes': 'sizes',
  '尺码': 'sizes',
  'sizeChart': 'sizeChart',
  '尺码表': 'sizeChart',

  // 图片相关 - 关键修复
  'imageUrls': 'imageUrls',
  '图片链接': 'imageUrls', // 🔥 关键修复
  'mainImage': 'mainImage',
  'images': 'images',
  'imagesMetadata': 'imagesMetadata',

  // 描述相关 - 关键修复
  'description': 'description',
  '详情页文字': 'description', // 🔥 关键修复
  'promotionText': 'promotionText',
  'productDescription': 'productDescription',

  // 其他字段
  'category': 'category',
  'sku': 'sku',
  'status': 'status',
  'scrapeInfo': 'scrapeInfo'
};

/**
 * 转换字段名
 */
function convertFieldNames(data) {
  const converted = {};

  for (const [jsKey, value] of Object.entries(data)) {
    // 检查是否有映射
    const pythonKey = FIELD_MAPPING[jsKey];

    if (pythonKey) {
      // 有映射，使用映射后的键名
      converted[pythonKey] = value;
    } else {
      // 没有映射，保持原键名
      converted[jsKey] = value;
    }
  }

  return converted;
}

/**
 * 转换产品数据为Python期望格式
 */
function convertToPythonFormat(data) {
  const result = {
    products: {}
  };

  // 处理每个产品
  for (const [productId, productData] of Object.entries(data)) {
    const convertedProduct = convertFieldNames(productData);

    // 确保有productId字段
    if (!convertedProduct.productId) {
      convertedProduct.productId = productId;
    }

    // 处理颜色数组 - 确保是字符串数组
    if (convertedProduct.colors && Array.isArray(convertedProduct.colors)) {
      convertedProduct.colors = convertedProduct.colors.map(color => {
        if (typeof color === 'object' && color.name) {
          return color.name;
        }
        return String(color);
      });
    }

    // 处理尺码数组 - 确保是字符串数组
    if (convertedProduct.sizes && Array.isArray(convertedProduct.sizes)) {
      convertedProduct.sizes = convertedProduct.sizes.map(size => String(size));
    }

    // 处理图片URL数组
    if (convertedProduct.imageUrls && Array.isArray(convertedProduct.imageUrls)) {
      convertedProduct.imageUrls = convertedProduct.imageUrls.map(url => String(url));
    }

    result.products[productId] = convertedProduct;
  }

  return result;
}

// 导出函数
module.exports = {
  convertFieldNames,
  convertToPythonFormat,
  FIELD_MAPPING
};