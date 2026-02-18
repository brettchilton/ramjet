import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useProducts, useCreateProduct, useUpdateProduct, useDeleteProduct } from '@/hooks/useProducts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Plus, Package, Pencil } from 'lucide-react';
import type { ProductListItem, ProductCreateData, ProductUpdateData } from '@/types/products';

export const Route = createFileRoute('/products/')({
  component: ProductsPage,
});

function ProductsPage() {
  return (
    <AuthGuard>
      <ProductsContent />
    </AuthGuard>
  );
}

function ProductsContent() {
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editProduct, setEditProduct] = useState<ProductListItem | null>(null);

  const { data: products, isLoading } = useProducts(search || undefined);

  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();

  const counts = {
    total: products?.length || 0,
    active: products?.filter((p) => p.is_active).length || 0,
    stockable: products?.filter((p) => p.is_stockable).length || 0,
  };

  const handleCreate = (data: ProductCreateData) => {
    createMutation.mutate(data, {
      onSuccess: () => setCreateOpen(false),
    });
  };

  const handleUpdate = (data: ProductUpdateData) => {
    if (!editProduct) return;
    updateMutation.mutate(
      { code: editProduct.product_code, data },
      { onSuccess: () => setEditProduct(null) },
    );
  };

  const handleDelete = () => {
    if (!editProduct) return;
    deleteMutation.mutate(editProduct.product_code, {
      onSuccess: () => setEditProduct(null),
    });
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 pt-[20px]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{counts.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Package className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{counts.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stockable</CardTitle>
            <Package className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">{counts.stockable}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search + Add */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Input
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Product
        </Button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !products || products.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <Package className="h-12 w-12 mb-4" />
          <p className="text-lg font-medium">No products found</p>
          <p className="text-sm">Add products to start managing your catalog</p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Stockable</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.map((product) => (
                <TableRow key={product.product_code}>
                  <TableCell className="font-mono text-sm">{product.product_code}</TableCell>
                  <TableCell className="font-medium">{product.product_description}</TableCell>
                  <TableCell className="text-muted-foreground">{product.customer_name || '—'}</TableCell>
                  <TableCell>
                    <Badge variant={product.is_active ? 'default' : 'secondary'}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={product.is_stockable ? 'outline' : 'secondary'}>
                      {product.is_stockable ? 'Yes' : 'No'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditProduct(product)}
                      title="Edit"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Create Dialog */}
      <CreateProductDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={handleCreate}
        isPending={createMutation.isPending}
        error={createMutation.error?.message}
      />

      {/* Edit Dialog */}
      <EditProductDialog
        product={editProduct}
        open={!!editProduct}
        onOpenChange={(open) => !open && setEditProduct(null)}
        onSubmit={handleUpdate}
        onDelete={handleDelete}
        isPending={updateMutation.isPending}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}

// ── Create Dialog ────────────────────────────────────────────────────

function CreateProductDialog({
  open,
  onOpenChange,
  onSubmit,
  isPending,
  error,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProductCreateData) => void;
  isPending: boolean;
  error?: string;
}) {
  const [form, setForm] = useState({
    product_code: '',
    product_description: '',
    customer_name: '',
    is_stockable: true,
  });

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setForm({
        product_code: '',
        product_description: '',
        customer_name: '',
        is_stockable: true,
      });
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: ProductCreateData = {
      product_code: form.product_code,
      product_description: form.product_description,
      is_stockable: form.is_stockable,
    };
    if (form.customer_name) data.customer_name = form.customer_name;
    onSubmit(data);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Product</DialogTitle>
          <DialogDescription>Create a new product in the catalog.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="create-code">Product Code</Label>
              <Input
                id="create-code"
                value={form.product_code}
                onChange={(e) => setForm((prev) => ({ ...prev, product_code: e.target.value }))}
                placeholder="PROD-001"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-desc">Description</Label>
              <Input
                id="create-desc"
                value={form.product_description}
                onChange={(e) => setForm((prev) => ({ ...prev, product_description: e.target.value }))}
                placeholder="Product description"
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="create-customer">Customer Name</Label>
            <Input
              id="create-customer"
              value={form.customer_name}
              onChange={(e) => setForm((prev) => ({ ...prev, customer_name: e.target.value }))}
              placeholder="Optional"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="create-stockable"
              checked={form.is_stockable}
              onCheckedChange={(checked) => setForm((prev) => ({ ...prev, is_stockable: checked }))}
            />
            <Label htmlFor="create-stockable">Stockable product</Label>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || !form.product_code || !form.product_description}>
              {isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Edit Dialog ──────────────────────────────────────────────────────

function EditProductDialog({
  product,
  open,
  onOpenChange,
  onSubmit,
  onDelete,
  isPending,
  isDeleting,
}: {
  product: ProductListItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProductUpdateData) => void;
  onDelete: () => void;
  isPending: boolean;
  isDeleting: boolean;
}) {
  const [form, setForm] = useState({
    product_description: '',
    customer_name: '',
    is_active: true,
    is_stockable: true,
  });

  const handleOpen = (isOpen: boolean) => {
    if (isOpen && product) {
      setForm({
        product_description: product.product_description,
        customer_name: product.customer_name || '',
        is_active: product.is_active,
        is_stockable: product.is_stockable,
      });
    }
    onOpenChange(isOpen);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: ProductUpdateData = {
      product_description: form.product_description,
      customer_name: form.customer_name || undefined,
      is_active: form.is_active,
      is_stockable: form.is_stockable,
    };
    onSubmit(data);
  };

  if (!product) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit {product.product_code}</DialogTitle>
          <DialogDescription>Update product details.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-desc">Description</Label>
            <Input
              id="edit-desc"
              value={form.product_description}
              onChange={(e) => setForm((prev) => ({ ...prev, product_description: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-customer">Customer Name</Label>
            <Input
              id="edit-customer"
              value={form.customer_name}
              onChange={(e) => setForm((prev) => ({ ...prev, customer_name: e.target.value }))}
            />
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="edit-active"
                checked={form.is_active}
                onCheckedChange={(checked) => setForm((prev) => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="edit-active">Active</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="edit-stockable"
                checked={form.is_stockable}
                onCheckedChange={(checked) => setForm((prev) => ({ ...prev, is_stockable: checked }))}
              />
              <Label htmlFor="edit-stockable">Stockable</Label>
            </div>
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
