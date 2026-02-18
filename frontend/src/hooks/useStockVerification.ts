import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchPendingVerifications,
  confirmVerification,
} from '@/services/stockVerificationService';
import type { VerificationConfirmRequest, VerificationConfirmResponse } from '@/types/stock';

export function usePendingVerifications() {
  return useQuery({
    queryKey: ['stockVerifications', 'pending'],
    queryFn: fetchPendingVerifications,
    refetchInterval: 15_000,
  });
}

export function useConfirmVerification(options?: {
  onSuccess?: (data: VerificationConfirmResponse) => void;
  onError?: (error: Error) => void;
}) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      verificationId,
      data,
    }: {
      verificationId: string;
      data: VerificationConfirmRequest;
    }) => confirmVerification(verificationId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['stockVerifications'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      options?.onSuccess?.(data);
    },
    onError: options?.onError,
  });
}
