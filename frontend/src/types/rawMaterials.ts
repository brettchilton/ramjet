// ── Raw Material Types ───────────────────────────────────────────────

export interface RawMaterial {
  id: string;
  material_code: string;
  material_name: string;
  material_type: string;
  unit_of_measure: string;
  current_stock: string; // Decimal as string from API
  red_threshold: string;
  amber_threshold: string;
  default_supplier?: string;
  unit_cost?: string;
  is_active: boolean;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  threshold_status: 'green' | 'amber' | 'red';
}

export interface RawMaterialMovement {
  id: string;
  raw_material_id: string;
  movement_type: 'received' | 'used' | 'adjustment' | 'stocktake';
  quantity: string;
  unit_cost?: string;
  supplier?: string;
  delivery_note?: string;
  reason?: string;
  performed_by: string;
  performed_by_name?: string;
  created_at: string;
}

export interface RawMaterialDetail extends RawMaterial {
  movements: RawMaterialMovement[];
}

// ── Request Types ────────────────────────────────────────────────────

export interface RawMaterialCreateData {
  material_code: string;
  material_name: string;
  material_type: string;
  unit_of_measure: string;
  red_threshold?: number;
  amber_threshold?: number;
  default_supplier?: string;
  unit_cost?: number;
  notes?: string;
}

export interface RawMaterialUpdateData {
  material_name?: string;
  material_type?: string;
  unit_of_measure?: string;
  red_threshold?: number;
  amber_threshold?: number;
  default_supplier?: string;
  unit_cost?: number;
  is_active?: boolean;
  notes?: string;
}

export interface ReceiveDeliveryData {
  quantity: number;
  unit_cost?: number;
  supplier?: string;
  delivery_note?: string;
}

export interface RecordUsageData {
  quantity: number;
  reason?: string;
}

export interface AdjustStockData {
  quantity: number;
  reason: string;
}
