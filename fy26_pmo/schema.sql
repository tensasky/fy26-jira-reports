-- FY26_PMO 数据库结构

-- Initiatives 表 (CNTIN项目，带FY26_INIT标签)
CREATE TABLE IF NOT EXISTS initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    labels TEXT,
    created TEXT,
    updated TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Features 表 (CNTIN项目)
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 指向Initiative
    labels TEXT,
    created TEXT,
    updated TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Epics 表 (其他项目)
CREATE TABLE IF NOT EXISTS epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    project TEXT,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 指向Feature (可能为NULL)
    labels TEXT,
    created TEXT,
    updated TEXT,
    has_parent BOOLEAN DEFAULT 0,  -- 是否有parent
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 抓取日志
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step TEXT,
    project TEXT,
    count INTEGER,
    status TEXT,
    message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project);
CREATE INDEX IF NOT EXISTS idx_epics_parent ON epics(parent_key);
CREATE INDEX IF NOT EXISTS idx_features_parent ON features(parent_key);
CREATE INDEX IF NOT EXISTS idx_initiatives_key ON initiatives(key);
