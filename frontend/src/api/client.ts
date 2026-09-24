const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function req(path: string, init?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  health: () => req('/health'),
  transactions: (params: Record<string, string> = {}) => {
    const q = new URLSearchParams(params).toString();
    return req(`/transactions${q ? `?${q}` : ''}`);
  },
  correct: (id: number, category: string, subcategory = '') =>
    req(`/transactions/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, subcategory }),
    }),
  uploadCsv: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${BASE}/upload/csv`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  uploadReceipt: async (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${BASE}/upload/receipt`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  report: (y: number, m: number) => req(`/report/monthly/${y}/${m}`),
  alerts: (y: number, m: number) => req(`/alerts?year=${y}&month=${m}`),
  setBudget: (category: string, year: number, month: number, budgeted_amount: number) =>
    req('/budget', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, year, month, budgeted_amount }),
    }),
};

export const API_BASE = BASE;
