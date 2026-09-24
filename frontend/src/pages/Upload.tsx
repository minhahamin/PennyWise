import { useState } from 'react';
import { api } from '../api/client';

const STAGES = ['분석중', '분류중', '저장중', '완료'];

export default function Upload() {
  const [stage, setStage] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [drag, setDrag] = useState(false);

  const runStages = async (fn: () => Promise<any>) => {
    setResult(null);
    for (const s of STAGES) {
      setStage(s);
      await new Promise((r) => setTimeout(r, 250));
    }
    try {
      setResult(await fn());
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
        <p className="muted">은행/카드사 포맷이 달라도 컬럼을 자동 매핑합니다.</p>
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
    </div>
  );
}
