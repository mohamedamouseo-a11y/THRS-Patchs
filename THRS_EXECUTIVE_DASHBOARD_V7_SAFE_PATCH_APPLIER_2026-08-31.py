#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path.cwd()
DASH = ROOT / 'frontend/src/pages/dashboards/ExecutiveDashboard.jsx'
CLIENT = ROOT / 'frontend/src/components/integration/ClientStatsWidget.jsx'
DELIVERY = ROOT / 'frontend/src/components/integration/DeliveryMetricsWidget.jsx'
SAT = ROOT / 'frontend/src/components/integration/SatisfactionWidget.jsx'
CSS = ROOT / 'frontend/src/styles/thrs-main-dashboard-v7.css'

FILES = [DASH, CLIENT, DELIVERY, SAT]
for path in FILES:
    if not path.exists():
        raise SystemExit(f'MISSING: {path}')
if not CSS.exists():
    raise SystemExit(f'MISSING: {CSS}')

originals = {p: p.read_text(encoding='utf-8') for p in FILES}
updated = dict(originals)


def replace_once(path, old, new, label):
    text = updated[path]
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR FAIL [{label}] expected 1 match, found {count}')
    updated[path] = text.replace(old, new, 1)


def replace_all(path, old, new, expected_min, label):
    text = updated[path]
    count = text.count(old)
    if count < expected_min:
        raise SystemExit(f'ANCHOR FAIL [{label}] expected >= {expected_min} matches, found {count}')
    updated[path] = text.replace(old, new)

# Dashboard imports / activation.
replace_once(DASH, "import React from 'react';", "import React, { useEffect, useState } from 'react';", 'react-hooks')
replace_once(DASH, "  Clock,\n  Gauge,", "  Clock,\n  Command,\n  Gauge,\n  Maximize2,", 'icons-command')
replace_once(DASH, "  Settings2,\n  Sparkles,", "  Settings2,\n  SlidersHorizontal,\n  Sparkles,", 'icons-slider')
replace_once(DASH, "  Wallet,\n} from 'lucide-react';", "  Wallet,\n  X,\n} from 'lucide-react';", 'icons-x')
replace_once(DASH, "import '../../styles/thrs-main-dashboard-v6.css';", "import '../../styles/thrs-main-dashboard-v6.css';\nimport '../../styles/thrs-main-dashboard-v7.css';", 'v7-css-import')

# Interaction state + keyboard command palette.
replace_once(
    DASH,
    "  const { data, loading, error } = useDashboardData();\n",
    "  const { data, loading, error } = useDashboardData();\n"
    "  const [timeRange, setTimeRange] = useState('7d');\n"
    "  const [selectedDepartment, setSelectedDepartment] = useState(null);\n"
    "  const [urgentOnly, setUrgentOnly] = useState(false);\n"
    "  const [focusMode, setFocusMode] = useState('overview');\n"
    "  const [commandOpen, setCommandOpen] = useState(false);\n\n"
    "  useEffect(() => {\n"
    "    const onKeyDown = (event) => {\n"
    "      const target = event.target;\n"
    "      const editable = target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA' || target?.isContentEditable;\n"
    "      if (!editable && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {\n"
    "        event.preventDefault();\n"
    "        setCommandOpen((value) => !value);\n"
    "      }\n"
    "      if (event.key === 'Escape') setCommandOpen(false);\n"
    "    };\n"
    "    window.addEventListener('keydown', onKeyDown);\n"
    "    return () => window.removeEventListener('keydown', onKeyDown);\n"
    "  }, []);\n",
    'interaction-state'
)

