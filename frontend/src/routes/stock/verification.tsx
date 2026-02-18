import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { VerificationTaskCard } from '@/components/stock/VerificationTaskCard';
import { usePendingVerifications, useConfirmVerification } from '@/hooks/useStockVerification';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ClipboardCheck, Loader2, CheckCircle2, Inbox } from 'lucide-react';
import type { VerificationConfirmResponse } from '@/types/stock';

export const Route = createFileRoute('/stock/verification')({
  component: VerificationPage,
});

function VerificationPage() {
  return (
    <AuthGuard>
      <VerificationContent />
    </AuthGuard>
  );
}

function VerificationContent() {
  const { data: orders, isLoading, error } = usePendingVerifications();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const confirmMutation = useConfirmVerification({
    onSuccess: (data: VerificationConfirmResponse) => {
      setSuccessMessage(data.message);
      setTimeout(() => setSuccessMessage(null), 5000);
    },
  });

  const handleConfirm = (verificationId: string, verifiedQuantity: number, notes?: string) => {
    confirmMutation.mutate({
      verificationId,
      data: { verified_quantity: verifiedQuantity, notes },
    });
  };

  if (isLoading) {
    return (
      <div className="container max-w-2xl mx-auto py-6 px-4 flex items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading verification tasks...
      </div>
    );
  }

  if (error) {
    return (
      <div className="container max-w-2xl mx-auto py-6 px-4">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-700">Failed to load verification tasks: {error.message}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container max-w-2xl mx-auto py-6 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ClipboardCheck className="h-7 w-7 text-blue-600" />
        <h1 className="text-2xl font-bold">Stock Verification Tasks</h1>
      </div>

      {/* Success message */}
      {successMessage && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-4 pb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
            <p className="text-green-700 font-medium">{successMessage}</p>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {(!orders || orders.length === 0) && (
        <Card>
          <CardContent className="pt-12 pb-12 text-center text-muted-foreground">
            <Inbox className="h-12 w-12 mx-auto mb-4 opacity-40" />
            <p className="text-lg font-medium">No pending verifications</p>
            <p className="text-sm mt-1">New tasks appear here when orders are created with existing stock.</p>
          </CardContent>
        </Card>
      )}

      {/* Orders with verifications */}
      {orders?.map((order) => (
        <Card key={order.order_id}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              <div className="flex items-center justify-between">
                <span>
                  Order: {order.po_number || 'N/A'} — {order.customer_name || 'Unknown'}
                </span>
                {order.order_status && (
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
                      order.order_status === 'approved'
                        ? 'bg-green-100 text-green-700'
                        : order.order_status === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {order.order_status}
                  </span>
                )}
              </div>
              {order.created_at && (
                <p className="text-xs text-muted-foreground font-normal mt-1">
                  Created: {new Date(order.created_at).toLocaleDateString()}
                </p>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pb-4">
            {order.verifications.map((v) => (
              <VerificationTaskCard
                key={v.id}
                verification={v}
                onConfirm={handleConfirm}
                isConfirming={confirmMutation.isPending}
              />
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
