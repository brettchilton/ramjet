import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '../components/AuthGuard';
import { useDashboardData } from '@/hooks/useAnalytics';
import { PeriodSelector } from '@/components/dashboard/PeriodSelector';
import { DashboardSkeleton } from '@/components/dashboard/DashboardSkeleton';
import { KPICards } from '@/components/dashboard/KPICards';
import { RevenueTrendChart } from '@/components/dashboard/RevenueTrendChart';
import { OrderStatusChart } from '@/components/dashboard/OrderStatusChart';
import { TopCustomersChart } from '@/components/dashboard/TopCustomersChart';
import { TopProductsChart } from '@/components/dashboard/TopProductsChart';
import { ConfidenceChart } from '@/components/dashboard/ConfidenceChart';
import { RecentOrdersList } from '@/components/dashboard/RecentOrdersList';
import type { Period } from '@/types/analytics';

export const Route = createFileRoute('/dashboard')({ component: DashboardPage });

function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}

function DashboardContent() {
  const [period, setPeriod] = useState<Period>('mtd');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data, isLoading, isError } = useDashboardData(period, startDate, endDate);

  return (
    <div className="space-y-6 pt-[20px]">
      {/* Header row */}
      <div className="flex items-center justify-end flex-wrap gap-4">
        <PeriodSelector
          value={period}
          onChange={setPeriod}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
        />
      </div>

      {isLoading ? (
        <DashboardSkeleton />
      ) : isError || !data ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <p className="text-lg font-medium">Failed to load dashboard data</p>
          <p className="text-sm">Check that the backend is running and try again</p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <KPICards kpi={data.kpi} />

          {/* Revenue Trend + Order Status */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="md:col-span-2">
              <RevenueTrendChart data={data.revenue_trend} />
            </div>
            <OrderStatusChart data={data.status_breakdown} />
          </div>

          {/* Top Customers + Top Products */}
          <div className="grid gap-4 md:grid-cols-2">
            <TopCustomersChart data={data.top_customers} />
            <TopProductsChart data={data.top_products} />
          </div>

          {/* Confidence + Recent Orders */}
          <div className="grid gap-4 md:grid-cols-2">
            <ConfidenceChart data={data.confidence_distribution} />
            <RecentOrdersList data={data.recent_orders} />
          </div>
        </>
      )}
    </div>
  );
}
