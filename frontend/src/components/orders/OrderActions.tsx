import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { RejectDialog } from '@/components/orders/RejectDialog';
import { useApproveOrder } from '@/hooks/useOrders';
import { getOfficeOrderUrl } from '@/services/orderService';
import {
  CheckCircle,
  XCircle,
  Pencil,
  Download,
  Save,
} from 'lucide-react';
import type { OrderDetail } from '@/types/orders';

interface OrderActionsProps {
  order: OrderDetail;
  isEditing: boolean;
  onToggleEdit: (e?: React.MouseEvent) => void;
}

export function OrderActions({ order, isEditing, onToggleEdit }: OrderActionsProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const approveMutation = useApproveOrder();

  if (order.status === 'approved') {
    return (
      <div className="flex items-center justify-between rounded-lg border bg-green-50/50 dark:bg-green-950/20 p-4">
        <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
          <CheckCircle className="h-5 w-5" />
          <span className="font-medium">Order Approved</span>
          {order.approved_at && (
            <span className="text-sm text-muted-foreground">
              — {new Date(order.approved_at).toLocaleString('en-AU')}
            </span>
          )}
        </div>
        {order.has_office_order && (
          <Button variant="outline" size="sm" asChild>
            <a
              href={getOfficeOrderUrl(order.id)}
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Download Office Order
            </a>
          </Button>
        )}
      </div>
    );
  }

  if (order.status === 'rejected') {
    return (
      <div className="rounded-lg border bg-red-50/50 dark:bg-red-950/20 p-4">
        <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
          <XCircle className="h-5 w-5" />
          <span className="font-medium">Order Rejected</span>
        </div>
        {order.rejected_reason && (
          <p className="mt-2 text-sm text-muted-foreground">
            Reason: {order.rejected_reason}
          </p>
        )}
      </div>
    );
  }

  // Pending or error — show action buttons
  return (
    <>
      <div className="sticky bottom-0 z-10 flex items-center justify-end gap-3 rounded-lg border bg-white/95 dark:bg-gray-950/95 backdrop-blur p-4">
        <Button
          variant="destructive"
          type="button"
          onClick={() => setRejectOpen(true)}
        >
          <XCircle className="mr-1.5 h-4 w-4" />
          Reject
        </Button>

        {isEditing ? (
          <Button
            key="save-btn"
            type="submit"
            form="order-data-form"
            variant="outline"
          >
            <Save className="mr-1.5 h-4 w-4" />
            Save Changes
          </Button>
        ) : (
          <Button
            key="edit-btn"
            variant="outline"
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onToggleEdit(e);
            }}
          >
            <Pencil className="mr-1.5 h-4 w-4" />
            Edit
          </Button>
        )}

        <Button
          onClick={() => approveMutation.mutate(order.id)}
          disabled={approveMutation.isPending}
          className="bg-green-600 hover:bg-green-700 text-white"
        >
          <CheckCircle className="mr-1.5 h-4 w-4" />
          {approveMutation.isPending ? 'Approving...' : 'Approve'}
        </Button>
      </div>

      <RejectDialog
        orderId={order.id}
        open={rejectOpen}
        onOpenChange={setRejectOpen}
      />
    </>
  );
}
