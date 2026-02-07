import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useRejectOrder } from '@/hooks/useOrders';

interface RejectDialogProps {
  orderId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RejectDialog({ orderId, open, onOpenChange }: RejectDialogProps) {
  const [reason, setReason] = useState('');
  const rejectMutation = useRejectOrder();

  const handleSubmit = () => {
    if (!reason.trim()) return;
    rejectMutation.mutate(
      { id: orderId, reason: reason.trim() },
      {
        onSuccess: () => {
          setReason('');
          onOpenChange(false);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reject Order</DialogTitle>
          <DialogDescription>
            Provide a reason for rejecting this order. This will be recorded and
            visible in the order history.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <Label htmlFor="reject-reason">Reason</Label>
          <Textarea
            id="reject-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter rejection reason..."
            className="mt-2"
            rows={4}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleSubmit}
            disabled={!reason.trim() || rejectMutation.isPending}
          >
            {rejectMutation.isPending ? 'Rejecting...' : 'Reject Order'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
