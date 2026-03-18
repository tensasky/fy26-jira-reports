-- FY26_INIT 数据库 Schema v5.3 (Optimized)
-- 优化内容：
-- 1. WAL 模式支持（预写式日志）
-- 2. 优化的索引策略
-- 3. 外键约束
-- 4. 统计视图

-- 启用 WAL 模式（提升读写并发性能）
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;  -- 平衡性能和安全性
PRAGMA cache_size=-64000;   -- 64MB 缓存
PRAGMA temp_store=MEMORY;   -- 临时表存储在内存

-- epics 表
CREATE TABLE IF NOT EXISTS epics (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,
    created TEXT,
    updated TEXT,  -- 新增：用于增量更新
    labels TEXT,
    raw_json TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- features 表
CREATE TABLE IF NOT EXISTS features (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,
    updated TEXT,  -- 新增：用于增量更新
    labels TEXT,
    raw_json TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- initiatives 表
CREATE TABLE IF NOT EXISTS initiatives (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    updated TEXT,  -- 新增：用于增量更新
    labels TEXT,
    raw_json TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 抓取日志表
CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    issue_type TEXT,
    count INTEGER,
    status TEXT,
    error_message TEXT,
    is_incremental BOOLEAN DEFAULT 0,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 性能优化索引
-- 用于按项目查询
CREATE INDEX IF NOT EXISTS idx_epics_project ON epics(project);
CREATE INDEX IF NOT EXISTS idx_epics_status ON epics(status);
CREATE INDEX IF NOT EXISTS idx_epics_parent ON epics(parent_key);
CREATE INDEX IF NOT EXISTS idx_epics_updated ON epics(updated);  -- 增量更新

-- 用于 Feature 查询
CREATE INDEX IF NOT EXISTS idx_features_parent ON features(parent_key);
CREATE INDEX IF NOT EXISTS idx_features_project ON features(project);
CREATE INDEX IF NOT EXISTS idx_features_updated ON features(updated);  -- 增量更新

-- 用于 Initiative 查询
CREATE INDEX IF NOT EXISTS idx_initiatives_project ON initiatives(project);
CREATE INDEX IF NOT EXISTS idx_initiatives_updated ON initiatives(updated);  -- 增量更新

-- 用于日志查询
CREATE INDEX IF NOT EXISTS idx_fetch_log_project ON fetch_log(project);
CREATE INDEX IF NOT EXISTS idx_fetch_log_fetched_at ON fetch_log(fetched_at);

-- 统计视图
CREATE VIEW IF NOT EXISTS v_epic_stats AS
SELECT 
    project,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status != 'Done' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'Done' THEN 1 END) as done_count
FROM epics
GROUP BY project;

CREATE VIEW IF NOT EXISTS v_daily_changes AS
SELECT 
    date(fetched_at) as date,
    COUNT(*) as total_fetched,
    SUM(CASE WHEN is_incremental THEN 1 ELSE 0 END) as incremental_count
FROM fetch_log
GROUP BY date(fetched_at)
ORDER BY date DESC;