# Derived executive intelligence.
replace_once(
    DASH,
    "  const departmentTotal = departmentDistribution.reduce((sum, item) => sum + Number(item.count || 0), 0);\n",
    "  const departmentTotal = departmentDistribution.reduce((sum, item) => sum + Number(item.count || 0), 0);\n"
    "  const visibleAttendanceTrend = timeRange === 'today' ? attendanceTrend.slice(-1) : attendanceTrend.slice(-7);\n"
    "  const healthScore = Math.max(0, Math.min(100, Math.round(\n"
    "    (attendanceRate * 0.62) + ((100 - Math.min(absentRate, 100)) * 0.18) + ((100 - Math.min(lateRate * 2, 100)) * 0.10) + ((100 - Math.min(pendingCount * 8, 100)) * 0.10)\n"
    "  )));\n"
    "  const healthState = healthScore >= 85 ? 'excellent' : healthScore >= 65 ? 'stable' : 'attention';\n"
    "  const briefingCount = Number(absentToday > 0) + Number(pendingCount > 0) + Number(lateToday > 0);\n",
    'derived-intelligence'
)
replace_all(DASH, 'attendanceTrend.map(', 'visibleAttendanceTrend.map(', 4, 'visible-trend')

# Root activation.
replace_once(
    DASH,
    '<main className="thrs-main-dashboard thrs-main-dashboard--v3 thrs-main-dashboard--v4 thrs-main-dashboard--v5 thrs-main-dashboard--v5-1 thrs-main-dashboard--v5-2 thrs-main-dashboard--v6 fade-in" dir={direction}>',
    '<main className="thrs-main-dashboard thrs-main-dashboard--v3 thrs-main-dashboard--v4 thrs-main-dashboard--v5 thrs-main-dashboard--v5-1 thrs-main-dashboard--v5-2 thrs-main-dashboard--v6 thrs-main-dashboard--v7 fade-in" dir={direction} data-v7-focus={focusMode}>',
    'root-v7'
)

# Executive briefing / health / focus navigation.
header_anchor = "      </header>\n\n      <section className=\"thrs-main-dashboard__v3-command thrs-main-dashboard__v6-command-deck\" aria-label={copy.totalEmployees}>"
briefing = "      </header>\n\n      <section className=\"thrs-main-dashboard__v7-briefing\" aria-label={language === 'ar' ? 'الملخص التنفيذي' : 'Executive briefing'}>\n        <div className=\"thrs-main-dashboard__v7-briefing-copy\">\n          <span>{language === 'ar' ? 'الملخص التنفيذي' : 'Executive briefing'}</span>\n          <strong>{briefingCount > 0\n            ? (language === 'ar' ? `${briefingCount} إشارات تحتاج انتباهك اليوم` : `${briefingCount} signals need your attention today`)\n            : (language === 'ar' ? 'لا توجد إشارات حرجة الآن' : 'No critical signals right now')}</strong>\n          <small>{language === 'ar' ? 'اضغط على أي مساحة أدناه للتعمق بدون مغادرة لوحة القيادة.' : 'Use focus mode or a signal below to drill in without leaving the command center.'}</small>\n        </div>\n        <div className=\"thrs-main-dashboard__v7-health-cluster\">\n          <div className={`thrs-main-dashboard__v7-health-score is-${healthState}`} style={{ '--v7-score': `${healthScore * 3.6}deg` }}>\n            <div><strong>{healthScore}</strong><small>/100</small></div>\n          </div>\n          <div className=\"thrs-main-dashboard__v7-health-copy\">\n            <small>{language === 'ar' ? 'صحة القوى العاملة' : 'Workforce health'}</small>\n            <strong>{healthState === 'excellent' ? (language === 'ar' ? 'ممتاز' : 'Excellent') : healthState === 'stable' ? (language === 'ar' ? 'مستقر' : 'Stable') : (language === 'ar' ? 'يحتاج انتباه' : 'Needs attention')}</strong>\n          </div>\n        </div>\n        <nav className=\"thrs-main-dashboard__v7-focus-nav\">\n          {[['overview', language === 'ar' ? 'نظرة عامة' : 'Overview'], ['workforce', language === 'ar' ? 'القوى العاملة' : 'Workforce'], ['decisions', language === 'ar' ? 'القرارات' : 'Decisions'], ['business', language === 'ar' ? 'الأعمال' : 'Business']].map(([value, label]) => (\n            <button type=\"button\" key={value} className={focusMode === value ? 'is-active' : ''} onClick={() => setFocusMode(value)} aria-pressed={focusMode === value}>{label}</button>\n          ))}\n        </nav>\n        <button type=\"button\" className=\"thrs-main-dashboard__v7-command-button\" onClick={() => setCommandOpen(true)}>\n          <Command size={17} aria-hidden=\"true\" /><span>{language === 'ar' ? 'الأوامر' : 'Commands'}</span><kbd>⌘K</kbd>\n        </button>\n      </section>\n\n      <section className=\"thrs-main-dashboard__v3-command thrs-main-dashboard__v6-command-deck\" aria-label={copy.totalEmployees}>"
replace_once(DASH, header_anchor, briefing, 'briefing')

