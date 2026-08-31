#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
BACKEND = ROOT / 'backend/src/controllers/dashboard.controller.js'
SERVICE = ROOT / 'frontend/src/services/dashboard.service.js'
HOOK = ROOT / 'frontend/src/hooks/useDashboardData.js'
DASH = ROOT / 'frontend/src/pages/dashboards/ExecutiveDashboard.jsx'
CSS = ROOT / 'frontend/src/styles/thrs-main-dashboard-v7-1.css'
FILES = [BACKEND, SERVICE, HOOK, DASH]

for path in FILES:
    if not path.exists():
        raise SystemExit(f'MISSING: {path}')
if not CSS.exists():
    raise SystemExit(f'MISSING: {CSS}')

originals = {p: p.read_text(encoding='utf-8') for p in FILES}
updated = dict(originals)

def replace_once(path, old, new, label):
    count = updated[path].count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR FAIL [{label}] expected 1 match, found {count}')
    updated[path] = updated[path].replace(old, new, 1)

def replace_between(path, start_marker, end_marker, replacement, label):
    text = updated[path]
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise SystemExit(f'ANCHOR FAIL [{label}]')
    updated[path] = text[:start] + replacement + text[end:]

if 'thrs-main-dashboard--v7' not in updated[DASH]:
    raise SystemExit('STATE FAIL: V7 is not active')

# ---------------- Backend attendance intelligence ----------------
anchor = "const { getScopeFilter, getEmployeeScopeFilter } = require('../utils/scopeFilter');\n"
helpers = anchor + r'''
const DASHBOARD_TIME_ZONE = process.env.COMPANY_TIMEZONE || 'Africa/Cairo';
const dashboardPad2 = (v) => String(v).padStart(2, '0');

const dashboardDateKey = (value) => {
  const date = value instanceof Date ? value : new Date(value);
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: DASHBOARD_TIME_ZONE,
    year: 'numeric', month: '2-digit', day: '2-digit'
  });
  const parts = Object.fromEntries(formatter.formatToParts(date).map((part) => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
};

const parseDashboardDate = (value) => {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    const now = new Date();
    return { key: dashboardDateKey(now), date: new Date(now.getFullYear(), now.getMonth(), now.getDate()) };
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  return { key: `${year}-${dashboardPad2(month)}-${dashboardPad2(day)}`, date: new Date(year, month - 1, day) };
};

const shiftDashboardKey = (key, days) => {
  const [y, m, d] = String(key).split('-').map(Number);
  const date = new Date(Date.UTC(y, m - 1, d + Number(days || 0), 12));
  return `${date.getUTCFullYear()}-${dashboardPad2(date.getUTCMonth() + 1)}-${dashboardPad2(date.getUTCDate())}`;
};

const importHasDate = (item, key) => (item?.rows || []).some((row) =>
  Array.isArray(row.finalDailyRecords) && row.finalDailyRecords.some((day) => String(day?.date || '').slice(0, 10) === key)
);

const summarizeImportDay = (item, key) => {
  const result = { records: 0, eligible: 0, present: 0, absent: 0, late: 0 };
  const offStatuses = new Set(['WEEKLY_OFF', 'OFFICIAL_HOLIDAY', 'CUSTOM_OFF', 'OFF_DAY_OVERTIME', 'OFF_DAY_INCOMPLETE']);
  for (const row of item?.rows || []) {
    if (!row.employeeId || !Array.isArray(row.finalDailyRecords)) continue;
    const day = row.finalDailyRecords.find((d) => String(d?.date || '').slice(0, 10) === key);
    if (!day) continue;
    result.records += 1;
    const status = String(day.status || '').toUpperCase();
    const isOff = day.isWorkingDay === false || offStatuses.has(status);
    const isAbsent = !isOff && status === 'ABSENT';
    const isLate = !isOff && (status === 'LATE' || status === 'LATE_AND_EARLY_DEPARTURE' || Number(day.morningLateMinutes || 0) > 0);
    const isPresent = !isOff && !isAbsent && (Boolean(day.checkIn) || ['PRESENT', 'WORK', 'LATE', 'EARLY_DEPARTURE', 'LATE_AND_EARLY_DEPARTURE', 'INCOMPLETE'].includes(status));
    if (!isOff) result.eligible += 1;
    if (isPresent) result.present += 1;
    if (isAbsent) result.absent += 1;
    if (isLate) result.late += 1;
  }
  return result;
};

const latestImportDate = (item) => {
  let latest = '';
  for (const row of item?.rows || []) {
    for (const day of Array.isArray(row.finalDailyRecords) ? row.finalDailyRecords : []) {
      const key = String(day?.date || '').slice(0, 10);
      if (/^\d{4}-\d{2}-\d{2}$/.test(key) && key > latest) latest = key;
    }
  }
  return latest;
};

'''
replace_once(BACKEND, anchor, helpers, 'backend-helpers')

