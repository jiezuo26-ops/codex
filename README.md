# 亚马逊卖家热点内容自动化系统 MVP

这个项目用于每天抓取与亚马逊卖家相关的热点信息，筛选可能影响利润、运营风险、广告成本、FBA费用、仓储费、佣金、退货、账户健康、Listing流量、红人视频、UGC、A+、主图视频、AI内容合规的内容，并生成待人工审核的内容草稿。

项目定位不是普通“亚马逊新闻搬运号”，而是帮助亚马逊卖家判断：

- 哪些平台变化会影响利润？
- 哪些流量变化值得跟？
- 哪些内容趋势能提高转化？
- 哪些视觉、视频、A+、UGC、主图视频动作现在更值得做？

内容最后要自然承接到业务方向：

- 红人视频。
- 亚马逊可购买视频。
- 主图视频。
- A+。
- Listing视觉优化。
- AI视频内容。

常用内容钩子：

- 亚马逊卖家注意：这个变化可能正在影响你的利润。
- 很多卖家还没发现，亚马逊这个流量入口正在变重要。
- FBA成本又变了？真正该看的不是新闻，而是利润模型。
- 为什么现在越来越多卖家开始补红人视频？
- 亚马逊Listing转化差，不一定是价格问题。

第一版不做自动发布，只生成 JSON 和 Markdown 文件，方便人工检查后再使用。

## 项目结构

```text
amazon-hotspot-content-bot/
├─ sources/          # 数据源列表
├─ prompts/          # 内容生成提示词模板
├─ outputs/          # 每天生成的抓取、评分、草稿内容
├─ scripts/          # 自动抓取、评分、生成脚本
├─ requirements.txt  # Python 依赖
└─ README.md         # 项目说明
```

## 安装依赖

先确认电脑已经安装 Python 3.10 或更新版本。MVP 版本暂不需要第三方依赖，但仍建议运行下面命令，方便后续加依赖时保持习惯一致。

```powershell
python -m pip install -r requirements.txt
```

## 大模型生成配置

默认使用本地模板生成内容，适合 MVP 跑通流程：

```powershell
USE_LLM=false
```

第二版建议开启大模型生成，提高小红书、抖音口播、公众号文章的理解和表达质量：

