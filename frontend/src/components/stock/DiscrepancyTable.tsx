import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Search } from 'lucide-react';
import type { DiscrepancyReport } from '@/types/stock';

interface DiscrepancyTableProps {
  report: DiscrepancyReport;
}

export function DiscrepancyTable({ report }: DiscrepancyTableProps) {
  const { missing_items, unexpected_scans, summary } = report;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold">{summary.total_expected}</p>
          <p className="text-xs text-muted-foreground">Expected</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-green-600">{summary.total_found}</p>
          <p className="text-xs text-muted-foreground">Found</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-red-600">{summary.total_missing}</p>
          <p className="text-xs text-muted-foreground">Missing</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-amber-600">{summary.total_unexpected}</p>
          <p className="text-xs text-muted-foreground">Unexpected</p>
        </div>
      </div>

      {/* Missing Items */}
      {missing_items.length > 0 && (
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-red-700 dark:text-red-400">
              <AlertTriangle className="h-5 w-5" />
              Missing Items ({missing_items.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Barcode</th>
                    <th className="pb-2 pr-4">Product</th>
                    <th className="pb-2 pr-4">Colour</th>
                    <th className="pb-2 pr-4 text-right">Qty</th>
                    <th className="pb-2">Last Movement</th>
                  </tr>
                </thead>
                <tbody>
                  {missing_items.map((item) => (
                    <tr key={item.stock_item_id} className="border-b last:border-b-0">
                      <td className="py-2 pr-4 font-mono text-xs">{item.barcode_id}</td>
                      <td className="py-2 pr-4">{item.product_code}</td>
                      <td className="py-2 pr-4">{item.colour}</td>
                      <td className="py-2 pr-4 text-right">{item.quantity}</td>
                      <td className="py-2 text-muted-foreground text-xs">
                        {item.last_movement || '—'}
                        {item.last_movement_date && (
                          <span className="ml-1">
                            ({new Date(item.last_movement_date).toLocaleDateString()})
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Unexpected Scans */}
      {unexpected_scans.length > 0 && (
        <Card className="border-amber-200 dark:border-amber-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-amber-700 dark:text-amber-400">
              <Search className="h-5 w-5" />
              Unexpected Scans ({unexpected_scans.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="space-y-1">
              {unexpected_scans.map((scan, idx) => (
                <div
                  key={`${scan.barcode_scanned}-${idx}`}
                  className="flex items-center justify-between py-2 px-2 border-b last:border-b-0 text-sm"
                >
                  <span className="font-mono text-xs">{scan.barcode_scanned}</span>
                  <span className="text-amber-600 text-xs font-medium">
                    {scan.scan_result === 'not_in_system' ? 'Not in system' : 'Wrong status'}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All clear */}
      {missing_items.length === 0 && unexpected_scans.length === 0 && (
        <Card className="border-green-200 dark:border-green-900">
          <CardContent className="py-6 text-center">
            <p className="text-lg font-semibold text-green-600">No Discrepancies Found</p>
            <p className="text-sm text-muted-foreground mt-1">
              All expected items were accounted for.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