new_exec = r'''const getExecutiveStats = async (req) => {
  const selected = parseDashboardDate(req.query?.date);
  const range = String(req.query?.range || '7d').toLowerCase();
  const rangeDays = range === 'today' || range === '1d' ? 1 : range === '30d' ? 30 : 7;
  const selectedKey = selected.key;
  const selectedDate = selected.date;
  const currentYear = selectedDate.getFullYear();
  const currentMonth = selectedDate.getMonth() + 1;
  const rangeStartKey = shiftDashboardKey(selectedKey, -(rangeDays - 1));

  const [
    totalEmployees,
    activeEmployees,
    newHiresThisMonth,
    terminatedThisMonth,
    pendingLeaveRequests,
    pendingCorrections,
    departmentStats,
    departments,
    payrollThisMonth,
    onLeave,
    approvedImports,
    latestApprovedImport,
  ] = await Promise.all([
    prisma.employee.count(),
    prisma.employee.count({ where: { status: 'ACTIVE' } }),
    prisma.employee.count({ where: { hireDate: { gte: new Date(currentYear, currentMonth - 1, 1), lt: new Date(currentYear, currentMonth, 1) } } }),
    prisma.employee.count({ where: { status: 'TERMINATED', updatedAt: { gte: new Date(currentYear, currentMonth - 1, 1), lt: new Date(currentYear, currentMonth, 1) } } }),
    prisma.leave.count({ where: { status: 'PENDING' } }),
    prisma.attendanceCorrection.count({ where: { status: 'PENDING' } }).catch(() => 0),
    prisma.employee.groupBy({ by: ['departmentId'], _count: { id: true }, where: { status: 'ACTIVE' } }),
    prisma.department.findMany(),
    prisma.payroll.aggregate({ where: { month: currentMonth, year: currentYear }, _sum: { netSalary: true } }),
    prisma.leave.count({ where: { status: 'APPROVED', startDate: { lte: selectedDate }, endDate: { gte: selectedDate } } }),
    prisma.attendanceImport.findMany({
      where: { status: 'APPROVED' },
      include: { rows: { select: { employeeId: true, finalDailyRecords: true } } },
      orderBy: [{ approvedAt: 'desc' }, { createdAt: 'desc' }],
      take: 24,
    }),
    prisma.attendanceImport.findFirst({
      where: { status: 'APPROVED' },
      include: { rows: { select: { finalDailyRecords: true } } },
      orderBy: [{ periodEnd: 'desc' }, { approvedAt: 'desc' }],
    }),
  ]);

  const selectedImport = approvedImports.find((item) => importHasDate(item, selectedKey)) || null;
  const selectedSummary = selectedImport ? summarizeImportDay(selectedImport, selectedKey) : { records: 0, eligible: 0, present: 0, absent: 0, late: 0 };
  const hasApprovedAttendance = Boolean(selectedImport && selectedSummary.records > 0);
  const latestAvailableDate = latestImportDate(latestApprovedImport);

  const attendanceTrend = [];
  for (let i = rangeDays - 1; i >= 0; i--) {
    const key = shiftDashboardKey(selectedKey, -i);
    const sourceImport = approvedImports.find((item) => importHasDate(item, key));
    const summary = sourceImport ? summarizeImportDay(sourceImport, key) : { eligible: 0, present: 0, absent: 0, late: 0 };
    attendanceTrend.push({
      date: key,
      present: summary.present,
      absent: summary.absent,
      late: summary.late,
      eligible: summary.eligible,
      source: sourceImport ? 'APPROVED_IMPORT' : 'NONE',
    });
  }

  const turnoverRate = totalEmployees > 0 ? Number(((terminatedThisMonth / totalEmployees) * 100).toFixed(1)) : 0;
  const departmentDistribution = departmentStats.map((d) => ({
    department: departments.find((dep) => dep.id === d.departmentId)?.name || 'غير محدد',
    count: d._count.id,
  }));
  const coveragePercent = activeEmployees > 0 ? Number(((selectedSummary.records / activeEmployees) * 100).toFixed(1)) : 0;

  return {
    selectedDate: selectedKey,
    attendanceSource: {
      hasData: hasApprovedAttendance,
      type: hasApprovedAttendance ? 'APPROVED_IMPORT' : 'NONE',
      label: hasApprovedAttendance ? 'Approved attendance sheet' : 'No approved attendance data',
      importId: selectedImport?.id || null,
      fileName: selectedImport?.fileName || null,
      approvedAt: selectedImport?.approvedAt || null,
      latestAvailableDate: latestAvailableDate || null,
      coverageCount: selectedSummary.records,
      coverageTotal: activeEmployees,
      coveragePercent,
      rangeDays,
    },
    stats: {
      totalEmployees,
      activeEmployees,
      newHiresThisMonth,
      turnoverRate,
      presentToday: selectedSummary.present,
      absentToday: selectedSummary.absent,
      lateToday: selectedSummary.late,
      onLeave,
      attendanceEligible: selectedSummary.eligible,
      pendingLeaveRequests,
      totalPayrollThisMonth: payrollThisMonth._sum.netSalary || 0,
    },
    departmentDistribution,
    attendanceTrend,
    pendingApprovals: { leaves: pendingLeaveRequests, corrections: pendingCorrections },
  };
};

'''
replace_between(BACKEND, 'const getExecutiveStats = async (req) => {', '// HR dashboard (HR_ADMIN, HR_MANAGER)', new_exec, 'executive-stats')

