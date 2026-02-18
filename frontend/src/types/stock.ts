// ── Stock Item ───────────────────────────────────────────────────────

export interface StockItem {
  id: string;
  barcode_id: string;
  product_code: string;
  colour: string;
  quantity: number;
  box_type: 'full' | 'partial';
  status: 'pending_scan' | 'in_stock' | 'picked' | 'scrapped' | 'consumed';
  production_date: string | null;
  scanned_in_at: string | null;
  scanned_out_at: string | null;
  order_id: string | null;
  parent_stock_item_id: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// ── Stock Movement ──────────────────────────────────────────────────

export interface StockMovement {
  id: string;
  stock_item_id: string;
  movement_type: 'stock_in' | 'stock_out' | 'adjustment' | 'stocktake_verified' | 'partial_repack';
  quantity_change: number;
  reason: string | null;
  order_id: string | null;
  stocktake_session_id: string | null;
  performed_by: string;
  created_at: string;
}

// ── Scan Response ───────────────────────────────────────────────────

export interface ScanResponse {
  success: boolean;
  stock_item: StockItem | null;
  movement: StockMovement | null;
  message: string;
  error: string | null;
  barcode_id: string | null;
  product_description: string | null;
}

// ── Scan Session (local tracking) ───────────────────────────────────

export interface ScanSessionEntry {
  barcode_id: string;
  success: boolean;
  message: string;
  product_code?: string;
  colour?: string;
  quantity?: number;
  timestamp: Date;
}

// ── Stock Summary ───────────────────────────────────────────────────

export interface StockSummaryItem {
  product_code: string;
  product_description: string | null;
  colour: string;
  total_units: number;
  carton_count: number;
  threshold_status: 'green' | 'amber' | 'red' | null;
  red_threshold: number | null;
  amber_threshold: number | null;
}

export interface StockSummaryTotals {
  total_skus: number;
  total_units: number;
  total_cartons: number;
  low_stock_count: number;
}

export interface StockSummaryResponse {
  summary: StockSummaryTotals;
  items: StockSummaryItem[];
}

// ── Stock Item Detail ──────────────────────────────────────────────

export interface StockItemDetail extends StockItem {
  product_description: string | null;
  scanned_in_by: string | null;
  scanned_out_by: string | null;
  movements: StockMovement[];
}

// ── Stock Item List ────────────────────────────────────────────────

export interface StockItemListResponse {
  items: StockItem[];
  total: number;
}

// ── Stock Threshold ────────────────────────────────────────────────

export interface StockThreshold {
  id: string;
  product_code: string;
  colour: string | null;
  red_threshold: number;
  amber_threshold: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface StockThresholdCreate {
  product_code: string;
  colour?: string | null;
  red_threshold: number;
  amber_threshold: number;
}

export interface StockThresholdUpdate {
  red_threshold?: number;
  amber_threshold?: number;
}

// ── Partial Repack ──────────────────────────────────────────────────

export interface PartialRepackResponse {
  success: boolean;
  original_item: StockItem | null;
  new_partial_item: StockItem | null;
  units_taken: number;
  units_remaining: number;
  label_url: string | null;
  message: string;
  error: string | null;
}

// ── Scan Mode ───────────────────────────────────────────────────────

export type ScanMode = 'stock_in' | 'stock_out';

// ── Stock Verification ─────────────────────────────────────────────

export interface StockVerification {
  id: string;
  order_line_item_id: string;
  product_code: string;
  colour: string;
  system_stock_quantity: number;
  verified_quantity: number | null;
  status: 'pending' | 'confirmed' | 'expired';
  line_number: number | null;
  ordered_quantity: number | null;
  product_description: string | null;
  created_at: string | null;
}

export interface VerificationOrder {
  order_id: string;
  customer_name: string | null;
  po_number: string | null;
  order_status: string | null;
  created_at: string | null;
  verifications: StockVerification[];
}

export interface VerificationConfirmRequest {
  verified_quantity: number;
  notes?: string;
}

export interface VerificationConfirmResponse {
  verification_id: string;
  status: string;
  verified_quantity: number;
  works_order_triggered: boolean;
  message: string;
}

// ── Stocktake ─────────────────────────────────────────────────────────

export interface StocktakeSession {
  id: string;
  name: string | null;
  status: 'in_progress' | 'completed' | 'cancelled';
  started_by: string;
  completed_by: string | null;
  started_at: string;
  completed_at: string | null;
  total_expected: number | null;
  total_scanned: number | null;
  total_discrepancies: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SessionProgress {
  total_expected: number;
  total_scanned: number;
  percentage: number;
}

export interface SessionDetailResponse {
  session: StocktakeSession;
  progress: SessionProgress;
}

export interface StocktakeScan {
  id: string;
  session_id: string;
  barcode_scanned: string;
  stock_item_id: string | null;
  scan_result: 'found' | 'not_in_system' | 'already_scanned' | 'wrong_status';
  scanned_by: string;
  scanned_at: string;
  notes: string | null;
}

export interface StocktakeScanWithProgress {
  scan: StocktakeScan;
  scan_result: string;
  stock_item: StockItem | null;
  session_progress: SessionProgress;
}

export interface MissingItem {
  stock_item_id: string;
  barcode_id: string;
  product_code: string;
  colour: string;
  quantity: number;
  last_movement: string | null;
  last_movement_date: string | null;
}

export interface UnexpectedScan {
  barcode_scanned: string;
  scan_result: string;
  scanned_at: string | null;
}

export interface DiscrepancySummary {
  total_expected: number;
  total_found: number;
  total_missing: number;
  total_unexpected: number;
}

export interface DiscrepancyReport {
  missing_items: MissingItem[];
  unexpected_scans: UnexpectedScan[];
  summary: DiscrepancySummary;
}
