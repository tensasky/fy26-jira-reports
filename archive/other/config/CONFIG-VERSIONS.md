# OpenClaw 配置与技能版本管理

> 版本化记录所有配置和技能变更，便于回溯和审计

---

## 📊 当前版本概览

| 组件 | 版本 | 最后更新 |
|------|------|----------|
| OpenClaw Core | 2026.2.25 | 2026-03-05 |
| 已安装技能 | 21+ | 2026-03-05 |
| 活跃频道 | 2 | 2026-02-27 |

---

## 🔄 版本历史

### v1.4.0 (2026-03-05)

**变更类型:** MINOR (新增产品经理技能)

#### 新增
- ✅ **product-manager** - 产品经理核心技能
- ✅ **proto-cog** - 原型设计工具
- ✅ **excalidraw-canvas** - 线框图画布
- ✅ **superdesign** - 超级设计工具

**技能清单 (21+)**
| 技能名 | 版本 | 类别 | 用途 |
|--------|------|------|------|
| product-manager | latest | 产品 | 产品经理核心能力 |
| openclaw-tavily-search | latest | 搜索 | Tavily AI 搜索引擎 |
| office-document-specialist-suite | latest | 办公 | Office 文档套件 |
| ... | | | |

---

### v1.3.0 (2026-02-28)

**变更类型:** MINOR (新增技能)

#### 新增
- ✅ **openclaw-tavily-search** - Tavily AI 搜索

**技能清单 (20)**
| 技能名 | 版本 | 类别 | 用途 |
|--------|------|------|------|
| openclaw-tavily-search | latest | 搜索 | Tavily AI 搜索引擎 |
| office-document-specialist-suite | latest | 办公 | Office 文档套件 |
| multi-search-engine | 2.0.1 | 搜索 | 多引擎聚合搜索 |
| ... (其余17个见v1.0.0/v1.1.0/v1.2.0) | | | |

---

### v1.2.0 (2026-02-28)

**变更类型:** MINOR (新增技能)

#### 新增
- ✅ **office-document-specialist-suite** - Office 文档专业套件

**技能清单 (19)**
| 技能名 | 版本 | 类别 | 用途 |
|--------|------|------|------|
| office-document-specialist-suite | latest | 办公 | Office 文档套件 |
| multi-search-engine | 2.0.1 | 搜索 | 多引擎聚合搜索 |
| ... (其余17个见v1.0.0/v1.1.0) | | | |

---

### v1.1.0 (2026-02-28)

**变更类型:** MINOR (新增技能)

#### 新增
- ✅ **multi-search-engine** - 多搜索引擎聚合查询

**技能清单 (18)**
| 技能名 | 版本 | 类别 | 用途 |
|--------|------|------|------|
| multi-search-engine | latest | 搜索 | 多引擎聚合搜索 |
| memory | 1.0.0 | 核心 | 长期记忆管理 |
| automation-workflows | 0.1.0 | 效率 | 自动化工作流 |
| ... (其余16个见v1.0.0) | | | |

---

### v1.0.0 (2026-02-27)

---

## 🔄 版本历史

### v1.0.0 (2026-02-27)

**核心配置**
- OpenClaw Core: 2026.2.25
- Gateway: 本地模式 (127.0.0.1:18789)
- 主模型: moonshot/kimi-k2.5

**频道配置**
```yaml
channels:
  feishu:
    enabled: true
    appId: cli_a91bd999acb8dbce
    domain: feishu
    connectionMode: websocket
    dmPolicy: pairing
    groupPolicy: allowlist
    
  telegram:
    enabled: true
    botToken: "***...oxT8"  # 已脱敏
    dmPolicy: pairing
    groupPolicy: allowlist
    polling: enabled
```

**已安装技能 (17)**