# ---------------- Frontend data plumbing ----------------
replace_once(SERVICE,
"  async getStats() {\n    return api.get('/dashboard/stats');\n  },",
"  async getStats(params = {}) {\n    return api.get('/dashboard/stats', { params });\n  },",
'dashboard-service')

replace_once(HOOK,
"const useDashboardData = () => {",
"const useDashboardData = ({ date, range = '7d' } = {}) => {",
'hook-signature')
replace_once(HOOK,
"      const response = await dashboardService.getStats();",
"      const response = await dashboardService.getStats({ date, range });",
'hook-request')
replace_once(HOOK,
"  }, []);",
"  }, [date, range]);",
'hook-deps')

# ---------------- V7.1 premium date intelligence ----------------
replace_once(DASH,
"import '../../styles/thrs-main-dashboard-v7.css';",
"import '../../styles/thrs-main-dashboard-v7.css';\nimport '../../styles/thrs-main-dashboard-v7-1.css';",
'v7-1-css')

replace_once(DASH,
"  const { data, loading, error } = useDashboardData();\n  const [timeRange, setTimeRange] = useState('7d');",
"  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));\n  const [timeRange, setTimeRange] = useState('7d');\n  const { data, loading, error, refetch } = useDashboardData({ date: selectedDate, range: timeRange });",
'filter-state')

replace_once(DASH,
"  const formattedDate = now.toLocaleDateString(language === 'ar' ? 'ar-EG' : 'en-US', {",
"  const selectedDateObject = new Date(`${selectedDate}T12:00:00`);\n  const formattedDate = selectedDateObject.toLocaleDateString(language === 'ar' ? 'ar-EG' : 'en-US', {",
'formatted-date')

