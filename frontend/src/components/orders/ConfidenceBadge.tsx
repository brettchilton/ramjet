import { cn } from '@/lib/utils';

interface ConfidenceBadgeProps {
  confidence: number | string | undefined;
  className?: string;
}

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  if (confidence === undefined || confidence === null) return null;

  const value = typeof confidence === 'string' ? parseFloat(confidence) : confidence;
  const percent = Math.round(value * 100);

  let colorClasses: string;
  if (value >= 0.9) {
    colorClasses = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
  } else if (value >= 0.7) {
    colorClasses = 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
  } else {
    colorClasses = 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        colorClasses,
        className
      )}
    >
      {percent}%
    </span>
  );
}