| 技能名 | 版本 | 类别 | 用途 |
|--------|------|------|------|
| memory | 1.0.0 | 核心 | 长期记忆管理 |
| automation-workflows | 0.1.0 | 效率 | 自动化工作流 |
| self-improving | 1.1.0 | 核心 | 自我改进 |
| copywriter | 1.1.0 | 内容 | UX/营销文案 |
| content-ideas | 1.0.2 | 内容 | 内容创意生成 |
| seo-content-writer | 0.1.1 | 内容 | SEO文章写作 |
| tube-cog | 1.0.2 | 媒体 | YouTube视频制作 |
| insta-cog | 1.0.2 | 媒体 | Instagram/TikTok视频 |
| tushare-finance | 2.0.6 | 金融 | A股/港股/美股数据 |
| stock-market-pro | 1.1.0 | 金融 | 股票分析与图表 |
| slides-cog | 1.0.5 | 内容 | PPT/PDF生成 |
| ppt-generator | 1.0.0 | 内容 | 竖屏极简PPT |
| word-docx | 1.0.0 | 文档 | Word文档读写 |
| cellcog | 1.0.21 | 研究 | 深度研究/多模态 |
| sapi-ttsl | 1.0.0 | 语音 | Windows SAPI5 TTS |

**系统技能 (内置, 36)**
- feishu_doc, feishu_wiki, feishu_drive, feishu_bitable
- web_search, web_fetch
- browser, canvas
- sessions_*, subagents
- 等...

**安全策略**
```yaml
denyCommands:
  - camera.snap
  - camera.clip
  - screen.record
  - calendar.add
  - contacts.add
  - reminders.add
```

**模型配置**
```yaml
primary: moonshot/kimi-k2.5
contextWindow: 256k
maxTokens: 8192
```

---

## 📝 变更日志 (Changelog)

### [v1.4.0] - 2026-03-05

#### 新增 (Added)
- 安装技能: product-manager (产品经理核心技能)
- 安装技能: proto-cog (原型设计工具)
- 安装技能: excalidraw-canvas (线框图画布)
- 安装技能: superdesign (超级设计工具)

#### 变更 (Changed)
- 技能总数: 20 → 24

#### 备份
- 配置文件已备份: `backups/openclaw-v1.4.0-20260305.json`

---

### [v1.3.0] - 2026-02-28

#### 新增 (Added)
- 安装技能: openclaw-tavily-search (Tavily AI 搜索引擎)

#### 变更 (Changed)
- 技能总数: 19 → 20

#### 备份
- 配置文件已备份: `backups/openclaw-v1.3.0-20260228.json`

---

### [v1.2.0] - 2026-02-28

#### 新增 (Added)
- 安装技能: office-document-specialist-suite (Office 文档专业套件)

#### 变更 (Changed)
- 技能总数: 18 → 19

#### 备份
- 配置文件已备份: `backups/openclaw-v1.2.0-20260228.json`

---

### [v1.1.0] - 2026-02-28

#### 新增 (Added)
- 安装技能: multi-search-engine (多搜索引擎聚合)

#### 变更 (Changed)
- 技能总数: 17 → 18

#### 备份
- 配置文件已备份: `backups/openclaw-v1.1.0-20260228.json`

---

### [v1.0.0] - 2026-02-27

#### 新增
- ✅ Telegram 机器人频道 (`openclaw pairing approve`)
- ✅ Feishu 企业微信集成
- ✅ 17 个技能安装完成

#### 配置
- Gateway 本地模式绑定 127.0.0.1:18789
- 主模型设为 kimi-k2.5
- 安全策略禁用敏感命令

#### 文档
- Chrome CDP 抓取方式记录
- Telegram 配置步骤记录

---

## 🛠️ 技能安装命令参考

```bash
# 列出可用技能
clawhub list

# 安装技能
clawhub install <skill-name>

# 更新技能
clawhub sync <skill-name>

# 强制重新安装
clawhub install <skill-name> --force
```

---

## 📋 待办/计划

- [ ] 配置 embedding provider (memory search)
- [ ] 创建东风/白板多 Agent 配置
- [ ] 设置定时任务 cron jobs
- [ ] 配置外部工具 (如有需要)

---

## 🔐 敏感信息位置

| 信息类型 | 存储位置 | 说明 |
|----------|----------|------|
| API Keys | `~/.openclaw/credentials/` | 各服务商密钥 |
| Bot Tokens | `~/.openclaw/openclaw.json` | Telegram/Feishu |
| 配对码 | 运行时临时 | 需手动批准 |

---

*此文件由 Tensasky 维护*
*最后更新: 2026-02-27*
