import { useEffect, useState } from 'react';
import { API_BASE, api } from '../api/client';
import { CategoryBadge } from '../components/ui';

const CATS = ['식비', '카페', '교통', '구독', '쇼핑', '의료', '고정비', '여가', '교육', '기타'];

export default function Transactions() {
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [cat, setCat] = useState('');
  const [onlyReview, setOnlyReview] = useState(false);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 20;

  const load = (p0 = page) => {
    const p: Record<string, string> = { limit: String(PAGE_SIZE), offset: String(p0 * PAGE_SIZE) };
    if (q) p.q = q;
    if (cat) p.category = cat;
    if (onlyReview) p.needs_review = 'true';
    api.transactions(p).then((r) => { setRows(r.items ?? []); setTotal(r.total ?? 0); })
      .catch(() => { setRows([]); setTotal(0); });
  };

  useEffect(() => { load(0); }, []);

  const go = (np: number) => { setPage(np); load(np); };
  const search = () => { setPage(0); load(0); };
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

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
        <button onClick={search}>조회</button>
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
      <div className="pager">
        <button className="page-btn" disabled={page <= 0} onClick={() => go(page - 1)}>‹ 이전</button>
        {Array.from({ length: pages }, (_, i) => i)
          .filter((i) => i === 0 || i === pages - 1 || Math.abs(i - page) <= 2)
          .reduce<(number | '…')[]>( (acc, i, idx, arr) => {
            if (idx > 0 && i - (arr[idx - 1] as number) > 1) acc.push('…');
            acc.push(i);
            return acc;
          }, [])
          .map((i, k) => i === '…'
            ? <span key={`e${k}`} className="page-ellipsis">…</span>
            : <button key={i} className={`page-btn${i === page ? ' on' : ''}`} onClick={() => go(i as number)}>{(i as number) + 1}</button>)}
        <button className="page-btn" disabled={page + 1 >= pages} onClick={() => go(page + 1)}>다음 ›</button>
        <span className="muted">총 {total}건</span>
      </div>
    </div>
  );
}