# Workforce controls.
intel_anchor = "          </div>\n          <div className=\"thrs-main-dashboard__v6-intelligence-facts\">"
intel_controls = "          </div>\n          <div className=\"thrs-main-dashboard__v7-intelligence-controls\">\n            <div className=\"thrs-main-dashboard__v7-range-switch\" role=\"group\">\n              <button type=\"button\" className={timeRange === 'today' ? 'is-active' : ''} onClick={() => setTimeRange('today')}>{language === 'ar' ? 'اليوم' : 'Today'}</button>\n              <button type=\"button\" className={timeRange === '7d' ? 'is-active' : ''} onClick={() => setTimeRange('7d')}>{language === 'ar' ? '٧ أيام' : '7 days'}</button>\n            </div>\n            {selectedDepartment ? <button type=\"button\" className=\"thrs-main-dashboard__v7-selection-chip\" onClick={() => setSelectedDepartment(null)}><span>{selectedDepartment}</span><X size={13} aria-hidden=\"true\" /></button> : null}\n            <button type=\"button\" className=\"thrs-main-dashboard__v7-focus-button\" onClick={() => setFocusMode(focusMode === 'workforce' ? 'overview' : 'workforce')}><Maximize2 size={14} aria-hidden=\"true\" />{focusMode === 'workforce' ? (language === 'ar' ? 'إنهاء التركيز' : 'Exit focus') : (language === 'ar' ? 'تركيز' : 'Focus')}</button>\n          </div>\n          <div className=\"thrs-main-dashboard__v6-intelligence-facts\">"
replace_once(DASH, intel_anchor, intel_controls, 'intelligence-controls')

# Department rows become interactive filters.
replace_once(
    DASH,
    "                  <div className=\"thrs-main-dashboard__department-row\" role=\"listitem\" key={`${item.department}-${index}`}>\n                    <span className=\"thrs-main-dashboard__department-name\">\n                      <i style={{ backgroundColor: departmentColors[index % departmentColors.length] }} />\n                      <span title={item.department}>{item.department}</span>\n                    </span>\n                    <strong>{count}</strong>\n                    <small>({percent}%)</small>\n                  </div>",
    "                  <button type=\"button\" className={`thrs-main-dashboard__department-row ${selectedDepartment === item.department ? 'is-selected' : ''}`} key={`${item.department}-${index}`} onClick={() => setSelectedDepartment((current) => current === item.department ? null : item.department)} aria-pressed={selectedDepartment === item.department}>\n                    <span className=\"thrs-main-dashboard__department-name\">\n                      <i style={{ backgroundColor: departmentColors[index % departmentColors.length] }} />\n                      <span title={item.department}>{item.department}</span>\n                    </span>\n                    <strong>{count}</strong>\n                    <small>({percent}%)</small>\n                  </button>",
    'department-filter'
)

