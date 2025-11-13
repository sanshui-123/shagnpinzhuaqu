/**
 * 飞书API调用示例
 * 运行前需要配置:
 * 1. 飞书App ID
 * 2. 飞书App Secret
 * 3. 表格App Token
 */

const https = require('https');

// 配置信息 - 需要替换为实际值
const APP_ID = 'your_app_id_here';
const APP_SECRET = 'your_app_secret_here';
const TABLE_TOKEN = 'your_table_token_here';

// 要写入的数据
const recordData = {
    "商品标题": "双面フーディー夹克",
    "品牌": "le coq sportif golf",
    "商品编号": "LG5FWB50M",
    "性别": "男",
    "价格": "￥19,800",
    "颜色选项": "ネイビー（NV00）, ネイビー×グレー（NV01）, ブラック（BK00）, ブルー（BL00）, グレー（GY00）, ベージュ（BG00）",
    "颜色数量": 6,
    "尺码选项": "S, M, L, LL",
    "尺码数量": 4,
    "图片总数": 48,
    "主要图片链接": "https://sc3.locondo.jp/contents/commodity_image/LE/LE1872EM012989_1_l.jpg",
    "详情页文字": "着脱可能な袖でベストとしても使える冬の定番、動きやすくて暖かい中棉夹克。-------------------------------------------------------------■可拆卸袖子的两用设计の中棉夹克です。作为夹克，作为马甲、シーンに合わせて着用できます。■袖窿内侧には、伸缩材质的活动褶を採用。扩大肩胛骨周围的活动范围、减轻挥杆时的压力します。■中わたはストレッチ機能のあるものを採用。さらに部位によって量を調整し、動きやすさにこだわりました。■裏地には、独自开发的保温功能「ヒートナビ」を搭載。【HEAT NAVI（ヒートナビ）】クリーンエネルギーである太陽光を効率よく活用した、提高了光吸收性能的蓄热保温材料で、従来の未加工素材と比べて+5℃の効果があります。将几乎所有光转化为热量するため、光さえあれば、即使不运动也能感受到温暖できます。■身頃には、三角形图案的绗缝を施し、兼顾设计性和保温性しています。■左胸と右胸には标志刺绣、左袖には布章をあしらっています。■後ろ襟には配色带を使用し、デザインのアクセントに。■左胸には带拉链的口袋を配置しています。■版型：常规■素材：表料：兼具伸缩性和防风性的聚酯纤维塔夫绸、里料：带热航功能的伸缩里料、中棉：有伸缩性的功能中棉【ルコックスポルティフ（ゴルフ）（le coq sportif golf）】フランス生まれのルコックスポルティフが、充满功能性和时尚性、创造时尚的高尔夫风格。#ルコックスポルティフゴルフ #le coq sportif golf #ゴルフ #ゴルフウェア機能：HEAT NAVI/MOTION 3D/はっ水/防風/蓄熱保温/デタッチャブル/部分ストレッチ\nログインすると以前注文した同じカテゴリの商品とサイズ比較が可能です。\nウェアを平置きにして測った、製品そのものの大きさです。お手持ちのウェアとの比較にご活用ください。\nお客様の身体の目安寸法です。動きやすさやフィット感を考慮したサイズ選びの基準となります。\n                    詳細は\n                    \n                      \n                      \n                      \n                      \n                      \n                        \n                      \n                      \n                      \n                      \n                      \n                      \n                      \n                      \n                      \n                      \n                    \n                        サイズガイド\n                        \n                      \n                    をご確認ください。\n",
    "尺码表": "\n    \n      \n        商品番号\n        \n      \n      LE1872EM012989\n    \n    \n      \n        ブランド商品番号※店舗お問い合わせ用\n        \n      \n      \n        \n          \n            LG5FWB50M\n          \n          \n        \n      \n    \n      \n        \n          ブランド名\n          \n        \n        \n          \n            le coq sportif golf（ルコックスポルティフ ゴルフ）\n            \n          \n        \n      \n    \n    \n    \n    \n      \n        色\n        \n      \n      ベージュ（BG00）\n    \n    \n    \n    \n      \n    \n      \n    \n      \n    \n      \n        \n          原産国\n            \n          \n          \n            \n              \n              \n                ミャンマー\n              \n            \n          \n        \n      \n    \n      \n        \n          重量\n            \n          \n          \n            \n              \n              \n                430.0g\n              \n            \n          \n        \n      \n    \n      \n        \n          洗濯記号\n            \n          \n          \n            \n              \n                \n                \n                  \n                \n                  \n                \n                  \n                \n                  \n                \n                  \n                \n                  \n                \n                  \n                \n                \n                  \n                    \n                    \n                      \n                        洗濯表示について\n                        \n                      \n                    \n                  \n                \n              \n              \n            \n          \n        \n      \n    \n      \n    \n      \n        \n          シーズン\n            \n          \n          \n            \n              \n              \n                2025年 秋冬\n              \n            \n          \n        \n      \n    \n\n    \n    \n      \n        \n          性別タイプ\n          \n        \n        \n          \n            \n\n              \n              \n              \n              \n                \n                \n                \n              \n                \n                \n                \n              \n              \n                \n                \n                  メンズ\n                \n                \n              \n              \n            \n            \n          \n        \n      \n    \n\n  ",
    "详情页链接": "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/",
    "抓取时间": "2025-11-12T17:42:57.015Z"
};

async function getTenantAccessToken() {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            app_id: APP_ID,
            app_secret: APP_SECRET
        });

        const options = {
            hostname: 'open.feishu.cn',
            port: 443,
            path: '/open-apis/auth/v3/tenant_access_token/internal',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': data.length
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    const response = JSON.parse(body);
                    if (response.code === 0) {
                        resolve(response.tenant_access_token);
                    } else {
                        reject(new Error(`获取Token失败: ${response.msg}`));
                    }
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function writeRecordToFeishu(token) {
    return new Promise((resolve, reject) => {
        // 将记录数据转换为飞书表格格式
        const records = [{
            fields: Object.keys(recordData).map(key => ({
                field_name: key,
                field_value: recordData[key]
            }))
        }];

        const data = JSON.stringify({ records });

        const options = {
            hostname: 'open.feishu.cn',
            port: 443,
            path: `/open-apis/bitable/v1/apps/${APP_ID}/tables/${TABLE_TOKEN}/records/batch_create`,
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Content-Length': data.length
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    const response = JSON.parse(body);
                    if (response.code === 0) {
                        console.log('✅ 成功写入飞书表格！');
                        console.log(`记录ID: ${response.data.records[0].record_id}`);
                        resolve(response);
                    } else {
                        reject(new Error(`写入失败: ${response.msg}`));
                    }
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    try {
        console.log('🚀 开始写入飞书表格...');

        // 1. 获取访问令牌
        const token = await getTenantAccessToken();
        console.log('✅ 获取访问令牌成功');

        // 2. 写入记录
        await writeRecordToFeishu(token);

        console.log('🎉 飞书API写入完成！');

    } catch (error) {
        console.error('❌ 写入失败:', error.message);
    }
}

if (require.main === module) {
    main();
}
