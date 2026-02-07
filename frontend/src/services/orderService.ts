import { apiClient } from '@/utils/apiClient';
import type {
  OrderSummary,
  OrderDetail,
  OrderUpdateData,
  LineItemUpdateData,
  ApproveResponse,
  RejectResponse,
  ProcessEmailsResponse,
  EmailMonitorStatus,
  IncomingEmailDetail,
  ProductFullResponse,
  CalculationResponse,
} from '@/types/orders';

// ── Orders ───────────────────────────────────────────────────────────

export async function fetchOrders(status?: string): Promise<OrderSummary[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await apiClient.get(`/api/orders/${params}`);
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

export async function fetchOrder(id: string): Promise<OrderDetail> {
  const res = await apiClient.get(`/api/orders/${id}`);
  if (!res.ok) throw new Error('Failed to fetch order');
  return res.json();
}

export async function updateOrder(id: string, data: OrderUpdateData): Promise<OrderDetail> {
  const res = await apiClient.put(`/api/orders/${id}`, data);
  if (!res.ok) throw new Error('Failed to update order');
  return res.json();
}

export async function updateLineItem(
  orderId: string,
  itemId: string,
  data: LineItemUpdateData
): Promise<void> {
  const res = await apiClient.put(`/api/orders/${orderId}/line-items/${itemId}`, data);
  if (!res.ok) throw new Error('Failed to update line item');
}

export async function approveOrder(id: string): Promise<ApproveResponse> {
  const res = await apiClient.post(`/api/orders/${id}/approve`);
  if (!res.ok) throw new Error('Failed to approve order');
  return res.json();
}

export async function rejectOrder(id: string, reason: string): Promise<RejectResponse> {
  const res = await apiClient.post(`/api/orders/${id}/reject`, { reason });
  if (!res.ok) throw new Error('Failed to reject order');
  return res.json();
}

// ── Download URLs ────────────────────────────────────────────────────

export function getOfficeOrderUrl(id: string): string {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  return `${baseUrl}/api/orders/${id}/forms/office-order`;
}

export function getWorksOrderUrl(orderId: string, itemId: string): string {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  return `${baseUrl}/api/orders/${orderId}/forms/works-order/${itemId}`;
}

export function getSourceAttachmentUrl(orderId: string, attachmentId: number): string {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8006';
  return `${baseUrl}/api/orders/${orderId}/source-pdf/${attachmentId}`;
}

// ── Email / System ───────────────────────────────────────────────────

export async function fetchEmailMonitorStatus(): Promise<EmailMonitorStatus> {
  const res = await apiClient.get('/api/system/email-monitor/status');
  if (!res.ok) throw new Error('Failed to fetch email monitor status');
  return res.json();
}

export async function fetchEmail(emailId: number): Promise<IncomingEmailDetail> {
  const res = await apiClient.get(`/api/system/emails/${emailId}`);
  if (!res.ok) throw new Error('Failed to fetch email');
  return res.json();
}

export async function processEmails(): Promise<ProcessEmailsResponse> {
  const res = await apiClient.post('/api/orders/process-pending');
  if (!res.ok) throw new Error('Failed to process emails');
  return res.json();
}

// ── Products ─────────────────────────────────────────────────────────

export async function fetchProductSpecs(productCode: string): Promise<ProductFullResponse> {
  const res = await apiClient.get(`/api/products/${encodeURIComponent(productCode)}`);
  if (!res.ok) throw new Error('Failed to fetch product specs');
  return res.json();
}

export async function calculateMaterials(
  productCode: string,
  colour: string,
  quantity: number
): Promise<CalculationResponse> {
  const params = new URLSearchParams({
    colour,
    quantity: String(quantity),
  });
  const res = await apiClient.get(
    `/api/products/${encodeURIComponent(productCode)}/calculate?${params}`
  );
  if (!res.ok) throw new Error('Failed to calculate materials');
  return res.json();
}
