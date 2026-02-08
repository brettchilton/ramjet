// ── Analytics Types ──────────────────────────────────────────────────

export interface KPIMetrics {
  total_revenue: string;
  total_orders: number;
  approved_orders: number;
  avg_order_value: string;
  total_units: number;
  avg_processing_hours: number | null;
  avg_confidence: number | null;
  review_rate: number;
}

export interface RevenueTrendPoint {
  date: string;
  revenue: string;
  order_count: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
  percentage: number;
}

export interface CustomerMetric {
  customer_name: string;
  revenue: string;
  order_count: number;
  unit_count: number;
}

export interface ProductMetric {
  product_code: string;
  description?: string;
  revenue: string;
  quantity: number;
}

export interface ConfidenceBucket {
  bucket: string;
  count: number;
}

export interface RecentOrder {
  id: string;
  customer_name?: string;
  po_number?: string;
  status: string;
  total: string;
  created_at?: string;
}

export interface DashboardData {
  period: string;
  period_start: string;
  period_end: string;
  kpi: KPIMetrics;
  revenue_trend: RevenueTrendPoint[];
  status_breakdown: StatusBreakdown[];
  top_customers: CustomerMetric[];
  top_products: ProductMetric[];
  confidence_distribution: ConfidenceBucket[];
  recent_orders: RecentOrder[];
}

export type Period = 'ytd' | 'mtd' | 'wtd' | 'custom';
