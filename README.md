# FY26 Jira Reports

自动化 Jira 报告生成系统，包含 FY26_INIT Epic 日报和 CNTIN-730 Initiative 周报。

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## 📋 项目概述

本项目为 lululemon China Technology 团队提供自动化的 Jira 数据报告生成服务：

| 报告 | 频率 | 数据源 | 主要功能 |
|------|------|--------|----------|
| **FY26_INIT Epic 日报** | 每日 18:00 | 22 个 Jira 项目 | Epic/Feature/Initiative 跟踪 |
| **CNTIN-730 Initiative 周报** | 按需/定时 | CNTIN-730 | AI 智能 What/Why 摘要 |

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- macOS (LaunchAgent 调度)
- Jira API Token
- QQ 邮箱授权码

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/tensasky/fy26-jira-reports.git
cd fy26-jira-reports
```

2. **安装依赖**
```bash
pip3 install requests
```

3. **配置环境变量**
```bash
# ~/.zshrc 或 ~/.bash_profile
export JIRA_API_TOKEN="your_jira_api_token"
export JIRA_EMAIL="your_email@lululemon.com"
export QQ_MAIL_PASSWORD="your_qq_auth_code"
```

4. **加载配置**
```bash
source ~/.zshrc
```

---

## 📊 FY26_INIT Epic 日报

### 功能特性

- ✅ **22 项目覆盖**: CNTEC, CNTOM, CNTDM, CNTMM, CNTD, CNTEST, CNENG, CNINFA, CNCA, CPR, EPCH, CNCRM, CNDIN, SWMP, CDM, CMDM, CNSCM, OF, CNRTPRJ, CSCPVT, CNPMO, CYBERPJT
- ✅ **SQLite 持久化**: 数据存储在本地数据库，确保完整性
- ✅ **交互式报告**: HTML 报告支持状态/项目/标签筛选
- ✅ **SLA Alert**: 自动标记超过 2 周未更新的 Epic
- ✅ **自动邮件**: 每日 18:00 自动发送到 chinatechpmo@lululemon.com

### 执行方式

**手动执行**:
```bash
python3 scripts/fy26_daily_report_v5.sh
```

**定时执行** (已配置 LaunchAgent):
```bash
# 查看状态
launchctl list | grep fy26

# 重新加载
launchctl unload ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist
```

### 数据模型

```
Initiative (CNTIN)
  └── Feature (CNTIN)
        └── Epic (Other Projects: CPR, CNTEC, etc.)
