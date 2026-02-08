import { useQuery } from '@tanstack/react-query';
import { fetchDashboardData } from '@/services/analyticsService';
import type { Period } from '@/types/analytics';

export function useDashboardData(
  period: Period,
  startDate?: string,
  endDate?: string,
) {
  return useQuery({
    queryKey: ['dashboard', period, startDate, endDate],
    queryFn: () => fetchDashboardData(period, startDate, endDate),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
