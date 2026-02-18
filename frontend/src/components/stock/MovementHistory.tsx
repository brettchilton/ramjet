import type { StockMovement } from '@/types/stock';
import { ArrowDownCircle, ArrowUpCircle, RefreshCw, ClipboardCheck, Scissors } from 'lucide-react';

interface MovementHistoryProps {
  movements: StockMovement[];
}

const movementConfig: Record<string, { icon: typeof ArrowDownCircle; label: string; colour: string }> = {
  stock_in: { icon: ArrowDownCircle, label: 'Stock In', colour: 'text-emerald-500' },
  stock_out: { icon: ArrowUpCircle, label: 'Stock Out', colour: 'text-red-500' },
  adjustment: { icon: RefreshCw, label: 'Adjustment', colour: 'text-amber-500' },
  stocktake_verified: { icon: ClipboardCheck, label: 'Stocktake Verified', colour: 'text-blue-500' },
  partial_repack: { icon: Scissors, label: 'Partial Repack', colour: 'text-purple-500' },
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function MovementHistory({ movements }: MovementHistoryProps) {
  if (movements.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No movement history.
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {movements.map((movement, index) => {
        const config = movementConfig[movement.movement_type] ?? {
          icon: RefreshCw,
          label: movement.movement_type,
          colour: 'text-muted-foreground',
        };
        const Icon = config.icon;
        const isLast = index === movements.length - 1;

        return (
          <div key={movement.id} className="flex gap-4">
            {/* Timeline line + icon */}
            <div className="flex flex-col items-center">
              <div className={`rounded-full p-1.5 ${config.colour} bg-muted`}>
                <Icon className="h-4 w-4" />
              </div>
              {!isLast && <div className="w-px flex-1 bg-border" />}
            </div>

            {/* Content */}
            <div className={`pb-6 ${isLast ? '' : ''}`}>
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{config.label}</span>
                <span className={`text-sm font-mono ${movement.quantity_change > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                  {movement.quantity_change > 0 ? '+' : ''}{movement.quantity_change}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatDate(movement.created_at)}
              </p>
              {movement.reason && (
                <p className="text-sm text-muted-foreground mt-1">
                  {movement.reason}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