```

---

## 🤖 CNTIN-730 Initiative 周报

### 功能特性

- ✅ **AI 智能摘要**: 自动生成 What/Why 业务解释
- ✅ **自然语言**: 动词开头，避免 AI 腔调，中英混合
- ✅ **冻结列设计**: 前 3 列固定，支持横向滚动
- ✅ **并发处理**: 5 线程并行生成摘要，~10 分钟完成 100+ Initiatives
- ✅ **缓存机制**: AI 摘要结果缓存，避免重复调用

### AI 摘要示例

**输入**:
```
标题: Implement Cloud POS for China Stores
描述: Migrate all stores from legacy POS to Cloud POS...
```

**输出**:
```html
<b>What:</b> 把线下门店的 POS 系统从旧版升级到 Cloud POS，
支持全渠道退货和实时库存查询<br>
<b>Why:</b> 现在门店退货要查好几个系统，太慢了，升级后一个界面搞定，
提升顾客体验和店员效率
```

### 执行方式

**手动执行**:
```bash
python3 scripts/cntin730_weekly_report.py
```

**配置定时任务** (可选):
```bash
# 每周一 9:00 执行
crontab -e
0 9 * * 1 cd $(pwd) && python3 scripts/cntin730_weekly_report.py
```

---

## 📁 项目结构

```
fy26-jira-reports/
├── scripts/
│   ├── fy26_daily_report_v5.sh          # FY26 日报主控脚本
│   ├── fetch_fy26_v5.py                 # 数据抓取
│   ├── generate_fy26_report_v5.py       # JSON 报告生成
│   ├── generate_fy26_html_v5.py         # HTML 报告生成
│   ├── send_fy26_report_v5.py           # 邮件发送
│   ├── cntin730_weekly_report.py        # CNTIN-730 周报主脚本
│   └── fy26_db_schema.sql               # 数据库Schema
├── docs/
│   ├── brd/                             # 业务需求文档
│   ├── prd/                             # 产品需求文档
│   └── design/                          # 详细设计文档
├── config/
│   └── com.openclaw.fy26-daily-report.plist  # LaunchAgent配置
├── reports/                             # 生成的报告
├── jira-reports/                        # 数据存储
│   └── fy26_data.db                     # SQLite数据库
├── CHANGELOG.md                         # 变更日志
└── README.md                            # 本文件
```

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `JIRA_API_TOKEN` | Jira API Token | 是 |
| `JIRA_EMAIL` | Jira 邮箱 | 是 |
| `QQ_MAIL_PASSWORD` | QQ 邮箱授权码 | 是 |
| `AI_API_KEY` | AI API Key (CNTIN-730) | 可选 |
| `AI_BASE_URL` | AI API 基础 URL | 可选 |

### 邮件配置

| 配置项 | 值 |
|--------|-----|
| SMTP 服务器 | smtp.qq.com |
| SSL 端口 | 465 |
| STARTTLS 端口 | 587 |
| 发件人 | 3823810468@qq.com |
| 收件人 | chinatechpmo@lululemon.com |
| 抄送 | rcheng2@lululemon.com |

---

## 🛠️ 故障排查

### 常见问题

**Q: 日报没有收到**  
A: 检查 LaunchAgent 状态:
```bash
launchctl list | grep fy26
tail -f logs/fy26_daily_report.log
```

**Q: 数据抓取不完整**  
A: 验证 Jira API Token 权限:
```bash
curl -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://lululemon.atlassian.net/rest/api/3/myself"
```

**Q: 邮件发送失败**  
A: 更新 QQ 邮箱授权码:
1. 登录 QQ 邮箱网页版
2. 设置 → 账户 → 开启 SMTP
3. 生成新授权码
4. 更新环境变量

**Q: AI 摘要生成慢**  
A: 检查缓存命中率:
```bash
ls -la /tmp/ai_summary_cache/ | wc -l
```

---

## 📚 文档

### 业务文档
- [FY26_INIT BRD](docs/brd/FY26_INIT_Epic_Report_BRD.md) - 业务需求
- [CNTIN730 BRD](docs/brd/CNTIN730_Initiative_Report_BRD.md) - 业务需求

### 产品文档
- [FY26_INIT PRD](docs/prd/FY26_INIT_Epic_Report_PRD.md) - 产品需求
- [CNTIN730 PRD](docs/prd/CNTIN730_Initiative_Report_PRD.md) - 产品需求

### 技术文档
- [FY26_INIT Design](docs/design/FY26_INIT_Epic_Report_Design.md) - 详细设计
- [CNTIN730 Design](docs/design/CNTIN730_Initiative_Report_Design.md) - 详细设计

### 发布记录
- [CHANGELOG](CHANGELOG.md) - 版本历史

---

## 🧪 开发

### 本地测试

```bash
# 测试数据抓取
python3 scripts/fetch_fy26_v5.py

# 测试报告生成
python3 scripts/generate_fy26_report_v5.py
python3 scripts/generate_fy26_html_v5.py

# 测试邮件发送
export QQ_MAIL_PASSWORD="test_password"
python3 scripts/send_fy26_report_v5.py
```

### 代码提交

```bash
git add .
git commit -m "feat: description"
git push origin main
```

---

## 📈 性能指标

| 指标 | FY26_INIT 日报 | CNTIN-730 周报 |
|------|----------------|----------------|
| 数据抓取 | < 3 分钟 | < 2 分钟 |
| 报告生成 | < 30 秒 | < 1 分钟 |
| AI 摘要 | - | ~10 分钟 (100 个) |
| 邮件发送 | < 10 秒 | < 10 秒 |

---

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 联系

- **作者**: OpenClaw
- **邮箱**: rcheng2@lululemon.com
- **项目**: https://github.com/tensasky/fy26-jira-reports

---

## 🙏 致谢

- lululemon China Technology 团队
- PMO 团队的反馈和支持
