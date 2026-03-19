# 🌙 Moonshot Token 用量监控

已为你创建完整的 Token 用量监控方案，包括：

1. **HTML 仪表盘** - 可视化查看余额和历史趋势
2. **定时报告** - 每6小时自动查询并发送飞书消息
3. **历史记录** - 自动保存使用历史，支持趋势分析

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `moonshot-dashboard.html` | 可视化仪表盘，在浏览器中打开即可查看 |
| `scripts/moonshot_reporter.py` | 查询脚本，被定时任务调用 |
| `scripts/check-moonshot-balance.sh` | Shell 版本查询脚本 |
| `moonshot-balance-history.csv` | 余额历史记录（自动创建）|

---

## ⚙️ 配置步骤

### 1. 设置 API Key

创建 `.env` 文件并添加你的 Moonshot API Key：

```bash
cd /Users/admin/.openclaw/workspace
echo "MOONSHOT_API_KEY=your_api_key_here" > .env
```

或者直接在命令行设置：

```bash
export MOONSHOT_API_KEY=your_api_key_here
```

### 2. 查看 HTML 仪表盘

用浏览器打开 `moonshot-dashboard.html`：

```bash
open moonshot-dashboard.html
```

首次打开需要输入 API Key（会保存在浏览器本地存储中）。

仪表盘功能：
- 💰 实时余额显示
- 📊 使用统计和趋势
- 📝 历史记录表格
- ⏱️ 自动刷新

---

## ⏰ 定时任务

已创建定时任务，每6小时自动运行一次：

```
任务 ID: 63785c7f-e147-44fe-8f65-b3f373d4b197
频率: 每6小时 (00:00, 06:00, 12:00, 18:00)
操作: 查询余额 → 发送到飞书
```

### 管理定时任务

查看所有任务：
```bash
openclaw cron list
```

暂停任务：
```bash
openclaw cron update 63785c7f-e147-44fe-8f65-b3f373d4b197 --enabled=false
```

删除任务：
```bash
openclaw cron remove 63785c7f-e147-44fe-8f65-b3f373d4b197
```

立即运行一次测试：
```bash
python3 scripts/moonshot_reporter.py
```

---

## 📊 报告内容

每次定时任务会发送如下报告到飞书：

```
🌙 Moonshot Token 用量报告

📅 查询时间: 2026-02-13 09:00

💰 余额情况
• 可用余额: 1,234,567 tokens
• 总余额: 2,000,000 tokens
• 已使用: 765,433 tokens (38.3%)

📊 余额构成
• 赠送余额: 1,000,000 tokens
• 充值余额: 1,000,000 tokens

✅ 状态: 余额充足

---
⏰ 每6小时自动更新
```

---

## 🔧 自定义设置

### 修改查询频率

编辑定时任务：

```bash
# 改为每12小时
openclaw cron update 63785c7f-e147-44fe-8f65-b3f373d4b197 \
  --schedule '{"kind":"every","everyMs":43200000}'
```

### 修改报告格式

编辑 `scripts/moonshot_reporter.py` 中的 `generate_report()` 函数。

---

## 📝 历史数据

所有查询结果自动保存到 `moonshot-balance-history.csv`，格式：

```csv
time,available,total,used,usage_rate,granted,topped_up
2026-02-13 09:00,1234567,2000000,765433,38.3,1000000,1000000
```

你可以用 Excel 或任何 CSV 工具分析使用趋势。
