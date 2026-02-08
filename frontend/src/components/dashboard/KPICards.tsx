import {
  DollarSign,
  ShoppingCart,
  TrendingUp,
  CheckCircle2,
  Package,
  Clock,
  Brain,
  AlertTriangle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { KPIMetrics } from '@/types/analytics';
import { formatCurrency, formatNumber, formatPercent, formatHours } from '@/utils/formatters';

interface KPICardsProps {
  kpi: KPIMetrics;
}

export function KPICards({ kpi }: KPICardsProps) {
  const cards = [
    {
      title: 'Revenue',
      value: formatCurrency(kpi.total_revenue),
      subtitle: 'Approved orders',
      icon: DollarSign,
      color: 'text-emerald-500',
    },
    {
      title: 'Total Orders',
      value: formatNumber(kpi.total_orders),
      subtitle: `${kpi.approved_orders} approved`,
      icon: ShoppingCart,
      color: 'text-blue-500',
    },
    {
      title: 'Avg Order Value',
      value: formatCurrency(kpi.avg_order_value),
      subtitle: 'Per approved order',
      icon: TrendingUp,
      color: 'text-violet-500',
    },
    {
      title: 'Approval Rate',
      value: kpi.total_orders > 0
        ? formatPercent((kpi.approved_orders / kpi.total_orders) * 100)
        : '--',
      subtitle: `${kpi.approved_orders} of ${kpi.total_orders}`,
      icon: CheckCircle2,
      color: 'text-green-500',
    },
    {
      title: 'Total Units',
      value: formatNumber(kpi.total_units),
      subtitle: 'Across all orders',
      icon: Package,
      color: 'text-cyan-500',
    },
    {
      title: 'Avg Processing',
      value: formatHours(kpi.avg_processing_hours),
      subtitle: 'To approval',
      icon: Clock,
      color: 'text-orange-500',
    },
    {
      title: 'AI Confidence',
      value: kpi.avg_confidence !== null
        ? formatPercent(kpi.avg_confidence * 100)
        : '--',
      subtitle: 'Avg extraction',
      icon: Brain,
      color: 'text-indigo-500',
    },
    {
      title: 'Review Rate',
      value: formatPercent(kpi.review_rate),
      subtitle: 'Items needing review',
      icon: AlertTriangle,
      color: 'text-amber-500',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
