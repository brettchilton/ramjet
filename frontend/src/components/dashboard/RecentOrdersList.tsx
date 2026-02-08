import { useNavigate } from '@tanstack/react-router';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/orders/StatusBadge';
import type { RecentOrder } from '@/types/analytics';
import { formatCurrency } from '@/utils/formatters';

interface RecentOrdersListProps {
  data: RecentOrder[];
}

export function RecentOrdersList({ data }: RecentOrdersListProps) {
  const navigate = useNavigate();

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '--';
    return new Date(dateStr).toLocaleDateString('en-AU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Recent Orders</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="max-h-[280px] overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>PO #</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((order) => (
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
                  <TableCell className="text-sm font-medium">
                    {order.customer_name || '--'}
                  </TableCell>
                  <TableCell className="text-sm">{order.po_number || '--'}</TableCell>
                  <TableCell className="text-right text-sm">
                    {formatCurrency(order.total)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(order.created_at)}
                  </TableCell>
                </TableRow>
              ))}
              {data.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No recent orders
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
