import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { won } from '../theme/categories';

export default function Insights() {
  const now = new Date();
  const [y, setY] = useState(now.getFullYear());
  const [m, setM] = useState(now.getMonth() + 1);
  const [report, setReport] = useState<any>(null);
  const [past, setPast] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => api.report(y, m).then(setReport).catch(() => setReport(null));

  useEffect(() => {
    setLoading(true);
    const jobs: Promise<any>[] = [load()];
    const nowD = new Date();
    for (let i = 0; i < 6; i++) {
      const d = new Date(nowD.getFullYear(), nowD.getMonth() - i, 1);
      jobs.push(api.report(d.getFullYear(), d.getMonth() + 1)
        .then((r: any) => ({ y: d.getFullYear(), m: d.getMonth() + 1, total: r.total_spending ?? 0,
                             alerts: (r.alerts ?? []).filter((a: any) => a.severity !== 'safe').length }))
        .catch(() => null));
    }
    Promise.all(jobs).then((rows) => {
      setPast(rows.slice(1).filter(Boolean));
      setLoading(false);
    });
  }, []);

  const jump = (yy: number, mm: number) => {
    setY(yy); setM(mm);
    api.report(yy, mm).then(setReport).catch(() => setReport(null));
  };

  if (loading) {
    return (
      <div>
        <div className="skel" style={{ width: 280, height: 36 }} />
        <div className="grid3" style={{ marginTop: 12 }}>
          <div className="skel" style={{ height: 120 }} />
          <div className="skel" style={{ height: 120 }} />
          <div className="skel" style={{ height: 120 }} />
        </div>
        <div className="skel" style={{ height: 200, marginTop: 12 }} />
        <p className="muted">리포트를 불러오는 중…</p>
      </div>
    );
  }

  return (
    <div>
      <div className="toolbar">
        <input type="number" value={y} onChange={(e) => setY(Number(e.target.value))} style={{ width: 90 }} />
        <input type="number" value={m} min={1} max={12} onChange={(e) => setM(Number(e.target.value))} style={{ width: 70 }} />
        <button onClick={load}>리포트 조회</button>
      </div>
      {!report && <p className="muted">리포트가 없습니다.</p>}
      {report && (
        <>
          <h3>{y}년 {m}월 요약 — 총 {won(report.total_spending ?? 0)}</h3>
          <h4>예산 초과 알림</h4>
          {(report.alerts ?? []).filter((a: any) => a.severity !== 'safe').map((a: any) => (
            <div key={a.category} className={`alert ${a.severity}`}>
              <b>{a.category}</b> — {won(a.actual_amount)} / {won(a.budgeted_amount)} ({a.percentage_used}%)
            </div>
          ))}
          {(report.alerts ?? []).filter((a: any) => a.severity !== 'safe').length === 0 && <p className="muted">초과/임박 항목 없음 🎉</p>}

          <h3>절약 팁 (데이터 기반)</h3>
          <div className="tips">
            {(report.tips ?? []).map((t: any, i: number) => (
              <div key={i} className="tip-card">
                <span className="tip-cat">{t.category}</span>
                <p>{t.tip}</p>
                <p className="save">예상 절약 {won(t.potential_savings_amount)}</p>
                <p className="based">근거: {t.based_on}</p>
              </div>
            ))}
          </div>
          <h3>월별 리포트 내역 (최근 6개월)</h3>
          <table className="tbl">
            <tbody>
              {past.map((p) => (
                <tr key={`${p.y}-${p.m}`}>
                  <td><b>{p.y}년 {p.m}월</b></td>
                  <td className="num">{won(p.total)}</td>
                  <td>{p.alerts > 0 ? `⚠️ 알림 ${p.alerts}건` : '✅ 정상'}</td>
                  <td><button onClick={() => jump(p.y, p.m)}>보기</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
