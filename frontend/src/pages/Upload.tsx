import { useEffect, useState } from 'react';
import { API_BASE, api } from '../api/client';

const STAGES = ['분석중', '분류중', '저장중', '완료'];

export default function Upload() {
  const [stage, setStage] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [drag, setDrag] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [lightbox, setLightbox] = useState<string | null>(null);
  const [preview, setPreview] = useState<any | null>(null);

  const loadHistory = () => api.uploadHistory().then(setHistory).catch(() => {});
  useEffect(() => { loadHistory(); }, []);

  const runStages = async (fn: () => Promise<any>) => {
    setResult(null);
    for (const s of STAGES) {
      setStage(s);
      await new Promise((r) => setTimeout(r, 250));
    }
    try {
      setResult(await fn());
      loadHistory();
    } catch (e: any) {
      setResult({ error: String(e.message ?? e) });
    } finally {
      setStage('완료');
    }
  };

  const onCsv = (f: File | undefined) => f && runStages(() => api.uploadCsv(f));
  const onReceipt = (f: File | undefined) => f && runStages(() => api.uploadReceipt(f));

  return (
    <div className="grid2">
      <section className="panel">
        <h3>CSV 업로드 (드래그앤드롭)</h3>
        <div
          className={`drop ${drag ? 'over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); onCsv(e.dataTransfer.files?.[0]); }}
        >
          여기로 CSV 파일을 드래그하거나
          <label className="file-btn">
            📂 CSV 파일 선택
            <input type="file" accept=".csv" hidden onChange={(e) => onCsv(e.target.files?.[0])} />
          </label>
        </div>
        <p className="muted">정해진 양식은 없습니다. 날짜·가맹점·금액 3개 컬럼만 있으면
          은행/카드사마다 다른 헤더도 자동 매핑합니다 (애매하면 AI가 추론).
          인코딩은 UTF-8/CP949 자동 감지. 예: <code>승인일자,가맹점명,이용금액</code></p>
      </section>
      <section className="panel">
        <h3>영수증 업로드 (모바일 촬영 지원)</h3>
        <label className="file-btn">
          📸 영수증 촬영 / 선택
          <input type="file" accept="image/*" capture="environment" hidden onChange={(e) => onReceipt(e.target.files?.[0])} />
        </label>
        <p className="muted">비전 LLM이 가맹점·날짜·총액·품목을 추출합니다.</p>
      </section>
      <section className="panel">
        <h3>처리 상태: {stage || '대기 중'}</h3>
        <div className="stages">{STAGES.map((s) => <span key={s} className={STAGES.indexOf(s) <= STAGES.indexOf(stage) ? 'on' : ''}>{s}</span>)}</div>
        {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      </section>
      <section className="panel" style={{ gridColumn: '1 / -1' }}>
        <h3>업로드 내역</h3>
        {history.length === 0 && <p className="muted">아직 업로드 내역이 없습니다.</p>}
        <table className="tbl">
          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td>{h.kind === 'csv' ? '📄 CSV' : '🧾 영수증'}</td>
                <td>
                  {h.kind === 'receipt' && h.image && (
                    <img src={`${API_BASE}/uploads/${h.image}`} alt="영수증" width={36} height={36}
                      className="thumb"
                      onClick={() => setLightbox(`${API_BASE}/uploads/${h.image}`)} />
                  )}
                  {h.filename}
                  {h.note && <div className="muted">{h.note}</div>}
                </td>
                <td>
                  {h.kind === 'csv' && h.image && (
                    <button onClick={() => api.csvPreview(h.id).then(setPreview).catch(() => {})}>미리보기</button>
                  )}
                  {h.kind === 'receipt' && (
                    <button onClick={() => {
                      if (!confirm('저장된 원본 이미지로 다시 판독할까요?')) return;
                      api.retryReceipt(h.id).then((r) => { alert(r.ok ? '판독 성공!' : (r.message ?? '판독 실패')); loadHistory(); });
                    }}>재시도</button>
                  )}
                </td>
                <td className="num">{h.saved}건 저장{h.skipped_duplicates > 0 && ` · 중복 ${h.skipped_duplicates}건`}</td>
                <td className="muted">{new Date(h.created_at).toLocaleString('ko-KR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {lightbox && (
        <div className="modal-overlay" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="영수증 확대" className="modal-img" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
      {preview && (
        <div className="modal-overlay" onClick={() => setPreview(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3>{preview.filename} <span className="muted">(상위 {preview.rows.length}/{preview.total}행)</span></h3>
            <div className="modal-scroll">
              <table className="tbl">
                <thead><tr>{preview.columns.map((c: string) => <th key={c}>{c}</th>)}</tr></thead>
                <tbody>
                  {preview.rows.map((r: any, i: number) => (
                    <tr key={i}>{preview.columns.map((c: string) => <td key={c}>{String(r[c])}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => setPreview(null)}>닫기</button>
          </div>
        </div>
      )}
    </div>
  );
}
