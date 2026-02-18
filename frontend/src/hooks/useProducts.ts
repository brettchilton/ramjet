import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from '@/services/productService';
import type { ProductCreateData, ProductUpdateData } from '@/types/products';

// ── Queries ──────────────────────────────────────────────────────────

export function useProducts(search?: string, customer?: string) {
  return useQuery({
    queryKey: ['products', search, customer],
    queryFn: () => fetchProducts(search, customer),
    staleTime: 30_000,
  });
}

// ── Mutations ────────────────────────────────────────────────────────

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProductCreateData) => createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ code, data }: { code: string; data: ProductUpdateData }) =>
      updateProduct(code, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => deleteProduct(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}
