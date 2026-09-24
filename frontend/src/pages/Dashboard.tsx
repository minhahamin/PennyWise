import { useEffect, useState } from 'react';
import { Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import { categoryColor, won } from '../theme/categories';
import { BudgetBar, StatCard } from '../components/ui';

function nowYM() {
  const d = new Date();
  return { y: d.getFullYear(), m: d.getMonth() + 1 };
}

export default function Dashboard() {
  const [{ y, m }] = useState(nowYM());
  const [report, setReport] = useState<any>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    api.report(y, m).then(setReport).catch((e) => setErr(String(e)));
  }, [y, m]);

  if (err) return <p>리포트를 불러오지 못했습니다. 백엔드(8000)가 켜져 있나요? {err}</p>;
  if (!report) return <p>불러오는 중…</p>;

  const donut = Object.entries(report.category_breakdown ?? {}).map(([name, value]) => ({ name, value }));
  const change = report.comparison_to_last_month?.total_change_pct ?? 0;

  return (
    <div>
      <div className="grid3">
        <StatCard label={`${y}년 ${m}월 총 지출`} value={won(report.total_spending ?? 0)}
          sub={`전월 대비 ${change > 0 ? '+' : ''}${change}%`} danger={change > 0} />
        <StatCard label="예산 초과 항목" value={`${(report.alerts ?? []).filter((a: any) => a.severity === 'exceeded').length}건`}
          sub={`경고 ${(report.alerts ?? []).filter((a: any) => a.severity === 'warning').length}건`} />
        <StatCard label="절약 팁" value={`${(report.tips ?? []).length}개`}
          sub="인사이트 탭에서 확인" />
      </div>

      <div className="grid2">
        <section className="panel">
          <h3>카테고리별 지출</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={donut} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
                {donut.map((d) => <Cell key={d.name} fill={categoryColor(d.name)} />)}
              </Pie>
              <Tooltip formatter={(v: any) => won(Number(v))} />
            </PieChart>
          </ResponsiveContainer>
          <div className="legend">
            {donut.map((d) => <span key={d.name}><i style={{ background: categoryColor(d.name) }} />{d.name} {won(Number(d.value))}</span>)}
          </div>
        </section>

        <section className="panel">
          <h3>예산 진행률</h3>
          {(report.alerts ?? []).length === 0 && <p className="muted">설정된 예산이 없습니다. 인사이트 탭에서 예산을 설정하세요.</p>}
          {(report.alerts ?? []).map((a: any) => (
            <BudgetBar key={a.category} category={`${a.category} (${won(a.actual_amount)}/${won(a.budgeted_amount)})`} pct={a.percentage_used} />
          ))}
        </section>
      </div>

      <section className="panel" style={{ marginTop: 16 }}>
        <h3>카테고리 Top 지출</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={donut.map((d) => ({ ...d }))}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip formatter={(v: any) => won(Number(v))} />
            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
        <p className="muted">* 최근 6개월 추이는 거래가 쌓이면 /transactions 기반으로 확장됩니다.</p>
      </section>
    </div>
  );
}
