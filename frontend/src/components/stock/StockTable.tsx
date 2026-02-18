import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { StockSummaryItem } from '@/types/stock';

interface StockTableProps {
  items: StockSummaryItem[];
  onRowClick?: (item: StockSummaryItem) => void;
}

function ThresholdBadge({ status }: { status: string | null }) {
  if (!status) {
    return <Badge variant="outline" className="text-muted-foreground">No threshold</Badge>;
  }

  const config = {
    green: { label: 'Healthy', className: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30' },
    amber: { label: 'Low', className: 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30' },
    red: { label: 'Critical', className: 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30' },
  }[status];

  if (!config) return null;

  return (
    <Badge variant="outline" className={config.className}>
      <span className={`mr-1.5 inline-block h-2 w-2 rounded-full ${
        status === 'green' ? 'bg-emerald-500' : status === 'amber' ? 'bg-amber-500' : 'bg-red-500'
      }`} />
      {config.label}
    </Badge>
  );
}

export function StockTable({ items, onRowClick }: StockTableProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No stock items found.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Colour</TableHead>
          <TableHead className="text-right">Cartons</TableHead>
          <TableHead className="text-right">Units</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow
            key={`${item.product_code}-${item.colour}`}
            className={onRowClick ? 'cursor-pointer' : ''}
            onClick={() => onRowClick?.(item)}
          >
            <TableCell>
              <div>
                <span className="font-medium">{item.product_code}</span>
                {item.product_description && (
                  <p className="text-sm text-muted-foreground truncate max-w-[200px]">
                    {item.product_description}
                  </p>
                )}
              </div>
            </TableCell>
            <TableCell>{item.colour}</TableCell>
            <TableCell className="text-right">{item.carton_count}</TableCell>
            <TableCell className="text-right font-medium">
              {item.total_units.toLocaleString()}
            </TableCell>
            <TableCell>
              <ThresholdBadge status={item.threshold_status} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
