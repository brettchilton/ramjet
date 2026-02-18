import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useRawMaterial, useReceiveDelivery, useRecordUsage, useAdjustStock } from '@/hooks/useRawMaterials';
import { ReceiveForm } from '@/components/raw-materials/ReceiveForm';
import { UsageForm } from '@/components/raw-materials/UsageForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  ArrowDownToLine,
  ArrowUpFromLine,
  Wrench,
  TrendingUp,
  TrendingDown,
  RotateCcw,
} from 'lucide-react';
import type { RawMaterial, ReceiveDeliveryData, RecordUsageData, AdjustStockData } from '@/types/rawMaterials';

export const Route = createFileRoute('/raw-materials/$materialId')({
  component: RawMaterialDetailPage,
});

function RawMaterialDetailPage() {
  return (
    <AuthGuard>
      <RawMaterialDetailContent />
    </AuthGuard>
  );
}

const statusColors: Record<string, string> = {
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
};

const statusLabels: Record<string, string> = {
  green: 'Healthy',
  amber: 'Low Stock',
  red: 'Critical',
};

const movementIcons: Record<string, typeof TrendingUp> = {
  received: TrendingUp,
  used: TrendingDown,
  adjustment: RotateCcw,
  stocktake: RotateCcw,
};

function RawMaterialDetailContent() {
  const { materialId } = Route.useParams();
  const navigate = useNavigate();
  const { data: material, isLoading } = useRawMaterial(materialId);

  const [receiveOpen, setReceiveOpen] = useState(false);
  const [useOpen, setUseOpen] = useState(false);
  const [adjustOpen, setAdjustOpen] = useState(false);

  const receiveMutation = useReceiveDelivery();
  const usageMutation = useRecordUsage();
  const adjustMutation = useAdjustStock();

  // Build a RawMaterial-compatible object for the forms
  const materialForForm: RawMaterial | null = material
    ? {
        id: material.id,
        material_code: material.material_code,
        material_name: material.material_name,
        material_type: material.material_type,
        unit_of_measure: material.unit_of_measure,
        current_stock: material.current_stock,
        red_threshold: material.red_threshold,
        amber_threshold: material.amber_threshold,
        default_supplier: material.default_supplier,
        unit_cost: material.unit_cost,
        is_active: material.is_active,
        notes: material.notes,
        threshold_status: material.threshold_status,
      }
    : null;

  const handleReceive = (data: ReceiveDeliveryData) => {
    receiveMutation.mutate(
      { id: materialId, data },
      { onSuccess: () => setReceiveOpen(false) },
    );
  };

  const handleUse = (data: RecordUsageData) => {
    usageMutation.mutate(
      { id: materialId, data },
      { onSuccess: () => setUseOpen(false) },
    );
  };

  const handleAdjust = (data: AdjustStockData) => {
    adjustMutation.mutate(
      { id: materialId, data },
      { onSuccess: () => setAdjustOpen(false) },
    );
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-AU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6 pt-[20px]">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!material) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">Raw material not found</p>
        <Button variant="link" onClick={() => navigate({ to: '/raw-materials' })}>
          Back to Raw Materials
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pt-[20px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate({ to: '/raw-materials' })}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{material.material_code}</h1>
            <p className="text-muted-foreground">{material.material_name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setReceiveOpen(true)}>
            <ArrowDownToLine className="h-4 w-4 mr-2" />
            Receive
          </Button>
          <Button variant="outline" onClick={() => setUseOpen(true)}>
            <ArrowUpFromLine className="h-4 w-4 mr-2" />
            Use
          </Button>
          <Button variant="outline" onClick={() => setAdjustOpen(true)}>
            <Wrench className="h-4 w-4 mr-2" />
            Adjust
          </Button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Current Stock</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full ${statusColors[material.threshold_status]}`}
              />
              <span className="text-2xl font-bold">
                {Number(material.current_stock).toLocaleString()}
              </span>
              <span className="text-muted-foreground">{material.unit_of_measure}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {statusLabels[material.threshold_status]}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Thresholds</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-red-500" />
                <span>Red &lt; {Number(material.red_threshold).toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <span>Amber &lt; {Number(material.amber_threshold).toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-muted-foreground">Type: </span>
                <Badge variant="outline">{material.material_type}</Badge>
              </div>
              <div>
                <span className="text-muted-foreground">Unit: </span>
                {material.unit_of_measure}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Supplier</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div>{material.default_supplier || '—'}</div>
              {material.unit_cost && (
                <div className="text-muted-foreground">
                  ${Number(material.unit_cost).toFixed(2)}/{material.unit_of_measure}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notes */}
      {material.notes && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{material.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* Movement History */}
      <Card>
        <CardHeader>
          <CardTitle>Movement History</CardTitle>
        </CardHeader>
        <CardContent>
          {material.movements.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No movements recorded yet.
            </p>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead>By</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {material.movements.map((mv) => {
                    const Icon = movementIcons[mv.movement_type] || RotateCcw;
                    const qty = Number(mv.quantity);
                    const isPositive = qty > 0;

                    return (
                      <TableRow key={mv.id}>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDate(mv.created_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Icon className={`h-4 w-4 ${isPositive ? 'text-green-500' : 'text-red-500'}`} />
                            <span className="capitalize">{mv.movement_type}</span>
                          </div>
                        </TableCell>
                        <TableCell className={`text-right font-mono ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                          {isPositive ? '+' : ''}{qty.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-sm">
                          {mv.performed_by_name || '—'}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {[
                            mv.supplier && `Supplier: ${mv.supplier}`,
                            mv.delivery_note && `DN: ${mv.delivery_note}`,
                            mv.unit_cost && `$${Number(mv.unit_cost).toFixed(2)}/unit`,
                            mv.reason,
                          ]
                            .filter(Boolean)
                            .join(' | ') || '—'}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Receive Dialog */}
      <ReceiveForm
        material={materialForForm}
        open={receiveOpen}
        onOpenChange={setReceiveOpen}
        onSubmit={handleReceive}
        isPending={receiveMutation.isPending}
      />

      {/* Usage Dialog */}
      <UsageForm
        material={materialForForm}
        open={useOpen}
        onOpenChange={setUseOpen}
        onSubmit={handleUse}
        isPending={usageMutation.isPending}
      />

      {/* Adjustment Dialog */}
      <AdjustmentDialog
        material={material}
        open={adjustOpen}
        onOpenChange={setAdjustOpen}
        onSubmit={handleAdjust}
        isPending={adjustMutation.isPending}
      />
    </div>
  );
}

// ── Adjustment Dialog ────────────────────────────────────────────────

function AdjustmentDialog({
  material,
  open,
  onOpenChange,
  onSubmit,
  isPending,
}: {
  material: { material_name: string; material_code: string; unit_of_measure: string } | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: AdjustStockData) => void;
  isPending: boolean;
}) {
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState('');

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setQuantity('');
      setReason('');
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ quantity: Number(quantity), reason });
  };

  if (!material) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manual Adjustment</DialogTitle>
          <DialogDescription>
            {material.material_name} ({material.material_code})
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="adj-qty">
              Quantity ({material.unit_of_measure}) — use negative for reductions
            </Label>
            <Input
              id="adj-qty"
              type="number"
              step="0.01"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="e.g. -50 or 100"
              required
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="adj-reason">Reason (required)</Label>
            <Textarea
              id="adj-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Damaged bag - moisture contamination"
              required
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !quantity || !reason}>
              {isPending ? 'Adjusting...' : 'Adjust'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
