import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useRawMaterials, useCreateRawMaterial, useUpdateRawMaterial, useDeleteRawMaterial, useReceiveDelivery, useRecordUsage } from '@/hooks/useRawMaterials';
import { RawMaterialTable } from '@/components/raw-materials/RawMaterialTable';
import { ReceiveForm } from '@/components/raw-materials/ReceiveForm';
import { UsageForm } from '@/components/raw-materials/UsageForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Package, AlertTriangle, AlertCircle } from 'lucide-react';
import type { RawMaterial, RawMaterialCreateData, RawMaterialUpdateData, ReceiveDeliveryData, RecordUsageData } from '@/types/rawMaterials';

export const Route = createFileRoute('/raw-materials/')({
  component: RawMaterialsPage,
});

function RawMaterialsPage() {
  return (
    <AuthGuard>
      <RawMaterialsContent />
    </AuthGuard>
  );
}

const MATERIAL_TYPES = ['resin', 'masterbatch', 'additive', 'packaging', 'other'] as const;
const UNITS = ['kg', 'litres', 'units', 'rolls'] as const;

function RawMaterialsContent() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editMaterial, setEditMaterial] = useState<RawMaterial | null>(null);
  const [receiveMaterial, setReceiveMaterial] = useState<RawMaterial | null>(null);
  const [useMaterial, setUseMaterial] = useState<RawMaterial | null>(null);

  const { data: materials, isLoading } = useRawMaterials(
    search || undefined,
    typeFilter || undefined,
  );

  const createMutation = useCreateRawMaterial();
  const updateMutation = useUpdateRawMaterial();
  const deleteMutation = useDeleteRawMaterial();
  const receiveMutation = useReceiveDelivery();
  const usageMutation = useRecordUsage();

  const counts = {
    total: materials?.length || 0,
    red: materials?.filter((m) => m.threshold_status === 'red').length || 0,
    amber: materials?.filter((m) => m.threshold_status === 'amber').length || 0,
    green: materials?.filter((m) => m.threshold_status === 'green').length || 0,
  };

  const handleCreate = (data: RawMaterialCreateData) => {
    createMutation.mutate(data, {
      onSuccess: () => setCreateOpen(false),
    });
  };

  const handleUpdate = (data: RawMaterialUpdateData) => {
    if (!editMaterial) return;
    updateMutation.mutate(
      { id: editMaterial.id, data },
      { onSuccess: () => setEditMaterial(null) },
    );
  };

  const handleDelete = () => {
    if (!editMaterial) return;
    deleteMutation.mutate(editMaterial.id, {
      onSuccess: () => setEditMaterial(null),
    });
  };

  const handleReceive = (data: ReceiveDeliveryData) => {
    if (!receiveMaterial) return;
    receiveMutation.mutate(
      { id: receiveMaterial.id, data },
      { onSuccess: () => setReceiveMaterial(null) },
    );
  };

  const handleUse = (data: RecordUsageData) => {
    if (!useMaterial) return;
    usageMutation.mutate(
      { id: useMaterial.id, data },
      { onSuccess: () => setUseMaterial(null) },
    );
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 pt-[20px]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Materials</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{counts.red}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">{counts.amber}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Healthy</CardTitle>
            <Package className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{counts.green}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search + Filter + Add */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 gap-3">
          <Input
            placeholder="Search materials..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v === 'all' ? '' : v)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {MATERIAL_TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Material
        </Button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (
        <RawMaterialTable
          materials={materials || []}
          onReceive={setReceiveMaterial}
          onUse={setUseMaterial}
          onEdit={setEditMaterial}
        />
      )}

      {/* Create Dialog */}
      <CreateMaterialDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        isPending={createMutation.isPending}
        error={createMutation.error?.message}
      />

      {/* Edit Dialog */}
      <EditMaterialDialog
        material={editMaterial}
        open={!!editMaterial}
        onOpenChange={(open) => !open && setEditMaterial(null)}
        onSubmit={handleUpdate}
        onDelete={handleDelete}
        isPending={updateMutation.isPending}
        isDeleting={deleteMutation.isPending}
      />

      {/* Receive Dialog */}
      <ReceiveForm
        material={receiveMaterial}
        open={!!receiveMaterial}
        onOpenChange={(open) => !open && setReceiveMaterial(null)}
        onSubmit={handleReceive}
        isPending={receiveMutation.isPending}
      />

      {/* Usage Dialog */}
      <UsageForm
        material={useMaterial}
        open={!!useMaterial}
        onOpenChange={(open) => !open && setUseMaterial(null)}
        onSubmit={handleUse}
        isPending={usageMutation.isPending}
      />
    </div>
  );
}

// ── Create Dialog ────────────────────────────────────────────────────

