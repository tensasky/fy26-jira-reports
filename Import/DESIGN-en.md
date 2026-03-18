# Intake Summary Report - Design Document

## Requirements Analysis

### Product Positioning
**Intake Summary Report** — An enterprise project intake management dashboard for monitoring project progress, costs, and SLA risk status.

### Target Users
- **Primary Users**: Project managers, department managers, delivery teams
- **Use Cases**: Daily project monitoring, weekly reporting, resource allocation decisions

### Core Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Department Filter** | Quick filter by department (EC/Marketing/Retail/SCM/MP&A/Corporate/Tech) | P0 |
| **KPI Overview** | Real-time statistics for total, open, in-progress, closed, and cancelled intakes | P0 |
| **Data Visualization** | Status distribution donut chart + task type bar chart | P1 |
| **Data Table** | Display intake details with search and filtering | P0 |
| **Date Filter** | Filter data by date range | P1 |
| **Export** | Export to Excel report | P2 |
| **SLA Alert** | Highlight pending days (>14 days red, >7 days yellow) | P1 |

### Data Fields
- Intake ID, Department, Requester, Created Date
- Task Type (Development/Configuration/Project/Additional Budget)
- Pending Days, Status, Cost, Approver, Description, Linked BRD

---

## UI Design

### Design Philosophy
**"Clean and professional, content-focused"** — Adopting lululemon brand style with white base and red accent, creating a professional dashboard suitable for technical/delivery teams.

### Color Scheme

| Usage | Color | Hex |
|-------|-------|-----|
| Background | Pure White | `#FFFFFF` |
| Page Background | Light Gray | `#F8FAFC` |
| Brand Accent | lululemon Red | `#E31937` |
| Primary Text | Dark Slate | `#1E293B` |
| Secondary Text | Slate-500 | `#64748B` |
| Border | Slate-200 | `#E2E8F0` |

### Status Colors

| Status | Color | Background |
|--------|-------|------------|
| Open | Blue | `#DBEAFE` / `#2563EB` |
| In Progress | Amber | `#FEF3C7` / `#D97706` |
| Closed | Emerald | `#D1FAE5` / `#059669` |
| Cancelled | Gray | `#F1F5F9` / `#475569` |
| SLA Critical | Red | `#FEE2E2` / `#DC2626` |
| SLA Warning | Amber | `#FEF3C7` / `#D97706` |

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [LOGO/Title]                   [Search] [Export Button]    │
├─────────────────────────────────────────────────────────────┤
│  [All] [EC] [Marketing] [Retail] [SCM] [MP&A] [Corp] [Tech] │
├─────────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Total  │ │  Open  │ │In Prog │ │ Closed │ │Cancelled│   │
│  │   30   │ │   10   │ │    6   │ │   11   │ │    3   │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
├─────────────────────────────────────────────────────────────┤
│  ▼ Data Visualization Dashboard (Collapsible)               │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  Status Distribution │  │ Task Type Distribution│         │
│  └─────────────────────┘  └─────────────────────┘          │
├─────────────────────────────────────────────────────────────┤
│  📅 Date Filter: [Start Date] to [End Date]                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Intake Details Table (ID/Type/Pending/Status/Cost/ │   │
│  │  Approver/Description/Link)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                              Total Closed Costs: $ 387,900 │
└─────────────────────────────────────────────────────────────┘
```

### Interactions

1. **KPI Card Click**: Filter table by status
2. **Chart Collapse**: Expand/collapse chart section
3. **Hover Effects**: Table row highlight, KPI card lift
4. **Real-time Search**: Instant table filtering
5. **Date Filter**: Auto-update on date selection

---

## Prototype Design

### Component List

| Component | Description |
|-----------|-------------|
| Header | Title + Search + Export button |
| DeptFilter | Department filter buttons |
| KPICards | 5 KPI statistic cards |
| ChartSection | Collapsible chart area |
| DateFilter | Date range selector |
| DataTable | Data table with pagination |

### Responsive Breakpoints

- **Desktop**: > 1024px — Full layout
- **Tablet**: 768px - 1024px — Adjusted spacing
- **Mobile**: < 768px — Stacked layout

### Animation Specs

| Animation | Duration | Easing |
|-----------|----------|--------|
| KPI Card Hover | 250ms | cubic-bezier(0.4, 0, 0.2, 1) |
| Chart Expand/Collapse | 300ms | ease-out |
| Button Hover | 200ms | ease |
| Table Row Hover | 150ms | ease |

---

## Files

- `index-en.html` — Complete English HTML implementation
- `index.html` — Chinese version
- `Final.html` — Original reference file

### Tech Stack
- **CSS**: Tailwind CSS (CDN)
- **Charts**: Chart.js + ChartDataLabels
- **Icons**: Font Awesome 6
- **Font**: Inter

---

*Version: v1.0*  
*Updated: 2026-03-06*
