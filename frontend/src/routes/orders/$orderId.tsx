import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useOrder, useUpdateOrder, useUpdateLineItem, useDeleteOrder } from '@/hooks/useOrders';
import { OrderSourcePanel } from '@/components/orders/OrderSourcePanel';
import { OrderDataForm } from '@/components/orders/OrderDataForm';
import { FormPreview } from '@/components/orders/FormPreview';
import { OrderActions } from '@/components/orders/OrderActions';
import { StatusBadge } from '@/components/orders/StatusBadge';
import { ConfidenceBadge } from '@/components/orders/ConfidenceBadge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { ArrowLeft, Trash2 } from 'lucide-react';
import type { LineItemUpdateData } from '@/types/orders';

export const Route = createFileRoute('/orders/$orderId')({
  component: OrderReviewPage,
});

function OrderReviewPage() {
  return (
    <AuthGuard>
      <OrderReviewContent />
    </AuthGuard>
  );
}

function OrderReviewContent() {
  const { orderId } = Route.useParams();
  const navigate = useNavigate();
  const { data: order, isLoading } = useOrder(orderId);
  const updateOrderMutation = useUpdateOrder();
  const updateLineItemMutation = useUpdateLineItem();
  const deleteMutation = useDeleteOrder();
  const [isEditing, _setIsEditing] = useState(false);

  // Trace state updates
  const setIsEditing = (newVal: boolean | ((prev: boolean) => boolean)) => {
    console.log('[OrderReviewContent] setIsEditing called with:', newVal);
    console.trace('[OrderReviewContent] Trace for setIsEditing');
    _setIsEditing(newVal);
  };

  const [deleteOpen, setDeleteOpen] = useState(false);



  // DEBUG LOGS (Re-added)




  // FIX: Only show skeleton if we have NO data.  
  // If we have data but are refetching (swr), we should keep showing the UI.
  if (isLoading && !order) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <Skeleton className="h-96 w-full" />
          </div>
          <div className="lg:col-span-3">
            <Skeleton className="h-96 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-muted-foreground">
        <p className="text-lg font-medium">Order not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate({ to: '/orders' })}
        >
          Back to Orders
        </Button>
      </div>
    );
  }

  const handleSave = async (
    headerData: {
      customer_name: string;
      po_number: string;
      po_date: string;
      delivery_date: string;
      special_instructions: string;
    },
    lineItems: Array<{
      id: string;
      line_number: number;
      product_code: string;
      product_description: string;
      colour: string;
      quantity: number;
      unit_price: number;
      line_total: number;
      confidence?: string;
      needs_review: boolean;
    }>
  ) => {
    // Update header
    await updateOrderMutation.mutateAsync({
      id: order.id,
      data: {
        customer_name: headerData.customer_name || undefined,
        po_number: headerData.po_number || undefined,
        po_date: headerData.po_date || undefined,
        delivery_date: headerData.delivery_date || undefined,
        special_instructions: headerData.special_instructions || undefined,
      },
    });

    // Update each modified line item
    for (const item of lineItems) {
      const original = order.line_items.find((li) => li.id === item.id);
      if (!original) continue;

      const updates: LineItemUpdateData = {};
      if (item.product_code !== (original.product_code || ''))
        updates.product_code = item.product_code;
      if (item.product_description !== (original.product_description || ''))
        updates.product_description = item.product_description;
      if (item.colour !== (original.colour || ''))
        updates.colour = item.colour;
      if (item.quantity !== original.quantity)
        updates.quantity = item.quantity;
      if (String(item.unit_price) !== (original.unit_price || '0'))
        updates.unit_price = String(item.unit_price);

      if (Object.keys(updates).length > 0) {
        await updateLineItemMutation.mutateAsync({
          orderId: order.id,
          itemId: item.id,
          data: updates,
        });
      }
    }

    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb bar */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/orders' })}
          >
            <ArrowLeft className="mr-1.5 h-4 w-4" />
            Back to Orders
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold">
              {order.customer_name || 'Unknown Customer'}
            </h1>
            {order.po_number && (
              <span className="text-sm text-muted-foreground">
                — PO# {order.po_number}
              </span>
            )}
          </div>
          <StatusBadge status={order.status} />
          <ConfidenceBadge confidence={order.extraction_confidence} />
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive"
          onClick={() => setDeleteOpen(true)}
        >
          <Trash2 className="h-5 w-5" />
          <span className="sr-only">Delete order</span>
        </Button>
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Order</DialogTitle>
            <DialogDescription>
              This will permanently delete the order, all line items, and any
              generated forms. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() =>
                deleteMutation.mutate(order.id, {
                  onSuccess: () => navigate({ to: '/orders' }),
                })
              }
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Order'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Two-column panel: Source (left) + Extracted data (right) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2 rounded-lg border p-4">
          <h2 className="text-sm font-semibold mb-3">Source Document</h2>
          <OrderSourcePanel emailId={order.email_id} orderId={order.id} />
        </div>

        <div className="lg:col-span-3 rounded-lg border p-4">
          <h2 className="text-sm font-semibold mb-3">Extracted Data</h2>
          <OrderDataForm
            order={order}
            isEditing={isEditing}
            onSave={handleSave}
          />
        </div>
      </div>

      {/* Form Preview */}
      <div className="rounded-lg border p-4">
        <FormPreview order={order} />
      </div>

      {/* Action Bar */}
      <OrderActions
        order={order}
        isEditing={isEditing}
        onToggleEdit={() => setIsEditing(!isEditing)}
      />
    </div>
  );
}
