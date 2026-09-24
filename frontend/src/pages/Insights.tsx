import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { won } from '../theme/categories';

export default function Insights() {
  const now = new Date();
  const [y, setY] = useState(now.getFullYear());
  const [m, setM] = useState(now.getMonth() + 1);
  const [report, setReport] = useState<any>(null);

  const load = () => api.report(y, m).then(setReport).catch(() => setReport(null));
  useEffect(load, []);

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
          <h3>예산 초과 알림</h3>
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
        </>
      )}
    </div>
  );
}
