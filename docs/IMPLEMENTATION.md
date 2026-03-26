# FY26 Jira Reports - Implementation Document

## 1. System Architecture

### 1.1 Overview
The system consists of three independent reporting modules, each following a similar architecture:
- Data fetching from Jira API
- Local SQLite storage
- HTML report generation
- Encrypted email delivery
- Automated scheduling via launchd

### 1.2 Module Structure

```
projects/
├── cntin730-report/          # CNTIN-730 Weekly Report
│   ├── scripts/
│   │   ├── cntin730_report.py    # Main report generator
│   │   └── send_report.py        # Email sender with AES-256 encryption
│   ├── reports/                   # Generated HTML/ZIP files
│   ├── logs/                      # Execution logs
│   └── config/
│       └── com.openclaw.cntin730-report.plist
│
├── fy26_pmo/                  # FY26_PMO Daily Report
│   ├── scripts/
│   │   ├── fetch_data.py         # Data fetching with pagination
│   │   ├── generate_html_v5.py   # HTML generator v5.7
│   │   ├── send_email.py         # Email sender
│   │   └── run.sh               # Main execution script
│   ├── jira_report.db            # SQLite database
│   └── reports/
│
└── fy26-intake-cost/          # FY26_Intake_Cost Report
    ├── scripts/
    │   ├── fetch_intake_cost.py  # Data fetching
    │   ├── generate_html.py      # Interactive HTML generator
    │   └── run.sh
    ├── intake_cost.db            # SQLite database
    └── reports/
```

## 2. Implementation Details

### 2.1 Data Fetching

#### 2.1.1 Jira API Integration
```python
# Common pattern across all modules
import requests
import base64

JIRA_URL = "https://lululemon.atlassian.net"
auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
auth_b64 = base64.b64encode(auth_str.encode()).decode()
headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

# Pagination handling
def fetch_issues_jql(jql, fields, page_size=100):
    all_issues = []
    next_page_token = None
    
    while True:
        payload = {"jql": jql, "maxResults": page_size, "fields": fields}
        if next_page_token:
            payload["nextPageToken"] = next_page_token
        
        response = requests.post(
            f"{JIRA_URL}/rest/api/3/search/jql",
            headers=headers, json=payload, verify=False
        )
        data = response.json()
        
        all_issues.extend(data.get('issues', []))
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
    
    return all_issues
```

#### 2.1.2 Data Transformation
```python
# Parse Jira's ADF (Atlassian Document Format) to plain text
def parse_adf_to_text(adf_content):
    texts = []
    def extract_text(node):
        if isinstance(node, dict):
            if node.get('type') == 'text':
                texts.append(node.get('text', ''))
            if 'content' in node:
                for child in node['content']:
                    extract_text(child)
    extract_text(adf_content)
    return ''.join(texts)
```

### 2.2 Database Schema

#### 2.2.1 Common Fields
All three reports share common database patterns:
- Primary key: Jira ticket key (e.g., CNTIN-730)
- Timestamps: created, updated (ISO 8601 format)
- JSON fields: labels, linked_issues (stored as JSON strings)

#### 2.2.2 FY26_Intake_Cost Schema
```sql
CREATE TABLE intakes (
    key TEXT PRIMARY KEY,
    summary TEXT,
    description TEXT,           -- Parsed ADF content
    status TEXT,                -- Jira status
    status_category TEXT,       -- To Do / In Progress / Done
    assignee TEXT,
    reporter TEXT,
    created TEXT,              -- ISO 8601 timestamp
    updated TEXT,
    labels TEXT,               -- JSON array (Pillars)
    components TEXT,           -- Type (e.g., "Data Platform")
    affects_versions TEXT,     -- Approver info
    initiative_child_count INTEGER,  -- Cost calculation base
    linked_issues TEXT,        -- JSON array (Follow up)
    issue_links TEXT           -- JSON array (changelog)
);
```

### 2.3 HTML Generation

#### 2.3.1 Template Structure (FY26_Intake_Cost)
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>FY26 Intake Cost Report</title>
    <style>
        /* CSS Grid for table layout */
        .table-header, .table-row {
            display: grid;
            grid-template-columns: 
                minmax(160px,1.5fr)   /* Intake */
                minmax(80px,0.8fr)    /* Pillar */
                minmax(60px,0.5fr)    /* SLA */
                minmax(90px,0.7fr)    /* Status */
                minmax(80px,0.7fr)    /* Assignee */
                minmax(90px,0.8fr)    /* Cost */
                minmax(80px,0.7fr)    /* Approver */
                minmax(120px,1fr);   /* Scope */
        }
    </style>
</head>
<body>
    <!-- Header with language toggle -->
    <div class="header">
        <h1 data-i18n="title">FY26 Intake Cost Report</h1>
        <div class="lang-toggle">
            <button onclick="setLang('zh')">中文</button>
            <button onclick="setLang('en')">EN</button>
        </div>
    </div>
    
    <!-- Exchange rate setting -->
    <div class="rate-setting">
        <input type="number" id="exchangeRate" value="0.135" 
               onchange="updateExchangeRate()">
    </div>
    
    <!-- Interactive table with JavaScript -->
    <script>
        // Data injected from Python
        const rowsData = [...];  // JSON data
        let exchangeRate = 0.135;
        
        // Real-time cost calculation
        function formatCost(rmb, rate) {
            const usd = rmb * rate;
            return `¥${rmb.toFixed(2)}<br>$${usd.toFixed(2)}`;
        }
    </script>
