import { apiClient } from '@/utils/apiClient';
import type {
  RawMaterial,
  RawMaterialDetail,
  RawMaterialMovement,
  RawMaterialCreateData,
  RawMaterialUpdateData,
  ReceiveDeliveryData,
  RecordUsageData,
  AdjustStockData,
} from '@/types/rawMaterials';

// ── Queries ──────────────────────────────────────────────────────────

export async function fetchRawMaterials(
  search?: string,
  materialType?: string
): Promise<RawMaterial[]> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (materialType) params.set('material_type', materialType);
  const qs = params.toString();
  const res = await apiClient.get(`/api/raw-materials/${qs ? `?${qs}` : ''}`);
  if (!res.ok) throw new Error('Failed to fetch raw materials');
  return res.json();
}

export async function fetchRawMaterial(id: string): Promise<RawMaterialDetail> {
  const res = await apiClient.get(`/api/raw-materials/${id}`);
  if (!res.ok) throw new Error('Failed to fetch raw material');
  return res.json();
}

// ── Mutations ────────────────────────────────────────────────────────

export async function createRawMaterial(data: RawMaterialCreateData): Promise<RawMaterial> {
  const res = await apiClient.post('/api/raw-materials/', data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create raw material' }));
    throw new Error(err.detail || 'Failed to create raw material');
  }
  return res.json();
}

export async function updateRawMaterial(id: string, data: RawMaterialUpdateData): Promise<RawMaterial> {
  const res = await apiClient.put(`/api/raw-materials/${id}`, data);
  if (!res.ok) throw new Error('Failed to update raw material');
  return res.json();
}

export async function deleteRawMaterial(id: string): Promise<void> {
  const res = await apiClient.delete(`/api/raw-materials/${id}`);
  if (!res.ok) throw new Error('Failed to delete raw material');
}

export async function receiveDelivery(id: string, data: ReceiveDeliveryData): Promise<RawMaterialMovement> {
  const res = await apiClient.post(`/api/raw-materials/${id}/receive`, data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to receive delivery' }));
    throw new Error(err.detail || 'Failed to receive delivery');
  }
  return res.json();
}

export async function recordUsage(id: string, data: RecordUsageData): Promise<RawMaterialMovement> {
  const res = await apiClient.post(`/api/raw-materials/${id}/use`, data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to record usage' }));
    throw new Error(err.detail || 'Failed to record usage');
  }
  return res.json();
}

export async function adjustStock(id: string, data: AdjustStockData): Promise<RawMaterialMovement> {
  const res = await apiClient.post(`/api/raw-materials/${id}/adjustment`, data);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to adjust stock' }));
    throw new Error(err.detail || 'Failed to adjust stock');
  }
  return res.json();
}
