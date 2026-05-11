/** Согласованные цвета кластеров для диаграмм, легенды и списков. */
export const CLUSTER_COLORS = [
  '#6366f1',
  '#f97316',
  '#10b981',
  '#ec4899',
  '#eab308',
  '#8b5cf6',
  '#ef4444',
  '#06b6d4',
  '#84cc16',
  '#f43f5e',
]

export function colorForClusterLabel(label) {
  const n = Number(label)
  const i = Number.isFinite(n) ? Math.abs(Math.trunc(n)) % CLUSTER_COLORS.length : 0
  return CLUSTER_COLORS[i]
}
