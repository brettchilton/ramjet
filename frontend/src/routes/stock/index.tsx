import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useUnifiedAuth } from '@/hooks/useUnifiedAuth';
import { useStockSummary, useStockItems } from '@/hooks/useStock';
import { StockLevelCards } from '@/components/stock/StockLevelCard';
import { StockTable } from '@/components/stock/StockTable';
import { ThresholdEditor } from '@/components/stock/ThresholdEditor';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Search, ChevronDown, ChevronUp, ArrowLeft } from 'lucide-react';
import type { StockSummaryItem } from '@/types/stock';

export const Route = createFileRoute('/stock/')({
  component: StockDashboard,
});

function StockDashboard() {
  const { user } = useUnifiedAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'admin';

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showThresholds, setShowThresholds] = useState(false);
  const [drillDown, setDrillDown] = useState<{ product_code: string; colour: string } | null>(null);

  // Summary query with debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const handleSearch = (value: string) => {
    setSearch(value);
    // Simple debounce via setTimeout
    const timer = setTimeout(() => setDebouncedSearch(value), 300);
    return () => clearTimeout(timer);
  };

  const { data: summaryData, isLoading } = useStockSummary({
    search: debouncedSearch || undefined,
    status_filter: statusFilter || undefined,
  });

  // Drill-down query for individual cartons
  const { data: cartonData } = useStockItems(
    drillDown
      ? {
          product_code: drillDown.product_code,
          colour: drillDown.colour,
          status: 'in_stock',
          limit: 200,
        }
      : undefined,
  );

  const handleRowClick = (item: StockSummaryItem) => {
    setDrillDown({ product_code: item.product_code, colour: item.colour });
  };

  const handleCartonClick = (stockItemId: string) => {
    navigate({ to: '/stock/$stockItemId', params: { stockItemId } });
  };

  // If drill-down is active, show carton list
  if (drillDown) {
    const drillDownItem = summaryData?.items.find(
      (i) => i.product_code === drillDown.product_code && i.colour === drillDown.colour,
    );

    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setDrillDown(null)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to dashboard
          </Button>
          <h1 className="text-2xl font-bold">
            {drillDown.product_code} — {drillDown.colour}
          </h1>
          {drillDownItem && (
            <span className="text-muted-foreground">
              ({drillDownItem.carton_count} cartons, {drillDownItem.total_units.toLocaleString()} units)
            </span>
          )}
        </div>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Barcode ID</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Scanned In</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cartonData?.items.map((item) => (
                  <TableRow
                    key={item.id}
                    className="cursor-pointer"
                    onClick={() => handleCartonClick(item.id)}
                  >
                    <TableCell className="font-mono text-sm">{item.barcode_id}</TableCell>
                    <TableCell className="text-right">{item.quantity}</TableCell>
                    <TableCell>
                      <Badge variant={item.box_type === 'full' ? 'default' : 'secondary'}>
                        {item.box_type === 'full' ? 'Full' : 'Partial'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {item.scanned_in_at
                        ? new Date(item.scanned_in_at).toLocaleDateString('en-AU', {
                            day: 'numeric',
                            month: 'short',
                          })
                        : '—'}
                    </TableCell>
                  </TableRow>
                ))}
                {cartonData?.items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                      No cartons found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          {isAdmin ? 'Stock Dashboard' : 'Stock Lookup'}
        </h1>
      </div>

      {/* Search + Filter */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search products..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        {isAdmin && (
          <div className="flex items-center gap-2">
            {['', 'red', 'amber', 'green'].map((filter) => (
              <Button
                key={filter}
                size="sm"
                variant={statusFilter === filter ? 'default' : 'outline'}
                onClick={() => setStatusFilter(filter)}
              >
                {filter === '' ? 'All' : filter.charAt(0).toUpperCase() + filter.slice(1)}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Summary Cards (admin only) */}
      {isAdmin && summaryData && <StockLevelCards totals={summaryData.summary} />}

      {/* Stock Table */}
      <Card>
        <CardHeader>
          <CardTitle>Stock Levels</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading stock levels...</div>
          ) : (
            <StockTable
              items={summaryData?.items ?? []}
              onRowClick={handleRowClick}
            />
          )}
        </CardContent>
      </Card>

      {/* Threshold Configuration (admin only, collapsible) */}
      {isAdmin && (
        <Card>
          <CardHeader
            className="cursor-pointer"
            onClick={() => setShowThresholds(!showThresholds)}
          >
            <div className="flex items-center justify-between">
              <CardTitle>Threshold Configuration</CardTitle>
              {showThresholds ? (
                <ChevronUp className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </CardHeader>
          {showThresholds && (
            <CardContent>
              <ThresholdEditor />
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
