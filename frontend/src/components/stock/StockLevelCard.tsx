import { Card, CardContent } from '@/components/ui/card';
import { Package, Boxes, AlertTriangle } from 'lucide-react';
import type { StockSummaryTotals } from '@/types/stock';

interface StockLevelCardProps {
  totals: StockSummaryTotals;
}

const cards = [
  {
    key: 'total_skus' as const,
    label: 'Total SKUs',
    icon: Package,
    format: (v: number) => v.toLocaleString(),
  },
  {
    key: 'total_units' as const,
    label: 'Total Units',
    icon: Boxes,
    format: (v: number) => v.toLocaleString(),
  },
  {
    key: 'low_stock_count' as const,
    label: 'Low Stock',
    icon: AlertTriangle,
    format: (v: number) => v.toLocaleString(),
  },
] as const;

export function StockLevelCards({ totals }: StockLevelCardProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {cards.map(({ key, label, icon: Icon, format }) => (
        <Card key={key}>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="rounded-lg bg-muted p-3">
              <Icon className={`h-6 w-6 ${key === 'low_stock_count' && totals[key] > 0 ? 'text-amber-500' : 'text-muted-foreground'}`} />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">{label}</p>
              <p className="text-2xl font-bold">{format(totals[key])}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
