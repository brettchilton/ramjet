import { apiClient } from '@/utils/apiClient';
import type {
  ProductListItem,
  ProductCreateData,
  ProductUpdateData,
} from '@/types/products';

// ── Queries ──────────────────────────────────────────────────────────

export async function fetchProducts(
  search?: string,
  customer?: string
): Promise<ProductListItem[]> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (customer) params.set('customer', customer);
  const qs = params.toString();
  const res = await apiClient.get(`/api/products/${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

// ── Mutations ────────────────────────────────────────────────────────

export async function createProduct(data: ProductCreateData): Promise<ProductListItem> {
  const res = await apiClient.post('/api/products/', data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create product' }));
    throw new Error(err.detail || 'Failed to create product');
  }
  return res.json();
}

export async function updateProduct(code: string, data: ProductUpdateData): Promise<ProductListItem> {
  const res = await apiClient.put(`/api/products/${encodeURIComponent(code)}`, data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update product' }));
    throw new Error(err.detail || 'Failed to update product');
  }
  return res.json();
}

export async function deleteProduct(code: string): Promise<void> {
  const res = await apiClient.delete(`/api/products/${encodeURIComponent(code)}`);
  if (!res.ok) throw new Error('Failed to deactivate product');
}