replace_once(DASH,
"  const attendanceRate = activeEmployees > 0 ? Math.round((presentToday / activeEmployees) * 100) : 0;",
"  const attendanceEligible = Number(stats.attendanceEligible || 0);\n  const attendanceRate = attendanceEligible > 0 ? Math.round((presentToday / attendanceEligible) * 100) : 0;",
'attendance-rate')

replace_once(DASH,
"  const visibleAttendanceTrend = timeRange === 'today' ? attendanceTrend.slice(-1) : attendanceTrend.slice(-7);",
"  const visibleAttendanceTrend = timeRange === 'today' ? attendanceTrend.slice(-1) : timeRange === '30d' ? attendanceTrend.slice(-30) : attendanceTrend.slice(-7);\n  const attendanceSource = data?.attendanceSource || {};",
'visible-trend')

replace_once(DASH,
"thrs-main-dashboard--v6 thrs-main-dashboard--v7 fade-in",
"thrs-main-dashboard--v6 thrs-main-dashboard--v7 thrs-main-dashboard--v7-1 fade-in",
'root-v7-1')

replace_once(DASH,
"  return (\n    <main className=",
"  const shiftSelectedDate = (days) => {\n    const date = new Date(`${selectedDate}T12:00:00`);\n    date.setDate(date.getDate() + days);\n    setSelectedDate(date.toISOString().slice(0, 10));\n  };\n  const todayKey = new Date().toISOString().slice(0, 10);\n  const yesterdayDate = new Date();\n  yesterdayDate.setDate(yesterdayDate.getDate() - 1);\n  const yesterdayKey = yesterdayDate.toISOString().slice(0, 10);\n\n  return (\n    <main className=",
'date-helpers')