# Decision tools.
replace_once(
    DASH,
    '<section className="thrs-main-dashboard__v3-action-center thrs-main-dashboard__v6-decision-console">',
    '<section className={`thrs-main-dashboard__v3-action-center thrs-main-dashboard__v6-decision-console ${urgentOnly ? \'is-urgent-only\' : \'\'}`}>',
    'urgent-class'
)
decision_anchor = "          <p>{language === 'ar' ? 'الأولوية أولًا: استثناءات الحضور، الموافقات، ثم الأوامر التنفيذية.' : 'Priority first: attendance exceptions, approvals, then executive commands.'}</p>"
decision_tools = decision_anchor + "\n          <div className=\"thrs-main-dashboard__v7-decision-tools\">\n            <button type=\"button\" className={urgentOnly ? 'is-active' : ''} onClick={() => setUrgentOnly((value) => !value)} aria-pressed={urgentOnly}><SlidersHorizontal size={14} aria-hidden=\"true\" />{language === 'ar' ? 'العاجل فقط' : 'Urgent only'}</button>\n            <button type=\"button\" onClick={() => setFocusMode(focusMode === 'decisions' ? 'overview' : 'decisions')} aria-pressed={focusMode === 'decisions'}><Maximize2 size={14} aria-hidden=\"true\" />{focusMode === 'decisions' ? (language === 'ar' ? 'إنهاء التركيز' : 'Exit focus') : (language === 'ar' ? 'وضع التركيز' : 'Focus mode')}</button>\n          </div>"
replace_once(DASH, decision_anchor, decision_tools, 'decision-tools')

# Smart business empty-state props on dashboard widgets.
replace_once(DASH, "          <ClientStatsWidget\n            className=", "          <ClientStatsWidget\n            executiveMode\n            className=", 'client-executive-mode')
replace_once(DASH, "              activeProjects: copy.activeProjects,\n              unavailable:", "              activeProjects: copy.activeProjects,\n              executiveEmpty: language === 'ar' ? 'لا توجد حركة عملاء أو مشاريع نشطة الآن' : 'No active client or project activity right now',\n              executiveEmptyHint: language === 'ar' ? 'ستظهر المؤشرات تلقائيًا عند وصول بيانات جديدة.' : 'Signals will appear automatically when new activity is available.',\n              unavailable:", 'client-empty-copy')
replace_once(DASH, "          <DeliveryMetricsWidget\n            className=", "          <DeliveryMetricsWidget\n            executiveMode\n            className=", 'delivery-executive-mode')
replace_once(DASH, "              totalDelivered: copy.totalDelivered,\n              unavailable:", "              totalDelivered: copy.totalDelivered,\n              executiveEmpty: language === 'ar' ? 'لا توجد حركة تسليم نشطة الآن' : 'No active delivery movement right now',\n              executiveEmptyHint: language === 'ar' ? 'سيظهر أداء التسليم هنا فور توفر نشاط مشاريع.' : 'Delivery performance will appear here as project activity arrives.',\n              unavailable:", 'delivery-empty-copy')
# Only the business pulse SatisfactionWidget (last occurrence) receives executiveMode.
needle = "          <SatisfactionWidget\n            className=\"thrs-main-dashboard__integration-widget\""
if updated[DASH].count(needle) != 1:
    raise SystemExit(f'ANCHOR FAIL [satisfaction-executive-mode] found {updated[DASH].count(needle)}')
updated[DASH] = updated[DASH].replace(needle, "          <SatisfactionWidget\n            executiveMode\n            className=\"thrs-main-dashboard__integration-widget\"", 1)
# Last noRecords block is business satisfaction; replace one occurrence after executiveMode by scoped split.
marker = "            executiveMode\n            className=\"thrs-main-dashboard__integration-widget\""
pos = updated[DASH].find(marker)
if pos < 0:
    raise SystemExit('ANCHOR FAIL [satisfaction-marker]')
