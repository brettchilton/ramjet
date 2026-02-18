import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useStockItemDetail } from '@/hooks/useStock';
import { MovementHistory } from '@/components/stock/MovementHistory';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export const Route = createFileRoute('/stock/$stockItemId')({
  component: StockItemDetailPage,
});

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    pending_scan: { label: 'Pending Scan', className: 'bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30' },
    in_stock: { label: 'In Stock', className: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30' },
    picked: { label: 'Picked', className: 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30' },
    scrapped: { label: 'Scrapped', className: 'bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30' },
    consumed: { label: 'Consumed', className: 'bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30' },
  };

  const c = config[status] ?? { label: status, className: '' };
  return <Badge variant="outline" className={c.className}>{c.label}</Badge>;
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value ?? '—'}</span>
    </div>
  );
}

function StockItemDetailPage() {
  const { stockItemId } = Route.useParams();
  const navigate = useNavigate();
  const { data: item, isLoading, error } = useStockItemDetail(stockItemId);

  if (isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12 text-muted-foreground">Loading stock item...</div>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12 text-muted-foreground">
          Stock item not found.
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate({ to: '/stock' })}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-xl font-bold font-mono">{item.barcode_id}</h1>
          <p className="text-sm text-muted-foreground">
            {item.product_code} — {item.product_description}
          </p>
        </div>
        <StatusBadge status={item.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Item Details */}
        <Card>
          <CardHeader>
            <CardTitle>Carton Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-0">
            <DetailRow label="Product" value={`${item.product_code} — ${item.product_description}`} />
            <DetailRow label="Colour" value={item.colour} />
            <DetailRow label="Quantity" value={`${item.quantity} units`} />
            <DetailRow
              label="Box Type"
              value={
                <Badge variant={item.box_type === 'full' ? 'default' : 'secondary'}>
                  {item.box_type === 'full' ? 'Full' : 'Partial'}
                </Badge>
              }
            />
            <DetailRow label="Status" value={<StatusBadge status={item.status} />} />
            <DetailRow
              label="Production Date"
              value={item.production_date ? new Date(item.production_date).toLocaleDateString('en-AU') : null}
            />
            <DetailRow
              label="Scanned In"
              value={item.scanned_in_at ? new Date(item.scanned_in_at).toLocaleString('en-AU') : null}
            />
            {item.scanned_out_at && (
              <DetailRow
                label="Scanned Out"
                value={new Date(item.scanned_out_at).toLocaleString('en-AU')}
              />
            )}
            {item.notes && <DetailRow label="Notes" value={item.notes} />}
          </CardContent>
        </Card>

        {/* Movement History */}
        <Card>
          <CardHeader>
            <CardTitle>Movement History</CardTitle>
          </CardHeader>
          <CardContent>
            <MovementHistory movements={item.movements} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