function CreateMaterialDialog({
  open,
  onOpenChange,
  onSubmit,
  isPending,
  error,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: RawMaterialCreateData) => void;
  isPending: boolean;
  error?: string;
}) {
  const [form, setForm] = useState({
    material_code: '',
    material_name: '',
    material_type: 'resin',
    unit_of_measure: 'kg',
    red_threshold: '',
    amber_threshold: '',
    default_supplier: '',
    unit_cost: '',
    notes: '',
  });

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setForm({
        material_code: '',
        material_name: '',
        material_type: 'resin',
        unit_of_measure: 'kg',
        red_threshold: '',
        amber_threshold: '',
        default_supplier: '',
        unit_cost: '',
        notes: '',
      });
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: RawMaterialCreateData = {
      material_code: form.material_code,
      material_name: form.material_name,
      material_type: form.material_type,
      unit_of_measure: form.unit_of_measure,
    };
    if (form.red_threshold) data.red_threshold = Number(form.red_threshold);
    if (form.amber_threshold) data.amber_threshold = Number(form.amber_threshold);
    if (form.default_supplier) data.default_supplier = form.default_supplier;
    if (form.unit_cost) data.unit_cost = Number(form.unit_cost);
    if (form.notes) data.notes = form.notes;
    onSubmit(data);
  };

  const update = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Raw Material</DialogTitle>
          <DialogDescription>Create a new raw material for inventory tracking.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="create-code">Material Code</Label>
              <Input
                id="create-code"
                value={form.material_code}
                onChange={(e) => update('material_code', e.target.value)}
                placeholder="RM-HDPE-BLACK"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-name">Name</Label>
              <Input
                id="create-name"
                value={form.material_name}
                onChange={(e) => update('material_name', e.target.value)}
                placeholder="HDPE Resin - Black"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={form.material_type} onValueChange={(v) => update('material_type', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MATERIAL_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Unit of Measure</Label>
              <Select value={form.unit_of_measure} onValueChange={(v) => update('unit_of_measure', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {UNITS.map((u) => (
                    <SelectItem key={u} value={u}>
                      {u}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="create-red">Red Threshold</Label>
              <Input
                id="create-red"
                type="number"
                step="0.01"
                min="0"
                value={form.red_threshold}
                onChange={(e) => update('red_threshold', e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-amber">Amber Threshold</Label>
              <Input
                id="create-amber"
                type="number"
                step="0.01"
                min="0"
                value={form.amber_threshold}
                onChange={(e) => update('amber_threshold', e.target.value)}
                placeholder="0"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="create-supplier">Default Supplier</Label>
              <Input
                id="create-supplier"
                value={form.default_supplier}
                onChange={(e) => update('default_supplier', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-cost">Unit Cost ($)</Label>
              <Input
                id="create-cost"
                type="number"
                step="0.01"
                min="0"
                value={form.unit_cost}
                onChange={(e) => update('unit_cost', e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="create-notes">Notes</Label>
            <Textarea
              id="create-notes"
              value={form.notes}
              onChange={(e) => update('notes', e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !form.material_code || !form.material_name}>
              {isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Edit Dialog ──────────────────────────────────────────────────────

function EditMaterialDialog({
  material,
  open,
  onOpenChange,
  onSubmit,
  onDelete,
  isPending,
  isDeleting,
}: {
  material: RawMaterial | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: RawMaterialUpdateData) => void;
  onDelete: () => void;
  isPending: boolean;
  isDeleting: boolean;
}) {
  const [form, setForm] = useState({
    material_name: '',
    material_type: '',
    unit_of_measure: '',
    red_threshold: '',
    amber_threshold: '',
    default_supplier: '',
    unit_cost: '',
    notes: '',
  });

  const handleOpen = (isOpen: boolean) => {
    if (isOpen && material) {
      setForm({
        material_name: material.material_name,
        material_type: material.material_type,
        unit_of_measure: material.unit_of_measure,
        red_threshold: material.red_threshold,
        amber_threshold: material.amber_threshold,
        default_supplier: material.default_supplier || '',
        unit_cost: material.unit_cost || '',
        notes: material.notes || '',
      });
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: RawMaterialUpdateData = {
      material_name: form.material_name,
      material_type: form.material_type,
      unit_of_measure: form.unit_of_measure,
      red_threshold: Number(form.red_threshold),
      amber_threshold: Number(form.amber_threshold),
      default_supplier: form.default_supplier || undefined,
      unit_cost: form.unit_cost ? Number(form.unit_cost) : undefined,
      notes: form.notes || undefined,
    };
    onSubmit(data);
  };

  const update = (field: string, value: string) => setForm((prev) => ({ ...prev, [field]: value }));

  if (!material) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit {material.material_code}</DialogTitle>
          <DialogDescription>Update raw material details.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">Name</Label>
            <Input
              id="edit-name"
              value={form.material_name}
              onChange={(e) => update('material_name', e.target.value)}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={form.material_type} onValueChange={(v) => update('material_type', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MATERIAL_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Unit</Label>
              <Select value={form.unit_of_measure} onValueChange={(v) => update('unit_of_measure', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {UNITS.map((u) => (
                    <SelectItem key={u} value={u}>
                      {u}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-red">Red Threshold</Label>
              <Input
                id="edit-red"
                type="number"
                step="0.01"
                min="0"
                value={form.red_threshold}
                onChange={(e) => update('red_threshold', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-amber">Amber Threshold</Label>
              <Input
                id="edit-amber"
                type="number"
                step="0.01"
                min="0"
                value={form.amber_threshold}
                onChange={(e) => update('amber_threshold', e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-supplier">Default Supplier</Label>
              <Input
                id="edit-supplier"
                value={form.default_supplier}
                onChange={(e) => update('default_supplier', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-cost">Unit Cost ($)</Label>
              <Input
                id="edit-cost"
                type="number"
                step="0.01"
                min="0"
                value={form.unit_cost}
                onChange={(e) => update('unit_cost', e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-notes">Notes</Label>
            <Textarea
              id="edit-notes"
              value={form.notes}
              onChange={(e) => update('notes', e.target.value)}
            />
          </div>
          <DialogFooter className="flex justify-between sm:justify-between">
            <Button
              type="button"
              variant="destructive"
              onClick={onDelete}
              disabled={isDeleting}
            >
              {isDeleting ? 'Deactivating...' : 'Deactivate'}
            </Button>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
