#!/usr/bin/env node

/**
 * Callaway 分类列表复用器（使用已有抓取文件）
 *
 * 站点结构改变、在线抓取不可用时，直接复用仓库中存量的
 * callaway_products_*.json，转换/复制到 results 目录供后续流程使用。
 *
 * 输入：--category 标识（例如 mens_all / womens_all），选取最新的 callaway_products_*.json
 * 输出：results/callaway_products_<category>_<timestamp>.json
 */

const fs = require('fs');
const path = require('path');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const argv = yargs(hideBin(process.argv))
  .option('category', {
    alias: 'c',
    type: 'string',
    demandOption: true,
    describe: '分类标识（如 mens_all / womens_all）'
  })
  .option('overwrite-latest', {
    alias: 'ol',
    type: 'boolean',
    default: false,
    describe: '写入固定最新文件 callaway_products_<category>_latest.json'
  })
  .argv;

const SOURCE_DIR = path.join(__dirname, 'golf_content', 'callaway');
const OUTPUT_DIR = path.join(__dirname, 'results');

function findLatestProductsFile() {
  const files = fs.readdirSync(SOURCE_DIR).filter((f) => f.startsWith('callaway_products_') && f.endsWith('.json'));
  if (!files.length) throw new Error('未找到任何 callaway_products_*.json 文件');
  const sorted = files
    .map((f) => ({ name: f, mtime: fs.statSync(path.join(SOURCE_DIR, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime);
  return path.join(SOURCE_DIR, sorted[0].name);
}

function main() {
  const { category, overwriteLatest } = argv;
  try {
    const sourceFile = findLatestProductsFile();
    const data = JSON.parse(fs.readFileSync(sourceFile, 'utf8'));

    if (!data.results || !Array.isArray(data.results) || !data.results.length) {
      throw new Error('源文件不包含 results 数组，无法复用');
    }

    const ts = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    const fileName = overwriteLatest
      ? `callaway_products_${category}_latest.json`
      : `callaway_products_${category}_${ts}.json`;
    const outPath = path.join(OUTPUT_DIR, fileName);

    // 直接复制原始数据，附带类别提示
    data.snapshotSource = path.basename(sourceFile);
    data.requestedCategory = category;
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2), 'utf8');

    console.log('✅ 已复用现有抓取文件');
    console.log(`源文件: ${sourceFile}`);
    console.log(`输出文件: ${outPath}`);
    console.log(`产品数量: ${data.results.reduce((sum, r) => sum + (r.products ? r.products.length : 0), 0)}`);
  } catch (err) {
    console.error('❌ 复用失败:', err.message);
    process.exit(1);
  }
}

main();
