import { useEffect, useState } from 'react';
import { API_BASE, api } from '../api/client';
import { CategoryBadge } from '../components/ui';

const CATS = ['식비', '카페', '교통', '구독', '쇼핑', '의료', '고정비', '여가', '교육', '기타'];

export default function Transactions() {
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [cat, setCat] = useState('');
  const [onlyReview, setOnlyReview] = useState(false);

  const load = () => {
    const p: Record<string, string> = {};
    if (q) p.q = q;
    if (cat) p.category = cat;
    if (onlyReview) p.needs_review = 'true';
    api.transactions(p).then(setRows).catch(() => setRows([]));
  };

  useEffect(load, []);

  const fix = async (id: number, category: string) => {
    await api.correct(id, category);
    load();
  };

  return (
    <div>
      <div className="toolbar">
        <input placeholder="가맹점 검색" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={cat} onChange={(e) => setCat(e.target.value)}>
          <option value="">전체 카테고리</option>
          {CATS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <label><input type="checkbox" checked={onlyReview} onChange={(e) => setOnlyReview(e.target.checked)} /> 확인 필요만</label>
        <button onClick={load}>조회</button>
      </div>
      <table className="tbl">
        <thead><tr><th>날짜</th><th>가맹점</th><th>금액</th><th>카테고리</th><th>출처</th><th>수정</th></tr></thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id}>
              <td>{t.date}</td>
              <td>
                {t.source === 'receipt' && t.receipt_image_path && (
                  <img src={`${API_BASE}/uploads/${t.receipt_image_path.split(/[\\/]/).pop()}`} alt="영수증" width={36} height={36} style={{ objectFit: 'cover', borderRadius: 6, marginRight: 6, verticalAlign: 'middle' }} />
                )}
                {t.merchant}
              </td>
              <td className="num">{Number(t.amount).toLocaleString()}원</td>
              <td><CategoryBadge category={t.category} confidence={t.confidence} /></td>
              <td>{t.source}</td>
              <td>
                <select defaultValue="" onChange={(e) => e.target.value && fix(t.id, e.target.value)}>
                  <option value="">수정…</option>
                  {CATS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && <p className="muted">거래가 없습니다. 업로드 탭에서 샘플 CSV를 올려보세요.</p>}
    </div>
  );
}
