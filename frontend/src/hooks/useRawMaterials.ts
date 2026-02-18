import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchRawMaterials,
  fetchRawMaterial,
  createRawMaterial,
  updateRawMaterial,
  deleteRawMaterial,
  receiveDelivery,
  recordUsage,
  adjustStock,
} from '@/services/rawMaterialService';
import type {
  RawMaterialCreateData,
  RawMaterialUpdateData,
  ReceiveDeliveryData,
  RecordUsageData,
  AdjustStockData,
} from '@/types/rawMaterials';

// ── Queries ──────────────────────────────────────────────────────────

export function useRawMaterials(search?: string, materialType?: string) {
  return useQuery({
    queryKey: ['rawMaterials', search, materialType],
    queryFn: () => fetchRawMaterials(search, materialType),
    staleTime: 30_000,
  });
}

export function useRawMaterial(id: string) {
  return useQuery({
    queryKey: ['rawMaterial', id],
    queryFn: () => fetchRawMaterial(id),
    enabled: !!id,
    staleTime: 30_000,
  });
}

// ── Mutations ────────────────────────────────────────────────────────

export function useCreateRawMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RawMaterialCreateData) => createRawMaterial(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}

export function useUpdateRawMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RawMaterialUpdateData }) =>
      updateRawMaterial(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterial', id] });
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}

export function useDeleteRawMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteRawMaterial(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}

export function useReceiveDelivery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReceiveDeliveryData }) =>
      receiveDelivery(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterial', id] });
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}

export function useRecordUsage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RecordUsageData }) =>
      recordUsage(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterial', id] });
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}

export function useAdjustStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AdjustStockData }) =>
      adjustStock(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rawMaterial', id] });
      queryClient.invalidateQueries({ queryKey: ['rawMaterials'] });
    },
  });
}
