// ── Order Types ──────────────────────────────────────────────────────

export interface OrderLineItem {
  id: string;
  order_id: string;
  line_number: number;
  product_code?: string;
  matched_product_code?: string;
  product_description?: string;
  colour?: string;
  quantity: number;
  unit_price?: string;
  line_total?: string;
  confidence?: string;
  needs_review: boolean;
  created_at?: string;
}

export interface OrderSummary {
  id: string;
  status: string;
  customer_name?: string;
  po_number?: string;
  extraction_confidence?: string;
  line_item_count: number;
  has_forms: boolean;
  created_at?: string;
}

export interface OrderDetail {
  id: string;
  email_id?: number;
  status: string;
  customer_name?: string;
  po_number?: string;
  po_date?: string;
  delivery_date?: string;
  special_instructions?: string;
  extraction_confidence?: string;
  extraction_raw_json?: Record<string, unknown>;
  approved_by?: string;
  approved_at?: string;
  rejected_reason?: string;
  has_office_order: boolean;
  created_at?: string;
  updated_at?: string;
  line_items: OrderLineItem[];
}

export interface OrderUpdateData {
  customer_name?: string;
  po_number?: string;
  po_date?: string;
  delivery_date?: string;
  special_instructions?: string;
}

export interface LineItemUpdateData {
  product_code?: string;
  matched_product_code?: string;
  product_description?: string;
  colour?: string;
  quantity?: number;
  unit_price?: string;
}

// ── Processing / Action Responses ────────────────────────────────────

export interface ProcessEmailsResponse {
  orders_created: number;
  errors: number;
  message: string;
}

export interface ApproveResponse {
  order_id: string;
  status: string;
  message: string;
  office_order_generated: boolean;
  works_orders_generated: number;
}

export interface RejectResponse {
  order_id: string;
  status: string;
  message: string;
}

// ── Email / System Types ─────────────────────────────────────────────

export interface EmailMonitorStatus {
  is_running: boolean;
  last_poll_at?: string;
  last_error?: string;
  emails_processed_total: number;
}

export interface EmailAttachment {
  id: number;
  filename?: string;
  content_type?: string;
  file_size_bytes?: number;
}

export interface IncomingEmailDetail {
  id: number;
  gmail_message_id: string;
  sender?: string;
  subject?: string;
  body_text?: string;
  body_html?: string;
  received_at?: string;
  processed: boolean;
  attachments: EmailAttachment[];
}

// ── Product Types (for FormPreview) ──────────────────────────────────

export interface ProductFullResponse {
  product_code: string;
  product_description: string;
  customer_name?: string;
  is_active: boolean;
  manufacturing?: {
    mould_no?: string;
    cycle_time_seconds?: number;
    shot_weight_grams?: string;
    num_cavities?: number;
    product_weight_grams?: string;
    estimated_running_time_hours?: string;
    machine_min_requirements?: string;
  };
  materials: {
    colour: string;
    material_grade?: string;
    material_type?: string;
    colour_no?: string;
    colour_supplier?: string;
    mb_add_rate?: string;
    additive?: string;
    additive_add_rate?: string;
    additive_supplier?: string;
  }[];
  packaging?: {
    qty_per_bag?: number;
    bag_size?: string;
    qty_per_carton?: number;
    carton_size?: string;
    cartons_per_pallet?: number;
    cartons_per_layer?: number;
  };
  pricing: {
    colour: string;
    customer_name?: string;
    unit_price: string;
    currency: string;
    effective_date?: string;
  }[];
}

export interface CalculationResponse {
  product_code: string;
  colour: string;
  quantity: number;
  material_requirements: {
    base_material_kg: number;
    material_grade?: string;
    material_type?: string;
    masterbatch_kg: number;
    colour_no?: string;
    colour_supplier?: string;
    additive_kg: number;
    additive?: string;
    additive_supplier?: string;
    total_material_kg: number;
  };
  packaging_requirements: {
    bags_needed: number;
    bag_size?: string;
    cartons_needed: number;
    carton_size?: string;
  };
  estimated_cost: number;
}