```powershell
USE_LLM=true
LLM_API_KEY=你的 API Key
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

配置说明：

- `USE_LLM`：是否启用大模型生成，`true` 或 `false`。
- `LLM_API_KEY`：大模型 API Key，也兼容 `OPENAI_API_KEY`。
- `LLM_BASE_URL`：OpenAI 兼容接口地址，可替换成支持 OpenAI Chat Completions 格式的服务。
- `LLM_MODEL`：模型名称。
- `LLM_TEMPERATURE`：创意程度，默认 `0.7`。
- `LLM_MAX_TOKENS`：最大输出长度，默认 `3000`。

项目提供了 [.env.example](.env.example) 作为配置参考。大模型调用失败时，系统会自动退回本地模板，不会中断每日流程。

如果使用 GitHub Actions，需要在仓库里配置：

- `Settings -> Secrets and variables -> Actions -> Secrets` 添加 `LLM_API_KEY`。
- `Settings -> Secrets and variables -> Actions -> Variables` 添加 `USE_LLM=true`，以及可选的 `LLM_MODEL`、`LLM_BASE_URL`。

## 每日摘要通知

系统可以在每天运行完成后自动发送摘要。摘要包含：

- 抓取来源数量。
- 抓取失败数量。
- 需要人工补充数量。
- 进入内容生成的热点数量。
- 生成草稿数量。
- 高风险需核查数量。
- 今日 TOP 热点。
- 今日发布包路径。

默认不配置通知地址时，摘要只会显示在 GitHub Actions 日志里。

要发送到飞书、企业微信、钉钉或自定义 Webhook，请在 GitHub 仓库配置：

- `Settings -> Secrets and variables -> Actions -> Secrets` 添加 `SUMMARY_WEBHOOK_URL`。
- `Settings -> Secrets and variables -> Actions -> Variables` 添加 `SUMMARY_WEBHOOK_TYPE`。

`SUMMARY_WEBHOOK_TYPE` 支持：

- `generic`：默认格式，发送 `{"text": "...摘要..."}`。
- `feishu` 或 `lark`：飞书/Lark 文本消息格式。
- `wecom`、`wechat_work` 或 `enterprise_wechat`：企业微信文本消息格式。
- `dingtalk` 或 `dingding`：钉钉文本消息格式。

本地测试摘要：

```powershell
python scripts/send_summary.py
```

## 数据源

主要数据源文件是：

```text
sources/sources.csv
```

字段说明：

```csv
platform,name,url,type,priority
```

- `platform`：平台，例如 `douyin`、`xiaohongshu_search`、`wechat_creator`。
- `name`：来源名称。
- `url`：需要抓取的网页地址。
- `type`：来源类型，当前支持 `official`、`official_forum`、`industry_media`、`creator`、`creator_search`、`manual_article`。
- `priority`：优先级，1 到 10，数字越大越重要。

添加新数据源时，直接在 `sources/sources.csv` 里新增一行即可。

## 运行流程

每天按下面顺序运行：

```powershell
python scripts/fetch_hotspots.py
python scripts/score_hotspots.py
python scripts/generate_content.py
python scripts/export_today_package.py
```

第一版完整流程也可以一键运行：

```powershell
python scripts/run_daily.py
```

它会依次完成：

1. 更新热点。
2. 筛选 TOP 5。
3. 生成内容草稿。
4. 导出今日发布包。

如果自动抓取失败，或者你手里已经有链接/正文，可以手动补充热点：

```powershell
python scripts/add_manual_hotspot.py
```

按提示粘贴链接、标题和正文。正文粘贴完成后，输入单独一行 `END` 结束。手动补充后继续运行：

```powershell
python scripts/score_hotspots.py
python scripts/generate_content.py
```

也可以直接用一行命令录入：

```powershell
python scripts/add_manual_hotspot.py --title "热点标题" --url "https://example.com" --text "这里粘贴正文"
```

也可以交给 GitHub Actions 自动运行。项目已配置定时任务文件：

```text
.github/workflows/daily-hotspot.yml
```

- 每天北京时间上午 10 点自动运行一次。
- 自动执行 `fetch_hotspots.py`、`score_hotspots.py`、`generate_content.py`、`export_today_package.py`。
- 自动把 `outputs/日期/` 里的生成结果提交回 GitHub 仓库。
- 自动执行 `send_summary.py` 发送每日摘要；未配置 Webhook 时只输出到 Actions 日志。
- 如果运行失败，错误会显示在 GitHub Actions 的运行日志里。

你也可以在 GitHub 仓库页面进入 `Actions`，选择 `Daily Hotspot Content`，点击 `Run workflow` 手动运行一次。

运行后会自动创建当天目录，例如：

```text
outputs/2026-06-26/
```

里面会包含：

- `raw_items/`：每个数据源单独保存的抓取 JSON。
- `raw_hotspots.json`：全部抓取结果汇总。
- `scored_hotspots.json`：全部内容评分结果。
- `top5_hotspots.json`：TOP 5 热点。
- `drafts/`：每个热点对应的内容草稿。
- `draft_index.json`：草稿索引。
- `publish_package/`：今日发布包，包含审核摘要、草稿合集和可直接查看的草稿文件。

## 脚本说明

### 1. 抓取热点

```powershell
python scripts/fetch_hotspots.py
```

这个脚本会读取 `sources/sources.csv`，依次抓取每个 URL 的网页标题、正文摘要、发布时间。如果某个 URL 抓取失败，会把失败原因写进 JSON，不会中断整个流程。

小红书、抖音、公众号等平台可能经常抓不到完整正文。系统的失败兜底规则是：

1. 保存失败原因到 `error`。
2. 不删除该来源。
3. 标记 `need_manual_input: true`。
4. 用户可以通过 `add_manual_hotspot.py` 手动补充标题、链接、正文。
5. 手动补充内容会同样进入评分、内容生成和今日发布包流程。

### 2. 热点评分

```powershell
python scripts/score_hotspots.py
```

这个脚本会按 100 分制评分：

- 利润影响 30分：佣金、FBA费用、仓储费、广告费、促销成本、退款、退货、现金流。
- 运营风险 20分：账户健康、政策违规、Listing下架、评价合规、品牌备案、侵权。
- 流量影响 20分：搜索排名、广告位、视频展示位、Amazon Inspire、Posts、Influencer、A+、主图视频。
- 传播价值 20分：是否适合做成卖家愿意收藏、转发、评论的内容。
- 时效性 10分：是否为最近 7 到 30 天的新内容。

最终输出超过 70 分的 TOP 5 热点。70 分及以下只保留在 `scored_hotspots.json` 里供人工查看，不进入内容生成。

评分脚本还会为每条热点增加事实核查字段：

```json
{
  "fact_check_required": true,
  "risk_level": "high",
  "source_urls": [],
  "uncertain_points": [],
  "publish_warning": "发布前必须人工核查"
}
```

只要内容涉及 FBA费用、仓储费、佣金、广告成本、退款、退货、政策变化、账户健康、封号风险、Listing下架、侵权、AI内容合规、生效日期等，系统会自动标记为 `risk_level: high`，并写入需要人工核查的不确定点。

### 3. 生成内容草稿

```powershell
python scripts/generate_content.py
```

这个脚本只会为超过 70 分的 TOP 5 热点生成：

- 小红书图文大纲，6页结构。
- 公众号科普文章草稿。
- 抖音60秒口播脚本。
- 跨境论坛引流帖。
- 标题备选 10 个。
- 适合配图方向。
- 事实核查提醒。

所有草稿都保存在当天的 `outputs/日期/drafts/` 文件夹里。

### 4. 导出今日发布包

```powershell
python scripts/export_today_package.py
```

这个脚本会把当天适合审核的内容整理到 `outputs/日期/publish_package/`。

今日发布包会包含：

- 今日热点标题。
- 为什么值得做。
- 小红书图文脚本。
- 公众号文章。
- 抖音口播。
- 论坛帖。
- 配图建议。
- 风险提醒。
- 参考来源。

- `README.md`：今日热点摘要和审核说明。
- `today_publish_package.md`：今日可审核内容合集。
- `items/`：单个热点的发布包文件。
- `manifest.json`：发布包文件清单。

## 修改提示词

提示词模板在：

```text
prompts/content_prompt.md
```

当前脚本使用稳定的本地模板生成草稿，没有接入大模型 API。后续如果要接入 OpenAI、Claude 或其他模型，可以把这个文件作为主提示词，再把 TOP 5 热点信息传给模型。

## 维护建议

- 每周检查一次 `sources/sources.csv`，删除失效链接。
- 对高价值创作者提高 `priority`。
- 对经常抓取失败但内容重要的平台，可以先保留，后续再接浏览器抓取方案。
- 发布前必须人工核查事实，尤其是费用、规则、生效日期、封号和合规类内容。
