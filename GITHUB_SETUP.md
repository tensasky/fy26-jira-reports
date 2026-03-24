# GitHub 发布指南

## 本地仓库位置

```
/Users/admin/.openclaw/workspace/projects/cntin730-report/
```

## 推送到 GitHub 步骤

### 1. 创建 GitHub 仓库

访问 https://github.com/new 创建新仓库：
- 仓库名: `cntin730-report`
- 描述: `CNTIN-730 FY26 Intakes 周报系统`
- 可见性: Private

### 2. 配置远程仓库

```bash
cd /Users/admin/.openclaw/workspace/projects/cntin730-report
git remote add origin https://github.com/YOUR_USERNAME/cntin730-report.git
```

### 3. 推送代码

```bash
git push -u origin main
```

或使用 GitHub CLI（如果已登录）：

```bash
cd /Users/admin/.openclaw/workspace/projects/cntin730-report
gh repo create cntin730-report --private --source=. --push
```

## 当前状态

- ✅ 代码已提交到本地 Git 仓库
- ✅ 版本: v5.2.0
- ✅ 定时任务已安装（工作日 12:00）
- ⏳ 等待推送到 GitHub

## 定时任务详情

- **文件**: `~/Library/LaunchAgents/com.openclaw.cntin730-report.plist`
- **执行时间**: 每周一至周五 12:00
- **脚本**: `/Users/admin/.openclaw/workspace/projects/cntin730-report/scripts/run.sh`
- **日志**: `~/.openclaw/workspace/logs/cntin730_launchd.log`

## 手动执行

```bash
# 手动运行报告生成
/Users/admin/.openclaw/workspace/projects/cntin730-report/scripts/run.sh

# 或仅生成报告
python3 /Users/admin/.openclaw/workspace/projects/cntin730-report/scripts/cntin730_report.py
```
