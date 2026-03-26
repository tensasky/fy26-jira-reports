-- FY26_PMO 数据库架构
-- 创建时间: 2026-03-23
-- 用途: 存储 FY26_PMO 报表数据

-- 抓取日志表
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetch_type TEXT NOT NULL,  -- 'epics', 'initiatives', 'features'
    project TEXT,
    count INTEGER,
    status TEXT,
    error_message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Epics 表（从各项目抓取）
CREATE TABLE IF NOT EXISTS epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    project TEXT NOT NULL,
    summary TEXT,
    description TEXT,
    status TEXT,
    assignee TEXT,
    assignee_email TEXT,
    reporter TEXT,
    created TIMESTAMP,
    updated TIMESTAMP,
    parent_key TEXT,  -- 关联的 CNTIN Feature
    labels TEXT,  -- JSON 格式存储
    raw_data TEXT,  -- 完整原始数据 JSON
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initiatives 表（从 CNTIN 抓取，带 FY26_INIT 标签）
CREATE TABLE IF NOT EXISTS initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    summary TEXT,
    description TEXT,
    status TEXT,
    assignee TEXT,
    assignee_email TEXT,
    reporter TEXT,
    created TIMESTAMP,
    updated TIMESTAMP,
    labels TEXT,  -- JSON 格式存储
    raw_data TEXT,  -- 完整原始数据 JSON
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Features 表（从 CNTIN 抓取，属于 Initiatives）
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    summary TEXT,
    description TEXT,
    status TEXT,
    assignee TEXT,
    assignee_email TEXT,
    reporter TEXT,
    created TIMESTAMP,
    updated TIMESTAMP,
    parent_key TEXT NOT NULL,  -- 关联的 CNTIN Initiative
    labels TEXT,  -- JSON 格式存储
    raw_data TEXT,  -- 完整原始数据 JSON
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 层级关系视图: Initiative -> Feature -> Epic
CREATE VIEW IF NOT EXISTS hierarchy_view AS
SELECT 
    i.key as initiative_key,
    i.summary as initiative_summary,
    i.status as initiative_status,
    i.assignee as initiative_assignee,
    f.key as feature_key,
    f.summary as feature_summary,
    f.status as feature_status,
    f.assignee as feature_assignee,
    e.key as epic_key,
    e.project as epic_project,
    e.summary as epic_summary,
    e.status as epic_status,
    e.assignee as epic_assignee
FROM initiatives i
LEFT JOIN features f ON f.parent_key = i.key
LEFT JOIN epics e ON e.parent_key = f.key;

-- 项目统计视图
CREATE VIEW IF NOT EXISTS project_stats AS
SELECT 
    project,
    COUNT(*) as epic_count,
    COUNT(DISTINCT parent_key) as linked_features
FROM epics
GROUP BY project;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project);
CREATE INDEX IF NOT EXISTS idx_epics_parent ON epics(parent_key);
CREATE INDEX IF NOT EXISTS idx_features_parent ON features(parent_key);
CREATE INDEX IF NOT EXISTS idx_epics_key ON epics(key);
CREATE INDEX IF NOT EXISTS idx_features_key ON features(key);
CREATE INDEX IF NOT EXISTS idx_initiatives_key ON initiatives(key);
