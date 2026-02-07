import { useMemo } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useOrders, useEmailMonitorStatus } from '@/hooks/useOrders';
import { StatusBadge } from '@/components/orders/StatusBadge';
import { ConfidenceBadge } from '@/components/orders/ConfidenceBadge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Mail,
  Package,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  FileText,
} from 'lucide-react';

export const Route = createFileRoute('/orders/')({
  component: OrdersDashboard,
});

function OrdersDashboard() {
  return (
    <AuthGuard>
      <OrdersDashboardContent />
    </AuthGuard>
  );
}

function OrdersDashboardContent() {
  const navigate = useNavigate();

  const { data: orders, isLoading: ordersLoading } = useOrders();
  const { data: emailStatus } = useEmailMonitorStatus();

  const counts = useMemo(() => {
    if (!orders) return { pending: 0, approved: 0, rejected: 0, error: 0, total: 0 };
    return {
      pending: orders.filter((o) => o.status === 'pending').length,
      approved: orders.filter((o) => o.status === 'approved').length,
      rejected: orders.filter((o) => o.status === 'rejected').length,
      error: orders.filter((o) => o.status === 'error').length,
      total: orders.length,
    };
  }, [orders]);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-AU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Status Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5 pt-[20px]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Email Monitor</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${emailStatus?.is_running ? 'bg-green-500' : 'bg-gray-400'}`}
              />
              <span className="text-sm font-medium">
                {emailStatus?.is_running ? 'Running' : 'Stopped'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {emailStatus?.emails_processed_total ?? 0} processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.pending}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.approved}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.rejected}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.error}</div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      {ordersLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (orders ?? []).length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Package className="h-12 w-12 mb-4" />
          <p className="text-lg font-medium">No orders found</p>
          <p className="text-sm">Orders will appear here when emails are processed</p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>PO #</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-center">Forms</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(orders ?? []).map((order) => (
                <TableRow
                  key={order.id}
                  className="cursor-pointer"
                  onClick={() =>
                    navigate({ to: '/orders/$orderId', params: { orderId: order.id } })
                  }
                >
                  <TableCell>
                    <StatusBadge status={order.status} />
                  </TableCell>
                  <TableCell className="font-medium">
                    {order.customer_name || '—'}
                  </TableCell>
                  <TableCell>{order.po_number || '—'}</TableCell>
                  <TableCell className="text-center">
                    {order.line_item_count}
                  </TableCell>
                  <TableCell>
                    <ConfidenceBadge confidence={order.extraction_confidence} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDate(order.created_at)}
                  </TableCell>
                  <TableCell className="text-center">
                    {order.has_forms && (
                      <FileText className="h-4 w-4 text-green-500 mx-auto" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
