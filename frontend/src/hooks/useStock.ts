import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchStockableProducts,
  fetchProductDetail,
  generateLabels,
  scanIn,
  scanOut,
  partialRepack,
  downloadSingleLabel,
  fetchStockSummary,
  fetchStockItems,
  fetchStockItemDetail,
  fetchThresholds,
  createThreshold,
  updateThreshold,
  deleteThreshold,
} from '@/services/stockService';
import type { LabelGenerateParams } from '@/services/stockService';
import type {
  ScanResponse,
  PartialRepackResponse,
  StockThresholdCreate,
  StockThresholdUpdate,
} from '@/types/stock';

// ── Queries ──────────────────────────────────────────────────────────

export function useStockableProducts() {
  return useQuery({
    queryKey: ['products', 'stockable'],
    queryFn: fetchStockableProducts,
    staleTime: 60_000,
  });
}

export function useProductDetail(productCode: string) {
  return useQuery({
    queryKey: ['product', productCode],
    queryFn: () => fetchProductDetail(productCode),
    enabled: !!productCode,
    staleTime: 60_000,
  });
}

// ── Mutations ────────────────────────────────────────────────────────

export function useGenerateLabels() {
  return useMutation({
    mutationFn: (params: LabelGenerateParams) => generateLabels(params),
    onSuccess: (blob) => {
      // Auto-download the PDF
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'stock-labels.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });
}

export function useScanIn(options?: {
  onSuccess?: (data: ScanResponse) => void;
  onError?: (error: Error) => void;
}) {
  return useMutation({
    mutationFn: (barcodeId: string) => scanIn(barcodeId),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

export function useScanOut(options?: {
  onSuccess?: (data: ScanResponse) => void;
  onError?: (error: Error) => void;
}) {
  return useMutation({
    mutationFn: ({ barcodeId, orderId }: { barcodeId: string; orderId?: string }) =>
      scanOut(barcodeId, orderId),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

export function usePartialRepack(options?: {
  onSuccess?: (data: PartialRepackResponse) => void;
  onError?: (error: Error) => void;
}) {
  return useMutation({
    mutationFn: ({
      barcodeId,
      unitsTaken,
      orderId,
    }: {
      barcodeId: string;
      unitsTaken: number;
      orderId?: string;
    }) => partialRepack(barcodeId, unitsTaken, orderId),
    onSuccess: options?.onSuccess,
    onError: options?.onError,
  });
}

export function useDownloadLabel() {
  return useMutation({
    mutationFn: (barcodeId: string) => downloadSingleLabel(barcodeId),
    onSuccess: (blob, barcodeId) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `label-${barcodeId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });
}

// ── Dashboard Queries ───────────────────────────────────────────────

export function useStockSummary(params?: {
  search?: string;
  colour?: string;
  status_filter?: string;
}) {
  return useQuery({
    queryKey: ['stockSummary', params],
    queryFn: () => fetchStockSummary(params),
    refetchInterval: 30_000,
  });
}

export function useStockItems(params?: {
  product_code?: string;
  colour?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['stockItems', params],
    queryFn: () => fetchStockItems(params),
    enabled: !!(params?.product_code || params?.colour || params?.search),
  });
}

export function useStockItemDetail(stockItemId: string) {
  return useQuery({
    queryKey: ['stockItem', stockItemId],
    queryFn: () => fetchStockItemDetail(stockItemId),
    enabled: !!stockItemId,
  });
}

// ── Threshold Hooks ─────────────────────────────────────────────────

export function useThresholds() {
  return useQuery({
    queryKey: ['stockThresholds'],
    queryFn: fetchThresholds,
    staleTime: 60_000,
  });
}

export function useCreateThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: StockThresholdCreate) => createThreshold(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockThresholds'] });
      queryClient.invalidateQueries({ queryKey: ['stockSummary'] });
    },
  });
}

export function useUpdateThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: StockThresholdUpdate }) =>
      updateThreshold(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockThresholds'] });
      queryClient.invalidateQueries({ queryKey: ['stockSummary'] });
    },
  });
}

export function useDeleteThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteThreshold(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stockThresholds'] });
      queryClient.invalidateQueries({ queryKey: ['stockSummary'] });
    },
  });
}
