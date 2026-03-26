# Changelog

所有版本更新记录。

## [5.2.0] - 2026-03-19

### 修复
- 修复点击展开功能，现在可以完整显示 Summary、Description 和 AI Summary
- Description 提取不再截断，显示完整内容
- 优化列宽：Summary 500px, Description 600px, AI Summary 550px

### 新增
- AI Summary 自动生成：根据 Description 智能提取 What/Why
- 展开时保留文本格式（white-space: pre-wrap）

### 变更
- 表格最小宽度调整为 1600px
- Summary 默认显示前 80 字符（原 60）

## [5.1.0] - 2026-03-18

### 变更
- 移除 Creator 和 Reporter 列
- Description 列宽度增加至 500-700px
- Alerts 列改为缩略图标（⚠️）显示在 Ticket Number 后

## [5.0.0] - 2026-03-12

### 重构
- 从 JSON 文件迁移到 SQLite 数据库架构
- 数据持久化存储，避免数据丢失
- 支持 SQL 查询和重复生成报告

### 修复
- 修复多个项目 Epic 抓取不完整问题
- 优化数据合并逻辑

## [4.x] - 2026-03-11

### 修复
- 多次修复 JSON 合并 bug
- 数据丢失问题（已废弃）

## [3.0.0] - 2026-03-11

### 修复
- 修正数据结构：CNTIN 项目没有 Epic
- 正确的扫描逻辑：Initiative → Feature → Epic

## [2.0.0] - 2026-03-11

### 废弃
- 尝试反向扫描，数据结构错误（已废弃）

## [1.0.0] - 2026-03-10

### 初始版本
- 基础报告功能
- 错误的数据结构（已废弃）
