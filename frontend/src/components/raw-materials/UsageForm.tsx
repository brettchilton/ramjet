import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import type { RawMaterial, RecordUsageData } from '@/types/rawMaterials';

interface UsageFormProps {
  material: RawMaterial | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: RecordUsageData) => void;
  isPending: boolean;
}

export function UsageForm({ material, open, onOpenChange, onSubmit, isPending }: UsageFormProps) {
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
    const data: RecordUsageData = { quantity: Number(quantity) };
    if (reason) data.reason = reason;
    onSubmit(data);
  };

  if (!material) return null;

  const maxQty = Number(material.current_stock);

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Record Usage</DialogTitle>
          <DialogDescription>
            {material.material_name} ({material.material_code}) — Available: {Number(material.current_stock).toLocaleString()} {material.unit_of_measure}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="use-qty">Quantity ({material.unit_of_measure})</Label>
            <Input
              id="use-qty"
              type="number"
              step="0.01"
              min="0.01"
              max={maxQty}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
              autoFocus
            />
            {Number(quantity) > maxQty && (
              <p className="text-sm text-destructive">
                Exceeds available stock ({maxQty} {material.unit_of_measure})
              </p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="use-reason">Reason (optional)</Label>
            <Textarea
              id="use-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Production run LOCAP2 Black"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending || !quantity || Number(quantity) <= 0 || Number(quantity) > maxQty}
            >
              {isPending ? 'Recording...' : 'Record Usage'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
