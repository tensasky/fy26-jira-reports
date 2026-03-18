# 变更日志规范

## 版本号规则

采用语义化版本：MAJOR.MINOR.PATCH

- **MAJOR**: 重大架构变更、频道增删
- **MINOR**: 新增技能、功能变更
- **PATCH**: 配置微调、bug修复

---

## 记录格式

每次变更按以下格式追加：

```markdown
## [版本号] - YYYY-MM-DD

### 新增 (Added)
- 新增技能: xxx
- 新增频道: xxx
- 新增配置: xxx

### 变更 (Changed)
- 更新技能: xxx v1.0 → v1.1
- 修改配置: xxx

### 弃用 (Deprecated)
- 即将移除: xxx

### 移除 (Removed)
- 移除技能: xxx
- 禁用频道: xxx

### 安全 (Security)
- 更新密钥
- 调整权限

### 修复 (Fixed)
- 修复 xxx 问题
```

---

## 快速命令

```bash
# 查看当前配置版本
cat ~/.openclaw/workspace/config/CONFIG-VERSIONS.md | grep "当前版本"

# 查看变更历史
cat ~/.openclaw/workspace/config/CHANGELOG.md

# 备份当前配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d)
```

---

## 回溯操作

如需回滚到某个版本：

1. 查看 CHANGELOG.md 找到目标版本
2. 恢复对应版本的 openclaw.json 配置
3. 重新安装对应版本的技能
4. 重启 Gateway