head, tail = updated[DASH][:pos], updated[DASH][pos:]
sat_copy_old = "              noRecords: copy.noSatisfaction,\n              unavailable:"
sat_copy_new = "              noRecords: copy.noSatisfaction,\n              executiveEmpty: language === 'ar' ? 'لا توجد تقييمات عملاء جديدة الآن' : 'No new client satisfaction signals right now',\n              executiveEmptyHint: language === 'ar' ? 'ستظهر الإشارات هنا عند وصول تقييمات جديدة.' : 'New satisfaction signals will surface here automatically.',\n              unavailable:"
if tail.count(sat_copy_old) < 1:
    raise SystemExit('ANCHOR FAIL [satisfaction-empty-copy]')
tail = tail.replace(sat_copy_old, sat_copy_new, 1)
updated[DASH] = head + tail

# Command palette before main close.
main_close = "      </section>\n    </main>\n  );\n};\n\nexport default ExecutiveDashboard;"
palette = "      </section>\n\n      {commandOpen ? (\n        <div className=\"thrs-main-dashboard__v7-command-backdrop\" onMouseDown={() => setCommandOpen(false)}>\n          <section className=\"thrs-main-dashboard__v7-command-palette\" role=\"dialog\" aria-modal=\"true\" aria-label={language === 'ar' ? 'لوحة الأوامر التنفيذية' : 'Executive command palette'} onMouseDown={(event) => event.stopPropagation()}>\n            <header>\n              <div><span><Command size={15} aria-hidden=\"true\" />{language === 'ar' ? 'أوامر سريعة' : 'Quick commands'}</span><strong>{language === 'ar' ? 'إلى أين تريد أن تذهب؟' : 'Where do you want to go?'}</strong></div>\n              <button type=\"button\" onClick={() => setCommandOpen(false)} aria-label={language === 'ar' ? 'إغلاق' : 'Close'}><X size={18} aria-hidden=\"true\" /></button>\n            </header>\n            <div className=\"thrs-main-dashboard__v7-command-grid\">\n              {[['/attendance', Clock, language === 'ar' ? 'مراجعة الحضور' : 'Review attendance'], ['/employees', Users, copy.employeeManagement], ['/approvals', UserCheck, copy.pendingApprovals], ['/reports', BarChart3, copy.reports], ['/payroll', Wallet, copy.payroll], ['/recruitment', Briefcase, copy.recruitment]].map(([to, Icon, label]) => (\n                <Link key={to} to={to} onClick={() => setCommandOpen(false)}><Icon size={18} aria-hidden=\"true\" /><span><strong>{label}</strong></span></Link>\n              ))}\n            </div>\n            <footer><span>{language === 'ar' ? 'اختصار لوحة المفاتيح' : 'Keyboard shortcut'}</span><kbd>⌘ K</kbd></footer>\n          </section>\n        </div>\n      ) : null}\n    </main>\n  );\n};\n\nexport default ExecutiveDashboard;"
replace_once(DASH, main_close, palette, 'command-palette')

# ClientStatsWidget smart empty state.
replace_once(CLIENT, "const ClientStatsWidget = ({ className = '', labels = {} }) => {", "const ClientStatsWidget = ({ className = '', labels = {}, executiveMode = false }) => {", 'client-prop')
replace_once(CLIENT, "  useEffect(() => {\n    loadData();\n  }, []);\n\n  return (", "  useEffect(() => {\n    loadData();\n  }, []);\n\n  const hasActivity = Boolean(Number(state.data?.activeClients || 0) || Number(state.data?.totalProjects || 0) || Number(state.data?.activeProjects || 0));\n\n  return (", 'client-activity')
replace_once(CLIENT, "      {!state.loading && !state.unavailable && state.data ? (\n        <div className=\"thrs-integration-widget__client-grid\" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '14px' }}>", "      {!state.loading && !state.unavailable && state.data ? (\n        executiveMode && !hasActivity ? (\n          <div className=\"thrs-integration-widget__executive-empty\"><span className=\"thrs-integration-widget__executive-empty-mark\" aria-hidden=\"true\" /><strong>{labels.executiveEmpty || 'No active business activity right now'}</strong><small>{labels.executiveEmptyHint || 'Signals will appear automatically when new activity is available.'}</small></div>\n        ) : (\n        <div className=\"thrs-integration-widget__client-grid\" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '14px' }}>", 'client-empty-open')
replace_once(CLIENT, "        </div>\n      ) : null}", "        </div>\n        )\n      ) : null}", 'client-empty-close')

