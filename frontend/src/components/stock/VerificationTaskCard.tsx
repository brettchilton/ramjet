import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { CheckCircle, Package, Loader2 } from 'lucide-react';
import type { StockVerification } from '@/types/stock';

interface VerificationTaskCardProps {
  verification: StockVerification;
  onConfirm: (verificationId: string, verifiedQuantity: number, notes?: string) => void;
  isConfirming: boolean;
}

export function VerificationTaskCard({
  verification,
  onConfirm,
  isConfirming,
}: VerificationTaskCardProps) {
  const [quantity, setQuantity] = useState<number>(verification.system_stock_quantity);
  const [notes, setNotes] = useState('');

  const handleConfirm = () => {
    onConfirm(verification.id, quantity, notes || undefined);
  };

  if (verification.status === 'confirmed') {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg bg-green-50 border border-green-200">
        <CheckCircle className="h-5 w-5 text-green-600 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">
            {verification.product_code} — {verification.colour}
          </p>
          <p className="text-sm text-muted-foreground">
            Verified: {verification.verified_quantity?.toLocaleString()} units
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-lg border bg-card space-y-4">
      {/* Product info */}
      <div className="flex items-start gap-3">
        <Package className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-base">
            {verification.product_code} — {verification.colour}
          </p>
          {verification.product_description && (
            <p className="text-sm text-muted-foreground">{verification.product_description}</p>
          )}
        </div>
      </div>

      {/* Quantities */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-muted-foreground">Ordered:</span>{' '}
          <span className="font-semibold">{verification.ordered_quantity?.toLocaleString()}</span>
        </div>
        <div>
          <span className="text-muted-foreground">System stock:</span>{' '}
          <span className="font-semibold">{verification.system_stock_quantity.toLocaleString()}</span>
        </div>
      </div>

      {/* Verify form */}
      <div className="space-y-3">
        <div>
          <Label htmlFor={`qty-${verification.id}`} className="text-sm font-medium">
            Verified quantity (units)
          </Label>
          <Input
            id={`qty-${verification.id}`}
            type="number"
            min={0}
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
            className="mt-1 h-12 text-lg"
          />
        </div>
        <div>
          <Label htmlFor={`notes-${verification.id}`} className="text-sm font-medium">
            Notes (optional)
          </Label>
          <Textarea
            id={`notes-${verification.id}`}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Counted 10 cartons in bay 3"
            className="mt-1"
            rows={2}
          />
        </div>
        <Button
          onClick={handleConfirm}
          disabled={isConfirming}
          className="w-full h-12 text-base font-semibold"
        >
          {isConfirming ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Confirming...
            </>
          ) : (
            <>
              <CheckCircle className="h-5 w-5 mr-2" />
              Confirm Stock
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
