-- FY26_INIT 数据库架构
-- 用于存储 Jira 数据并生成报告

-- Epic 表（其他项目的 Epic）
CREATE TABLE IF NOT EXISTS epics (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 关联的 CNTIN Feature
    created TEXT,
    labels TEXT,  -- JSON 数组
    raw_json TEXT,  -- 完整的 JSON 数据
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature 表（CNTIN Feature）
CREATE TABLE IF NOT EXISTS features (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 关联的 CNTIN Initiative
    labels TEXT,  -- JSON 数组
    raw_json TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initiative 表（CNTIN Initiative）
CREATE TABLE IF NOT EXISTS initiatives (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    labels TEXT,  -- JSON 数组
    raw_json TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project);
CREATE INDEX IF NOT EXISTS idx_epics_parent ON epics(parent_key);
CREATE INDEX IF NOT EXISTS idx_features_parent ON features(parent_key);
CREATE INDEX IF NOT EXISTS idx_features_labels ON features(labels);
CREATE INDEX IF NOT EXISTS idx_initiatives_labels ON initiatives(labels);

-- 抓取日志表
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    issue_type TEXT,  -- Epic, Feature, Initiative
    count INTEGER,
    status TEXT,  -- success, failed
    error_message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
