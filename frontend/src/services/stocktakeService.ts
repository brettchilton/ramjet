import { apiClient } from '@/utils/apiClient';
import type {
  StocktakeSession,
  SessionDetailResponse,
  StocktakeScanWithProgress,
  StocktakeScan,
  DiscrepancyReport,
} from '@/types/stock';

// ── Sessions ────────────────────────────────────────────────────────

export async function fetchSessions(): Promise<StocktakeSession[]> {
  const res = await apiClient.get('/api/stocktake/sessions');
  if (!res.ok) throw new Error('Failed to fetch stocktake sessions');
  return res.json();
}

export async function fetchSessionDetail(sessionId: string): Promise<SessionDetailResponse> {
  const res = await apiClient.get(`/api/stocktake/sessions/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch session detail');
  return res.json();
}

export async function startSession(name: string, notes?: string): Promise<StocktakeSession> {
  const body: Record<string, string> = { name };
  if (notes) body.notes = notes;

  const res = await apiClient.post('/api/stocktake/sessions', body);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to start session' }));
    throw new Error(error.detail || 'Failed to start session');
  }
  return res.json();
}

// ── Scanning ────────────────────────────────────────────────────────

export async function recordScan(
  sessionId: string,
  barcodeScanned: string,
  notes?: string,
): Promise<StocktakeScanWithProgress> {
  const body: Record<string, string> = { barcode_scanned: barcodeScanned };
  if (notes) body.notes = notes;

  const res = await apiClient.post(`/api/stocktake/sessions/${sessionId}/scan`, body);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Scan failed' }));
    throw new Error(error.detail || 'Scan failed');
  }
  return res.json();
}

export async function fetchSessionScans(
  sessionId: string,
  limit: number = 50,
): Promise<StocktakeScan[]> {
  const res = await apiClient.get(`/api/stocktake/sessions/${sessionId}/scans?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch session scans');
  return res.json();
}

// ── Complete / Cancel ───────────────────────────────────────────────

export async function completeSession(
  sessionId: string,
  autoAdjust: boolean = false,
): Promise<StocktakeSession> {
  const res = await apiClient.post(`/api/stocktake/sessions/${sessionId}/complete`, {
    auto_adjust: autoAdjust,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to complete session' }));
    throw new Error(error.detail || 'Failed to complete session');
  }
  return res.json();
}

export async function cancelSession(sessionId: string): Promise<StocktakeSession> {
  const res = await apiClient.post(`/api/stocktake/sessions/${sessionId}/cancel`);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to cancel session' }));
    throw new Error(error.detail || 'Failed to cancel session');
  }
  return res.json();
}

// ── Discrepancies ───────────────────────────────────────────────────

export async function fetchDiscrepancies(sessionId: string): Promise<DiscrepancyReport> {
  const res = await apiClient.get(`/api/stocktake/sessions/${sessionId}/discrepancies`);
  if (!res.ok) throw new Error('Failed to fetch discrepancies');
  return res.json();
}
