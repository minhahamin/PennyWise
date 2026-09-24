import { categoryColor, won } from '../theme/categories';

export function StatCard({ label, value, sub, danger }: { label: string; value: string; sub?: string; danger?: boolean }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className="value" style={{ color: danger ? 'var(--danger)' : 'var(--ink)' }}>{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

export function CategoryBadge({ category, confidence }: { category: string; confidence: number }) {
  const needsReview = confidence < 0.6;
  return (
    <span className="badge" style={{ background: categoryColor(category) + '22', borderColor: categoryColor(category), color: 'var(--ink)' }}>
      {category}
      {needsReview && <b title="AI 확신도 낮음 — 확인 필요"> · 확인 필요</b>}
    </span>
  );
}

export function BudgetBar({ category, pct }: { category: string; pct: number }) {
  const over = pct >= 100;
  const warn = pct >= 80 && !over;
  return (
    <div className="budget-row">
      <span className="budget-cat">{category}</span>
      <div className="budget-track">
        <div
          className="budget-fill"
          style={{ width: `${Math.min(pct, 100)}%`, background: over ? 'var(--danger)' : warn ? 'var(--warn)' : categoryColor(category) }}
        />
      </div>
      <span className="budget-pct" style={{ color: over ? 'var(--danger)' : 'var(--ink)' }}>{pct.toFixed(0)}%</span>
    </div>
  );
}

export { won };
