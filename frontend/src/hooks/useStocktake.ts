import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSessions,
  fetchSessionDetail,
  startSession,
  recordScan,
  fetchSessionScans,
  completeSession,
  cancelSession,
  fetchDiscrepancies,
} from '@/services/stocktakeService';
import type { StocktakeScanWithProgress } from '@/types/stock';

// ── Queries ─────────────────────────────────────────────────────────

export function useStocktakeSessions() {
  return useQuery({
    queryKey: ['stocktakeSessions'],
    queryFn: fetchSessions,
    staleTime: 30_000,
  });
}

export function useStocktakeSession(sessionId: string) {
  return useQuery({
    queryKey: ['stocktakeSession', sessionId],
    queryFn: () => fetchSessionDetail(sessionId),
    enabled: !!sessionId,
    refetchInterval: 5_000, // Poll for progress updates during active sessions
  });
}

export function useStocktakeScans(sessionId: string) {
  return useQuery({
    queryKey: ['stocktakeScans', sessionId],
    queryFn: () => fetchSessionScans(sessionId),
    enabled: !!sessionId,
    refetchInterval: 5_000,
  });
}

export function useDiscrepancies(sessionId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['stocktakeDiscrepancies', sessionId],
    queryFn: () => fetchDiscrepancies(sessionId),
    enabled: !!sessionId && enabled,
  });
}

// ── Mutations ───────────────────────────────────────────────────────

export function useStartSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, notes }: { name: string; notes?: string }) =>
      startSession(name, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocktakeSessions'] });
    },
  });
}

export function useRecordScan(options?: {
  onSuccess?: (data: StocktakeScanWithProgress) => void;
  onError?: (error: Error) => void;
}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      barcodeScanned,
      notes,
    }: {
      sessionId: string;
      barcodeScanned: string;
      notes?: string;
    }) => recordScan(sessionId, barcodeScanned, notes),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['stocktakeSession', variables.sessionId],
      });
      queryClient.invalidateQueries({
        queryKey: ['stocktakeScans', variables.sessionId],
      });
      options?.onSuccess?.(data);
    },
    onError: options?.onError,
  });
}

export function useCompleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      autoAdjust,
    }: {
      sessionId: string;
      autoAdjust: boolean;
    }) => completeSession(sessionId, autoAdjust),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['stocktakeSessions'] });
      queryClient.invalidateQueries({
        queryKey: ['stocktakeSession', variables.sessionId],
      });
      queryClient.invalidateQueries({
        queryKey: ['stocktakeDiscrepancies', variables.sessionId],
      });
      // Also invalidate stock data since auto-adjust may have changed it
      queryClient.invalidateQueries({ queryKey: ['stockSummary'] });
      queryClient.invalidateQueries({ queryKey: ['stockItems'] });
    },
  });
}

export function useCancelSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => cancelSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocktakeSessions'] });
    },
  });
}
