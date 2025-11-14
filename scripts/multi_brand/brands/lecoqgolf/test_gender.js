const EnhancedDetailScraper = require("./enhanced_detail_scraper");
const scraper = new EnhancedDetailScraper();

async function testGender() {
  try {
    console.log("🔍 测试性别识别...");
    const result = await scraper.scrapeDetailPage("https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/");
    console.log("性别:", result.gender);
    console.log("商品编号:", result.productCode);
    console.log("标题:", result.title.translated || result.title.original);
  } catch (error) {
    console.error("错误:", error.message);
  }
}

testGender();
