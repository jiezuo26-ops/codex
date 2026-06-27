# 数据源类型说明

`sources/sources.csv` 的 `type` 字段统一使用以下 6 类：

- `official`：亚马逊官方公告、Seller News、政策页面。
- `official_forum`：亚马逊官方论坛、卖家社区讨论。
- `industry_media`：行业媒体、第三方趋势观察网站。
- `creator`：明确的社媒创作者、博主、公众号作者。
- `creator_search`：小红书等平台的搜索结果页，用于跟踪某个创作者或关键词。
- `manual_article`：人工粘贴的链接、正文或临时热点材料。

示例：

```csv
platform,name,url,type,priority
amazon,Amazon Seller News,https://sellercentral.amazon.com/gp/headlines.html,official,10
amazon,Amazon Seller Forums,https://sellercentral.amazon.com/seller-forums,official_forum,9
industry,Marketplace Pulse,https://www.marketplacepulse.com/,industry_media,8
douyin,某亚马逊博主,https://www.douyin.com/user/example,creator,8
xiaohongshu_search,亚马逊广告经验,https://www.xiaohongshu.com/search_result?keyword=亚马逊广告经验,creator_search,7
manual,手动补充热点,https://example.com/article,manual_article,10
```
