import { apiClient } from '@/utils/apiClient';
import type { DashboardData, Period } from '@/types/analytics';

export async function fetchDashboardData(
  period: Period,
  startDate?: string,
  endDate?: string,
): Promise<DashboardData> {
  const params = new URLSearchParams({ period });
  if (period === 'custom' && startDate) params.set('start_date', startDate);
  if (period === 'custom' && endDate) params.set('end_date', endDate);

  const res = await apiClient.get(`/api/analytics/dashboard?${params}`);
  if (!res.ok) throw new Error('Failed to fetch dashboard data');
  return res.json();
}
