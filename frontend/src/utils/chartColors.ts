import { useContext } from 'react';
import { ColorModeContext } from '@/ColorModeContext';

export const CHART_COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#84cc16', // lime
] as const;

export const STATUS_COLORS: Record<string, string> = {
  pending: '#3b82f6',   // blue
  approved: '#22c55e',  // green
  rejected: '#ef4444',  // red
  error: '#f97316',     // orange
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  '90-100%': '#22c55e',
  '80-90%': '#84cc16',
  '70-80%': '#f59e0b',
  '60-70%': '#f97316',
  '< 60%': '#ef4444',
};

export function useChartTheme() {
  const { mode } = useContext(ColorModeContext);
  const isDark = mode === 'dark';

  return {
    axisColor: isDark ? '#6b7280' : '#9ca3af',
    gridColor: isDark ? '#374151' : '#e5e7eb',
    textColor: isDark ? '#d1d5db' : '#4b5563',
    tooltipBg: isDark ? '#1f2937' : '#ffffff',
    tooltipBorder: isDark ? '#374151' : '#e5e7eb',
    isDark,
  };
}