datebar_anchor = "      </header>\n\n      <section className=\"thrs-main-dashboard__v7-briefing\""
datebar = """      </header>\n\n      <section className=\"thrs-main-dashboard__v7-1-datebar\" aria-label={language === 'ar' ? 'فلتر تاريخ الحضور' : 'Attendance date filter'}>\n        <div className=\"thrs-main-dashboard__v7-1-date-nav\">\n          <button type=\"button\" onClick={() => shiftSelectedDate(-1)}>‹</button>\n          <label><Calendar size={16} aria-hidden=\"true\" /><input type=\"date\" value={selectedDate} max={todayKey} onChange={(event) => setSelectedDate(event.target.value)} /></label>\n          <button type=\"button\" onClick={() => shiftSelectedDate(1)} disabled={selectedDate >= todayKey}>›</button>\n        </div>\n        <div className=\"thrs-main-dashboard__v7-1-presets\">\n          <button type=\"button\" className={selectedDate === todayKey ? 'is-active' : ''} onClick={() => setSelectedDate(todayKey)}>{language === 'ar' ? 'اليوم' : 'Today'}</button>\n          <button type=\"button\" className={selectedDate === yesterdayKey ? 'is-active' : ''} onClick={() => setSelectedDate(yesterdayKey)}>{language === 'ar' ? 'أمس' : 'Yesterday'}</button>\n          <button type=\"button\" disabled={!attendanceSource.latestAvailableDate} onClick={() => attendanceSource.latestAvailableDate && setSelectedDate(attendanceSource.latestAvailableDate)}>{language === 'ar' ? 'آخر حضور' : 'Latest attendance'}</button>\n          <button type=\"button\" onClick={refetch}>{language === 'ar' ? 'تحديث' : 'Refresh'}</button>\n        </div>\n        <div className={`thrs-main-dashboard__v7-1-source ${attendanceSource.hasData ? 'is-approved' : 'is-missing'}`}>\n          <span aria-hidden=\"true\" />\n          <div><small>{language === 'ar' ? 'مصدر البيانات' : 'Data source'}</small><strong>{attendanceSource.hasData ? (language === 'ar' ? 'شيت حضور معتمد' : 'Approved attendance sheet') : (language === 'ar' ? 'لا توجد بيانات معتمدة' : 'No approved data')}</strong>{attendanceSource.fileName ? <em>{attendanceSource.fileName}</em> : null}</div>\n        </div>\n        <div className=\"thrs-main-dashboard__v7-1-coverage\">\n          <div><span>{language === 'ar' ? 'التغطية' : 'Coverage'}</span><strong>{attendanceSource.coverageCount || 0}/{attendanceSource.coverageTotal || activeEmployees}</strong></div>\n          <div className=\"thrs-main-dashboard__v7-1-coverage-track\"><span style={{ width: `${Math.min(Number(attendanceSource.coveragePercent || 0), 100)}%` }} /></div>\n          <small>{Number(attendanceSource.coveragePercent || 0).toFixed(1)}%</small>\n        </div>\n      </section>\n\n      {!attendanceSource.hasData ? (\n        <section className=\"thrs-main-dashboard__v7-1-no-data\">\n          <div><span>{language === 'ar' ? 'لا توجد بيانات حضور لهذا التاريخ' : 'No attendance data for this date'}</span><strong>{formattedDate}</strong><small>{attendanceSource.latestAvailableDate ? (language === 'ar' ? `آخر تاريخ متاح: ${attendanceSource.latestAvailableDate}` : `Latest available: ${attendanceSource.latestAvailableDate}`) : (language === 'ar' ? 'اعتمد شيت حضور ليظهر هنا.' : 'Approve an attendance sheet to populate this view.')}</small></div>\n          {attendanceSource.latestAvailableDate ? <button type=\"button\" onClick={() => setSelectedDate(attendanceSource.latestAvailableDate)}>{language === 'ar' ? 'عرض آخر حضور' : 'View latest attendance'}</button> : null}\n        </section>\n      ) : null}\n\n      <section className=\"thrs-main-dashboard__v7-briefing\""" 
replace_once(DASH, datebar_anchor, datebar, 'datebar')

replace_once(DASH,
"              <button type=\"button\" className={timeRange === '7d' ? 'is-active' : ''} onClick={() => setTimeRange('7d')}>{language === 'ar' ? '٧ أيام' : '7 days'}</button>\n            </div>",
"              <button type=\"button\" className={timeRange === '7d' ? 'is-active' : ''} onClick={() => setTimeRange('7d')}>{language === 'ar' ? '٧ أيام' : '7 days'}</button>\n              <button type=\"button\" className={timeRange === '30d' ? 'is-active' : ''} onClick={() => setTimeRange('30d')}>{language === 'ar' ? '٣٠ يوم' : '30 days'}</button>\n            </div>",
'range-30d')

replace_once(DASH,
"            <h2>{language === 'ar' ? 'اتجاهات اليوم في مشهد واحد' : 'Today’s workforce signals in one view'}</h2>",
"            <h2>{language === 'ar' ? 'اتجاهات الحضور حسب التاريخ المختار' : 'Attendance intelligence for the selected date'}</h2>\n            <small className=\"thrs-main-dashboard__v7-1-intelligence-source\">{attendanceSource.hasData ? (language === 'ar' ? 'الأرقام محسوبة من الشيت المعتمد نفسه.' : 'Metrics are calculated from the approved attendance sheet.') : (language === 'ar' ? 'لا توجد بيانات حضور موثوقة لهذا التاريخ.' : 'No trusted attendance source for this date.')}</small>",
'intelligence-copy')

for path, needles in {
    BACKEND: ['attendanceSource:', 'summarizeImportDay', 'attendanceEligible'],
    SERVICE: ["api.get('/dashboard/stats', { params })"],
    HOOK: ['dashboardService.getStats({ date, range })'],
    DASH: ['thrs-main-dashboard--v7-1', 'thrs-main-dashboard__v7-1-datebar', "timeRange === '30d'"],
}.items():
    for needle in needles:
        if needle not in updated[path]:
            raise SystemExit(f'VALIDATION FAIL: {needle} missing from {path}')

for path in FILES:
    path.write_text(updated[path], encoding='utf-8')

print('V7.1 Attendance Intelligence Safe Applier: PASS')
for path in FILES:
    if originals[path] != updated[path]:
        print(f' - {path}')
