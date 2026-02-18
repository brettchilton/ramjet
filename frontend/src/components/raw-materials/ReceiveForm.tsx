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
import { Button } from '@/components/ui/button';
import type { RawMaterial, ReceiveDeliveryData } from '@/types/rawMaterials';

interface ReceiveFormProps {
  material: RawMaterial | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ReceiveDeliveryData) => void;
  isPending: boolean;
}

export function ReceiveForm({ material, open, onOpenChange, onSubmit, isPending }: ReceiveFormProps) {
  const [quantity, setQuantity] = useState('');
  const [supplier, setSupplier] = useState('');
  const [deliveryNote, setDeliveryNote] = useState('');
  const [unitCost, setUnitCost] = useState('');

  const handleOpen = (isOpen: boolean) => {
    if (isOpen && material) {
      setQuantity('');
      setSupplier(material.default_supplier || '');
      setDeliveryNote('');
      setUnitCost(material.unit_cost || '');
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: ReceiveDeliveryData = {
      quantity: Number(quantity),
    };
    if (supplier) data.supplier = supplier;
    if (deliveryNote) data.delivery_note = deliveryNote;
    if (unitCost) data.unit_cost = Number(unitCost);
    onSubmit(data);
  };

  if (!material) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Receive Delivery</DialogTitle>
          <DialogDescription>
            {material.material_name} ({material.material_code})
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="receive-qty">Quantity ({material.unit_of_measure})</Label>
            <Input
              id="receive-qty"
              type="number"
              step="0.01"
              min="0.01"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="receive-supplier">Supplier</Label>
            <Input
              id="receive-supplier"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="receive-dn">Delivery Note Reference</Label>
            <Input
              id="receive-dn"
              value={deliveryNote}
              onChange={(e) => setDeliveryNote(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="receive-cost">Unit Cost ($/{material.unit_of_measure})</Label>
            <Input
              id="receive-cost"
              type="number"
              step="0.01"
              min="0"
              value={unitCost}
              onChange={(e) => setUnitCost(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !quantity || Number(quantity) <= 0}>
              {isPending ? 'Receiving...' : 'Receive'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
