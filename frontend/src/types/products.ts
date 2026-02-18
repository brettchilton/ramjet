// ── Product Types ───────────────────────────────────────────────────

export interface ProductListItem {
  product_code: string;
  product_description: string;
  customer_name?: string;
  is_active: boolean;
  is_stockable: boolean;
}

export interface ProductFullResponse extends ProductListItem {
  manufacturing?: ManufacturingSpec;
  materials: MaterialSpec[];
  packaging?: PackagingSpec;
  pricing: PricingEntry[];
}

export interface ManufacturingSpec {
  mould_no?: string;
  cycle_time_seconds?: number;
  shot_weight_grams?: string;
  num_cavities?: number;
  product_weight_grams?: string;
  estimated_running_time_hours?: string;
  machine_min_requirements?: string;
}

export interface MaterialSpec {
  colour: string;
  material_grade?: string;
  material_type?: string;
  colour_no?: string;
  colour_supplier?: string;
  mb_add_rate?: string;
  additive?: string;
  additive_add_rate?: string;
  additive_supplier?: string;
}

export interface PackagingSpec {
  qty_per_bag?: number;
  bag_size?: string;
  qty_per_carton?: number;
  carton_size?: string;
  cartons_per_pallet?: number;
  cartons_per_layer?: number;
}

export interface PricingEntry {
  colour: string;
  customer_name?: string;
  unit_price: string;
  currency: string;
  effective_date?: string;
}

// ── Request Types ────────────────────────────────────────────────────

export interface ProductCreateData {
  product_code: string;
  product_description: string;
  customer_name?: string;
  is_stockable?: boolean;
}

export interface ProductUpdateData {
  product_description?: string;
  customer_name?: string;
  is_active?: boolean;
  is_stockable?: boolean;
}
