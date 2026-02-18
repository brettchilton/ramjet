import { apiClient } from '@/utils/apiClient';
import type {
  VerificationOrder,
  VerificationConfirmRequest,
  VerificationConfirmResponse,
} from '@/types/stock';

export async function fetchPendingVerifications(): Promise<VerificationOrder[]> {
  const res = await apiClient.get('/api/stock-verifications/pending');
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to fetch verifications' }));
    throw new Error(error.detail || 'Failed to fetch verifications');
  }
  return res.json();
}

export async function fetchOrderVerifications(orderId: string): Promise<VerificationOrder[]> {
  const res = await apiClient.get(`/api/stock-verifications/order/${orderId}`);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to fetch order verifications' }));
    throw new Error(error.detail || 'Failed to fetch order verifications');
  }
  return res.json();
}

export async function confirmVerification(
  verificationId: string,
  data: VerificationConfirmRequest,
): Promise<VerificationConfirmResponse> {
  const res = await apiClient.post(
    `/api/stock-verifications/${verificationId}/confirm`,
    data,
  );
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to confirm verification' }));
    throw new Error(error.detail || 'Failed to confirm verification');
  }
  return res.json();
}
