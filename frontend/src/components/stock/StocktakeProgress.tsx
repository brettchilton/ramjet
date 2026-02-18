import { Progress } from '@/components/ui/progress';
import type { SessionProgress } from '@/types/stock';

interface StocktakeProgressProps {
  progress: SessionProgress;
}

export function StocktakeProgress({ progress }: StocktakeProgressProps) {
  const { total_expected, total_scanned, percentage } = progress;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Progress</span>
        <span className="font-semibold">
          {total_scanned} / {total_expected}{' '}
          <span className="text-muted-foreground">({percentage}%)</span>
        </span>
      </div>
      <Progress value={percentage} className="h-4" />
    </div>
  );
}
