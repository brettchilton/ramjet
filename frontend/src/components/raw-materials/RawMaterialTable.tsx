import { useNavigate } from '@tanstack/react-router';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Package, ArrowDownToLine, ArrowUpFromLine, Pencil } from 'lucide-react';
import type { RawMaterial } from '@/types/rawMaterials';

interface RawMaterialTableProps {
  materials: RawMaterial[];
  onReceive: (material: RawMaterial) => void;
  onUse: (material: RawMaterial) => void;
  onEdit: (material: RawMaterial) => void;
}

const statusColors: Record<string, string> = {
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
};

const typeBadgeVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  resin: 'default',
  masterbatch: 'secondary',
  additive: 'outline',
  packaging: 'secondary',
  other: 'outline',
};

export function RawMaterialTable({ materials, onReceive, onUse, onEdit }: RawMaterialTableProps) {
  const navigate = useNavigate();

  if (materials.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <Package className="h-12 w-12 mb-4" />
        <p className="text-lg font-medium">No raw materials found</p>
        <p className="text-sm">Add materials to start tracking inventory</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Code</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Stock</TableHead>
            <TableHead>Unit</TableHead>
            <TableHead>Supplier</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {materials.map((material) => (
            <TableRow
              key={material.id}
              className="cursor-pointer"
              onClick={() =>
                navigate({
                  to: '/raw-materials/$materialId',
                  params: { materialId: material.id },
                })
              }
            >
              <TableCell>
                <span
                  className={`inline-block h-3 w-3 rounded-full ${statusColors[material.threshold_status] || 'bg-gray-400'}`}
                  title={`${material.threshold_status} — Stock: ${material.current_stock}`}
                />
              </TableCell>
              <TableCell className="font-mono text-sm">{material.material_code}</TableCell>
              <TableCell className="font-medium">{material.material_name}</TableCell>
              <TableCell>
                <Badge variant={typeBadgeVariant[material.material_type] || 'outline'}>
                  {material.material_type}
                </Badge>
              </TableCell>
              <TableCell className="text-right font-mono">
                {Number(material.current_stock).toLocaleString()}
              </TableCell>
              <TableCell className="text-muted-foreground">{material.unit_of_measure}</TableCell>
              <TableCell className="text-muted-foreground">
                {material.default_supplier || '—'}
              </TableCell>
              <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onReceive(material)}
                    title="Receive delivery"
                  >
                    <ArrowDownToLine className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onUse(material)}
                    title="Record usage"
                  >
                    <ArrowUpFromLine className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(material)}
                    title="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