</body>
</html>
```

#### 2.3.2 Interactive Features
```javascript
// Status filtering with mapping
function filterByStatus(status) {
    const statusMapping = {
        'not_started': ['New'],
        'in_progress': ['Discovery', 'Strategy', 'Execution'],
        'closed': ['Done'],
        'cancelled': ['Cancelled']
    };
    
    activeFilters.status = status;
    renderTable();
}

// Expandable rows
function toggleRow(key) {
    const row = document.querySelector(`[data-key="${key}"]`);
    row.classList.toggle('expanded');
    const details = document.getElementById(`details-${key}`);
    details.classList.toggle('show');
}

// i18n support
const i18n = {
    zh: { title: 'FY26 Intake Cost 报表', ... },
    en: { title: 'FY26 Intake Cost Report', ... }
};
```

### 2.4 Email Delivery

#### 2.4.1 AES-256 Encryption
```python
import subprocess

def create_encrypted_zip(html_file, password="lulupmo"):
    zip_file = html_file.with_suffix('.zip')
    cmd = [
        "/opt/homebrew/bin/7z", "a", "-tzip",
        f"-p{password}", "-mem=AES256",
        str(zip_file), str(html_file)
    ]
    subprocess.run(cmd, capture_output=True)
    return zip_file
```

#### 2.4.2 SMTP with TLS
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(zip_file, recipient):
    msg = MIMEMultipart()
    msg['Subject'] = f"CNTIN-730 FY26项目周报 - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = "3823810468@qq.com"
    msg['To'] = recipient
    
    # Attach encrypted ZIP
    with open(zip_file, 'rb') as f:
        attachment = MIMEBase('application', 'zip')
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 
                          f'attachment; filename="{zip_file.name}"')
    msg.attach(attachment)
    
    # Send via QQ SMTP
    with smtplib.SMTP('smtp.qq.com', 587) as server:
        server.starttls()
        server.login("3823810468@qq.com", os.getenv('QQ_EMAIL_PASSWORD'))
        server.send_message(msg)
```

## 3. Scheduling Configuration

### 3.1 macOS launchd Setup

#### 3.1.1 CNTIN-730 (Weekdays 12:00)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.cntin730-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/admin/.../scripts/send_report.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <dict>  <!-- Monday -->
            <key>Weekday</key><integer>1</integer>
            <key>Hour</key><integer>12</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Tuesday-Friday similar -->
    </array>
</dict>
</plist>
```

#### 3.1.2 Installation Commands
```bash
# Copy plist file
cp com.openclaw.cntin730-report.plist ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist

# Verify status
launchctl list | grep cntin730
```

### 3.2 Troubleshooting

#### 3.2.1 Common Issues
| Issue | Solution |
|-------|----------|
| Job not running | Check `launchctl list` output |
| Permission denied | Ensure plist file is owned by user |
| Python not found | Use full path `/usr/bin/python3` |
| Environment variables | Set in plist `EnvironmentVariables` dict |

#### 3.2.2 Log Locations
```
~/Library/LaunchAgents/com.openclaw.*.plist  # Config
~/.../projects/*/logs/*.log                   # Application logs
~/.../projects/*/logs/launchd.log            # launchd stdout
~/.../projects/*/logs/launchd_error.log      # launchd stderr
```

## 4. Error Handling

### 4.1 Jira API Errors
```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("⚠️ Request timeout, retrying...")
    time.sleep(5)
    # Retry logic
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP Error: {e}")
    # Log and alert
```

### 4.2 Email Delivery Failures
```python
for attempt in range(3):
    try:
        send_email(zip_file, recipient)
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
        time.sleep(60)  # Wait 1 minute before retry
```

## 5. Security Implementation

### 5.1 API Token Management
- Stored in: `~/.openclaw/workspace/.jira-config`
- Format: `export JIRA_API_TOKEN="..."`
- File permissions: 600

### 5.2 Email Credentials
- Stored in environment variable: `QQ_EMAIL_PASSWORD`
- Loaded from `.jira-config` at runtime
- Never logged or displayed

### 5.3 Data Encryption
- Database: File-level permissions (600)
- Email attachments: AES-256 ZIP encryption
- Password: `lulupmo` (shared via separate channel)

## 6. Performance Optimization

### 6.1 Database Indexing
```sql
CREATE INDEX idx_status ON intakes(status);
CREATE INDEX idx_created ON intakes(created);
CREATE INDEX idx_pillar ON intakes(labels);
```

### 6.2 Caching Strategy
- SQLite database persists between runs
- Only fetch updated records (using `updated` timestamp)
- HTML reports cached until next generation

### 6.3 Memory Management
- Streaming JSON parsing for large responses
- Batch database inserts (100 records at a time)
- Explicit garbage collection after report generation

## 7. Testing

### 7.1 Unit Tests
```python
def test_status_mapping():
    assert get_status_class('New') == 'status-todo'
    assert get_status_class('Discovery') == 'status-progress'
    assert get_status_class('Done') == 'status-done'

def test_cost_calculation():
    assert format_cost(100, 0.135) == '¥100.00<br>$13.50'
```

### 7.2 Integration Tests
- Jira API connectivity test
- Database read/write test
- Email delivery test (to test address)
- End-to-end report generation test

## 8. Monitoring

### 8.1 Health Checks
```bash
# Check launchd status
launchctl list | grep -E "(cntin730|fy26)"

# Check recent logs
tail -50 ~/.../projects/*/logs/*.log

# Check database integrity
sqlite3 intake_cost.db "SELECT COUNT(*) FROM intakes;"
```

### 8.2 Alerts
- Email failure: Logged to stderr
- Data fetch failure: Retry with exponential backoff
- Missing report: Manual intervention required
