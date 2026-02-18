import { apiClient } from '@/utils/apiClient';
import type {
  ScanResponse,
  PartialRepackResponse,
  StockSummaryResponse,
  StockItemDetail,
  StockItemListResponse,
  StockThreshold,
  StockThresholdCreate,
  StockThresholdUpdate,
} from '@/types/stock';

// ── Types ───────────────────────────────────────────────────────────

export interface LabelGenerateParams {
  product_code: string;
  colour: string;
  quantity_per_carton: number;
  number_of_labels: number;
  box_type: 'full' | 'partial';
  production_date?: string; // YYYY-MM-DD
}

export interface ProductListItem {
  product_code: string;
  product_description: string;
  customer_name: string | null;
  is_active: boolean;
  is_stockable: boolean;
}

export interface ProductFullResponse {
  product_code: string;
  product_description: string;
  customer_name: string | null;
  is_active: boolean;
  is_stockable: boolean;
  materials: Array<{
    colour: string;
    material_grade: string | null;
    material_type: string | null;
  }>;
  packaging: {
    qty_per_carton: number | null;
  } | null;
}

// ── Products (for label form dropdowns) ─────────────────────────────

export async function fetchStockableProducts(): Promise<ProductListItem[]> {
  const res = await apiClient.get('/api/products/');
  if (!res.ok) throw new Error('Failed to fetch products');
  const products: ProductListItem[] = await res.json();
  return products.filter((p) => p.is_stockable && p.is_active);
}

export async function fetchProductDetail(productCode: string): Promise<ProductFullResponse> {
  const res = await apiClient.get(`/api/products/${encodeURIComponent(productCode)}`);
  if (!res.ok) throw new Error('Failed to fetch product details');
  return res.json();
}

// ── Scan-In ────────────────────────────────────────────────────────

export async function scanIn(barcodeId: string): Promise<ScanResponse> {
  const res = await apiClient.post('/api/stock/scan-in', { barcode_id: barcodeId });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Scan request failed' }));
    throw new Error(error.detail || 'Scan request failed');
  }
  return res.json();
}

// ── Scan-Out ─────────────────────────────────────────────────────────

export async function scanOut(
  barcodeId: string,
  orderId?: string,
): Promise<ScanResponse> {
  const body: Record<string, string> = { barcode_id: barcodeId };
  if (orderId) body.order_id = orderId;

  const res = await apiClient.post('/api/stock/scan-out', body);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Scan-out request failed' }));
    throw new Error(error.detail || 'Scan-out request failed');
  }
  return res.json();
}

// ── Partial Repack ──────────────────────────────────────────────────

export async function partialRepack(
  barcodeId: string,
  unitsTaken: number,
  orderId?: string,
): Promise<PartialRepackResponse> {
  const body: Record<string, unknown> = {
    barcode_id: barcodeId,
    units_taken: unitsTaken,
  };
  if (orderId) body.order_id = orderId;

  const res = await apiClient.post('/api/stock/partial-repack', body);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Partial repack request failed' }));
    throw new Error(error.detail || 'Partial repack request failed');
  }
  return res.json();
}

// ── Single Label Download ───────────────────────────────────────────

export async function downloadSingleLabel(barcodeId: string): Promise<Blob> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  const token = localStorage.getItem('authToken');

  const res = await fetch(
    `${baseUrl}/api/stock/labels/single/${encodeURIComponent(barcodeId)}`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: 'include',
    },
  );

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to download label' }));
    throw new Error(error.detail || 'Failed to download label');
  }
  return res.blob();
}

// ── Stock Summary (Dashboard) ──────────────────────────────────────

export async function fetchStockSummary(params?: {
  search?: string;
  colour?: string;
  status_filter?: string;
}): Promise<StockSummaryResponse> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.colour) searchParams.set('colour', params.colour);
  if (params?.status_filter) searchParams.set('status_filter', params.status_filter);

  const qs = searchParams.toString();
  const res = await apiClient.get(`/api/stock/summary${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error('Failed to fetch stock summary');
  return res.json();
}

// ── Stock Item List ────────────────────────────────────────────────

export async function fetchStockItems(params?: {
  product_code?: string;
  colour?: string;
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<StockItemListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.product_code) searchParams.set('product_code', params.product_code);
  if (params?.colour) searchParams.set('colour', params.colour);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.search) searchParams.set('search', params.search);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const qs = searchParams.toString();
  const res = await apiClient.get(`/api/stock/items${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error('Failed to fetch stock items');
  return res.json();
}

// ── Stock Item Detail ──────────────────────────────────────────────

export async function fetchStockItemDetail(stockItemId: string): Promise<StockItemDetail> {
  const res = await apiClient.get(`/api/stock/items/${stockItemId}`);
  if (!res.ok) throw new Error('Failed to fetch stock item detail');
  return res.json();
}

// ── Threshold CRUD ─────────────────────────────────────────────────

export async function fetchThresholds(): Promise<StockThreshold[]> {
  const res = await apiClient.get('/api/stock/thresholds');
  if (!res.ok) throw new Error('Failed to fetch thresholds');
  return res.json();
}

export async function createThreshold(data: StockThresholdCreate): Promise<StockThreshold> {
  const res = await apiClient.post('/api/stock/thresholds', data);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to create threshold' }));
    throw new Error(error.detail || 'Failed to create threshold');
  }
  return res.json();
}

export async function updateThreshold(id: string, data: StockThresholdUpdate): Promise<StockThreshold> {
  const res = await apiClient.put(`/api/stock/thresholds/${id}`, data);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to update threshold' }));
    throw new Error(error.detail || 'Failed to update threshold');
  }
  return res.json();
}

export async function deleteThreshold(id: string): Promise<void> {
  const res = await apiClient.delete(`/api/stock/thresholds/${id}`);
  if (!res.ok) throw new Error('Failed to delete threshold');
}

// ── Label Generation ────────────────────────────────────────────────

export async function generateLabels(params: LabelGenerateParams): Promise<Blob> {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  const token = localStorage.getItem('authToken');

  const res = await fetch(`${baseUrl}/api/stock/labels/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: 'include',
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to generate labels' }));
    throw new Error(error.detail || 'Failed to generate labels');
  }

  return res.blob();
}
