export const CATEGORY_COLORS: Record<string, string> = {
  식비: '#f59e0b',
  카페: '#fb923c',
  교통: '#3b82f6',
  구독: '#8b5cf6',
  쇼핑: '#a855f7',
  의료: '#10b981',
  고정비: '#64748b',
  여가: '#ec4899',
  교육: '#0ea5e9',
  기타: '#9ca3af',
};

export function categoryColor(cat: string): string {
  return CATEGORY_COLORS[cat] ?? '#9ca3af';
}

export const won = (n: number) => `${Math.round(n).toLocaleString('ko-KR')}원`;
