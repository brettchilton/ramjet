import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Trash2, Save, Plus } from 'lucide-react';
import {
  useThresholds,
  useCreateThreshold,
  useUpdateThreshold,
  useDeleteThreshold,
  useStockableProducts,
} from '@/hooks/useStock';
import type { StockThreshold } from '@/types/stock';

export function ThresholdEditor() {
  const { data: thresholds, isLoading } = useThresholds();
  const { data: products } = useStockableProducts();
  const createMutation = useCreateThreshold();
  const updateMutation = useUpdateThreshold();
  const deleteMutation = useDeleteThreshold();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState({ red: 0, amber: 0 });
  const [showAdd, setShowAdd] = useState(false);
  const [newThreshold, setNewThreshold] = useState({
    product_code: '',
    colour: '',
    red_threshold: 0,
    amber_threshold: 0,
  });

  const startEdit = (t: StockThreshold) => {
    setEditingId(t.id);
    setEditValues({ red: t.red_threshold, amber: t.amber_threshold });
  };

  const saveEdit = (id: string) => {
    updateMutation.mutate(
      { id, data: { red_threshold: editValues.red, amber_threshold: editValues.amber } },
      { onSuccess: () => setEditingId(null) },
    );
  };

  const handleCreate = () => {
    if (!newThreshold.product_code) return;
    createMutation.mutate(
      {
        product_code: newThreshold.product_code,
        colour: newThreshold.colour || undefined,
        red_threshold: newThreshold.red_threshold,
        amber_threshold: newThreshold.amber_threshold,
      },
      {
        onSuccess: () => {
          setShowAdd(false);
          setNewThreshold({ product_code: '', colour: '', red_threshold: 0, amber_threshold: 0 });
        },
      },
    );
  };

  if (isLoading) return <div className="text-sm text-muted-foreground">Loading thresholds...</div>;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Product</TableHead>
            <TableHead>Colour</TableHead>
            <TableHead className="text-right">Red (Critical)</TableHead>
            <TableHead className="text-right">Amber (Warning)</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {thresholds?.map((t) => (
            <TableRow key={t.id}>
              <TableCell className="font-medium">{t.product_code}</TableCell>
              <TableCell>{t.colour || 'All colours'}</TableCell>
              <TableCell className="text-right">
                {editingId === t.id ? (
                  <Input
                    type="number"
                    className="w-24 ml-auto text-right"
                    value={editValues.red}
                    onChange={(e) => setEditValues({ ...editValues, red: Number(e.target.value) })}
                  />
                ) : (
                  t.red_threshold.toLocaleString()
                )}
              </TableCell>
              <TableCell className="text-right">
                {editingId === t.id ? (
                  <Input
                    type="number"
                    className="w-24 ml-auto text-right"
                    value={editValues.amber}
                    onChange={(e) => setEditValues({ ...editValues, amber: Number(e.target.value) })}
                  />
                ) : (
                  t.amber_threshold.toLocaleString()
                )}
              </TableCell>
              <TableCell>
                <div className="flex gap-1">
                  {editingId === t.id ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => saveEdit(t.id)}
                      disabled={updateMutation.isPending}
                    >
                      <Save className="h-4 w-4" />
                    </Button>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => startEdit(t)}>
                      Edit
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-destructive hover:text-destructive"
                    onClick={() => deleteMutation.mutate(t.id)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}

          {/* Add new row */}
          {showAdd && (
            <TableRow>
              <TableCell>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={newThreshold.product_code}
                  onChange={(e) => setNewThreshold({ ...newThreshold, product_code: e.target.value })}
                >
                  <option value="">Select product...</option>
                  {products?.map((p) => (
                    <option key={p.product_code} value={p.product_code}>
                      {p.product_code} — {p.product_description}
                    </option>
                  ))}
                </select>
              </TableCell>
              <TableCell>
                <Input
                  placeholder="Colour (blank = all)"
                  value={newThreshold.colour}
                  onChange={(e) => setNewThreshold({ ...newThreshold, colour: e.target.value })}
                />
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  className="w-24 ml-auto text-right"
                  value={newThreshold.red_threshold}
                  onChange={(e) => setNewThreshold({ ...newThreshold, red_threshold: Number(e.target.value) })}
                />
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  className="w-24 ml-auto text-right"
                  value={newThreshold.amber_threshold}
                  onChange={(e) => setNewThreshold({ ...newThreshold, amber_threshold: Number(e.target.value) })}
                />
              </TableCell>
              <TableCell>
                <Button
                  size="sm"
                  onClick={handleCreate}
                  disabled={createMutation.isPending || !newThreshold.product_code}
                >
                  <Save className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {!showAdd && (
        <Button variant="outline" size="sm" onClick={() => setShowAdd(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add threshold
        </Button>
      )}
    </div>
  );
}
