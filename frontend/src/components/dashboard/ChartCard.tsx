import { useState } from 'react';
import { BarChart3, List } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ChartCardProps {
  title: string;
  description?: string;
  chart: React.ReactNode;
  list: React.ReactNode;
}

export function ChartCard({ title, description, chart, list }: ChartCardProps) {
  const [showList, setShowList] = useState(false);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={() => setShowList(!showList)}
        >
          {showList ? (
            <BarChart3 className="h-4 w-4" />
          ) : (
            <List className="h-4 w-4" />
          )}
        </Button>
      </CardHeader>
      <CardContent className="pt-0">
        {showList ? list : chart}
      </CardContent>
    </Card>
  );
}