# DeliveryMetricsWidget smart empty state.
replace_once(DELIVERY, "const DeliveryMetricsWidget = ({ className = '', labels = {} }) => {", "const DeliveryMetricsWidget = ({ className = '', labels = {}, executiveMode = false }) => {", 'delivery-prop')
replace_once(DELIVERY, "  const onTimeRate = useMemo(() => Number(state.data?.onTimeRate || 0), [state.data]);\n", "  const onTimeRate = useMemo(() => Number(state.data?.onTimeRate || 0), [state.data]);\n  const hasActivity = Boolean(onTimeRate || Number(state.data?.avgDeliveryDays || 0) || Number(state.data?.delayedProjects || 0) || Number(state.data?.totalDelivered || 0));\n", 'delivery-activity')
replace_once(DELIVERY, "      {!state.loading && !state.unavailable && state.data ? (\n        <div className=\"thrs-integration-widget__delivery-grid\"", "      {!state.loading && !state.unavailable && state.data ? (\n        executiveMode && !hasActivity ? (\n          <div className=\"thrs-integration-widget__executive-empty\"><span className=\"thrs-integration-widget__executive-empty-mark\" aria-hidden=\"true\" /><strong>{labels.executiveEmpty || 'No active delivery movement right now'}</strong><small>{labels.executiveEmptyHint || 'Delivery signals will appear when project activity is available.'}</small></div>\n        ) : (\n        <div className=\"thrs-integration-widget__delivery-grid\"", 'delivery-empty-open')
replace_once(DELIVERY, "        </div>\n      ) : null}", "        </div>\n        )\n      ) : null}", 'delivery-empty-close')

# SatisfactionWidget smart empty state.
replace_once(SAT, "const SatisfactionWidget = ({ className = '', labels = {} }) => {", "const SatisfactionWidget = ({ className = '', labels = {}, executiveMode = false }) => {", 'sat-prop')
replace_once(SAT, "      {!state.loading && !state.unavailable ? (\n        <div className=\"thrs-integration-widget__satisfaction-grid\"", "      {!state.loading && !state.unavailable ? (\n        executiveMode && !state.rows.length ? (\n          <div className=\"thrs-integration-widget__executive-empty\"><span className=\"thrs-integration-widget__executive-empty-mark\" aria-hidden=\"true\" /><strong>{labels.executiveEmpty || 'No new client satisfaction signals right now'}</strong><small>{labels.executiveEmptyHint || 'New satisfaction signals will appear automatically.'}</small></div>\n        ) : (\n        <div className=\"thrs-integration-widget__satisfaction-grid\"", 'sat-empty-open')
replace_once(SAT, "        </div>\n      ) : null}", "        </div>\n        )\n      ) : null}", 'sat-empty-close')

# Validate that V7 is actually activated before writing anything.
required = [
    (DASH, 'thrs-main-dashboard--v7'),
    (DASH, 'thrs-main-dashboard__v7-briefing'),
    (DASH, 'setCommandOpen'),
    (CLIENT, 'executiveMode'),
    (DELIVERY, 'executiveMode'),
    (SAT, 'executiveMode'),
]
for path, token in required:
    if token not in updated[path]:
        raise SystemExit(f'VALIDATION FAIL: {token} missing in {path}')

# All validations passed; write atomically per file.
for path in FILES:
    tmp = path.with_suffix(path.suffix + '.v7tmp')
    tmp.write_text(updated[path], encoding='utf-8')
    tmp.replace(path)

print('V7_SAFE_PATCH: PASS')
print('Changed:')
for path in FILES:
    print(f'- {path}')
