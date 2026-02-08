import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchOrders,
  fetchOrder,
  fetchEmailMonitorStatus,
  approveOrder,
  rejectOrder,
  updateOrder,
  updateLineItem,
  deleteOrder,
} from '@/services/orderService';
import type { OrderUpdateData, LineItemUpdateData } from '@/types/orders';

// ── Queries ──────────────────────────────────────────────────────────

export function useOrders(status?: string) {
  return useQuery({
    queryKey: ['orders', status],
    queryFn: () => fetchOrders(status),
    refetchInterval: 30_000,
  });
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => fetchOrder(id),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useEmailMonitorStatus() {
  return useQuery({
    queryKey: ['emailMonitorStatus'],
    queryFn: fetchEmailMonitorStatus,
    refetchInterval: 15_000,
  });
}

// ── Mutations ────────────────────────────────────────────────────────

export function useApproveOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => approveOrder(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

export function useRejectOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      rejectOrder(id, reason),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

export function useUpdateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: OrderUpdateData }) =>
      updateOrder(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['order', id] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

export function useDeleteOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

export function useUpdateLineItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      orderId,
      itemId,
      data,
    }: {
      orderId: string;
      itemId: string;
      data: LineItemUpdateData;
    }) => updateLineItem(orderId, itemId, data),
    onSuccess: (_data, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: ['order', orderId] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}
