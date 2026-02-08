import { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ConfidenceBadge } from '@/components/orders/ConfidenceBadge';
import { cn } from '@/lib/utils';

function formatCurrency(value: number | string | null | undefined): string {
  if (value == null) return '—';
  const num = typeof value === 'string' ? Number(value) : value;
  if (isNaN(num)) return '—';
  return `$${num.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
import { AlertCircle } from 'lucide-react';
import type { OrderDetail } from '@/types/orders';

interface OrderDataFormProps {
  order: OrderDetail;
  isEditing: boolean;
  onSave: (headerData: HeaderFormValues, lineItems: LineItemFormValues[]) => void;
}

interface HeaderFormValues {
  customer_name: string;
  po_number: string;
  po_date: string;
  delivery_date: string;
  special_instructions: string;
}

interface LineItemFormValues {
  id: string;
  line_number: number;
  product_code: string;
  product_description: string;
  colour: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  confidence?: string;
  needs_review: boolean;
}

export function OrderDataForm({ order, isEditing, onSave }: OrderDataFormProps) {
  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
  } = useForm<{
    header: HeaderFormValues;
    line_items: LineItemFormValues[];
  }>({
    defaultValues: getDefaults(order),
  });

  const { fields } = useFieldArray({ control, name: 'line_items' });
  const watchedLineItems = watch('line_items');

  // Reset form when order data changes (skip while editing to prevent flash)
  useEffect(() => {
    if (!isEditing) {
      reset(getDefaults(order));
    }
  }, [order, reset, isEditing]);

  // Auto-calc line totals when qty or price changes
  useEffect(() => {
    watchedLineItems?.forEach((item, index) => {
      const qty = Number(item.quantity) || 0;
      const price = Number(item.unit_price) || 0;
      const newTotal = parseFloat((qty * price).toFixed(2));
      if (item.line_total !== newTotal) {
        setValue(`line_items.${index}.line_total`, newTotal);
      }
    });
  }, [watchedLineItems, setValue]);

  const onSubmit = (data: { header: HeaderFormValues; line_items: LineItemFormValues[] }) => {
    onSave(data.header, data.line_items);
  };

  // Get field-level confidence from raw JSON
  const rawJson = order.extraction_raw_json as Record<string, unknown> | undefined;
  const fieldConfidence = (rawJson?.field_confidences ?? {}) as Record<string, number>;

  return (
    <form id="order-data-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header Fields */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          label="Customer Name"
          confidence={fieldConfidence['customer_name']}
          isEditing={isEditing}
          displayValue={order.customer_name || '—'}
        >
          <Input {...register('header.customer_name')} disabled={!isEditing} />
        </FormField>

        <FormField
          label="PO Number"
          confidence={fieldConfidence['po_number']}
          isEditing={isEditing}
          displayValue={order.po_number || '—'}
        >
          <Input {...register('header.po_number')} disabled={!isEditing} />
        </FormField>

        <FormField
          label="PO Date"
          confidence={fieldConfidence['po_date']}
          isEditing={isEditing}
          displayValue={order.po_date || '—'}
        >
          <Input type="date" {...register('header.po_date')} disabled={!isEditing} />
        </FormField>

        <FormField
          label="Delivery Date"
          confidence={fieldConfidence['delivery_date']}
          isEditing={isEditing}
          displayValue={order.delivery_date || '—'}
        >
          <Input type="date" {...register('header.delivery_date')} disabled={!isEditing} />
        </FormField>

        <div className="sm:col-span-2">
          <FormField
            label="Special Instructions"
            confidence={fieldConfidence['special_instructions']}
            isEditing={isEditing}
            displayValue={order.special_instructions || '—'}
          >
            <Textarea
              {...register('header.special_instructions')}
              disabled={!isEditing}
              rows={3}
            />
          </FormField>
        </div>
      </div>

      {/* Line Items Table */}
      <div>
        <h3 className="text-sm font-semibold mb-3">Line Items</h3>
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">#</TableHead>
                <TableHead>Product Code</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Colour</TableHead>
                <TableHead className="w-24 text-right">Qty</TableHead>
                <TableHead className="w-28 text-right">Unit Price</TableHead>
                <TableHead className="w-28 text-right">Line Total</TableHead>
                <TableHead className="w-16 text-center">Conf.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fields.map((field, index) => {
                const item = watchedLineItems?.[index];
                return (
                  <TableRow
                    key={field.id}
                    className={cn(item?.needs_review && 'bg-amber-50/50 dark:bg-amber-950/20')}
                  >
                    <TableCell className="text-muted-foreground">
                      <div className="flex items-center gap-1">
                        {item?.needs_review && (
                          <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
                        )}
                        {field.line_number}
                      </div>
                    </TableCell>
                    <TableCell>
                      {isEditing ? (
                        <Input
                          {...register(`line_items.${index}.product_code`)}
                          className="h-8"
                        />
                      ) : (
                        <span className="text-sm">{item?.product_code || '—'}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {isEditing ? (
                        <Input
                          {...register(`line_items.${index}.product_description`)}
                          className="h-8"
                        />
                      ) : (
                        <span className="text-sm">
                          {item?.product_description || '—'}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {isEditing ? (
                        <Input
                          {...register(`line_items.${index}.colour`)}
                          className="h-8"
                        />
                      ) : (
                        <span className="text-sm">{item?.colour || '—'}</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {isEditing ? (
                        <Input
                          type="number"
                          {...register(`line_items.${index}.quantity`, {
                            valueAsNumber: true,
                          })}
                          className="h-8 text-right"
                        />
                      ) : (
                        <span className="text-sm">{item?.quantity}</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {isEditing ? (
                        <Input
                          type="number"
                          step="0.01"
                          {...register(`line_items.${index}.unit_price`, {
                            valueAsNumber: true,
                          })}
                          className="h-8 text-right"
                        />
                      ) : (
                        <span className="text-sm">
                          {formatCurrency(item?.unit_price)}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(item?.line_total)}
                    </TableCell>
                    <TableCell className="text-center">
                      <ConfidenceBadge confidence={item?.confidence} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        {/* Totals */}
        {watchedLineItems && watchedLineItems.length > 0 && (() => {
          const subtotal = watchedLineItems.reduce((sum, item) => sum + (Number(item.line_total) || 0), 0);
          const gst = subtotal * 0.1;
          const total = subtotal + gst;
          return (
            <div className="flex flex-col items-end mt-2 pr-20 gap-1">
              <div className="flex gap-4">
                <span className="text-sm font-medium text-muted-foreground">Subtotal:</span>
                <span className="text-sm font-medium">{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-sm font-medium text-muted-foreground">GST (10%):</span>
                <span className="text-sm font-medium">{formatCurrency(gst)}</span>
              </div>
              <div className="flex gap-4">
                <span className="text-sm font-medium text-muted-foreground">Total (inc. GST):</span>
                <span className="text-sm font-bold">{formatCurrency(total)}</span>
              </div>
            </div>
          );
        })()}
      </div>
    </form>
  );
}

// Helper: read-only vs editable field wrapper
function FormField({
  label,
  confidence,
  isEditing,
  displayValue,
  children,
}: {
  label: string;
  confidence?: number;
  isEditing: boolean;
  displayValue: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <Label className="text-sm">{label}</Label>
        {confidence !== undefined && <ConfidenceBadge confidence={confidence} />}
      </div>
      {isEditing ? children : <p className="text-sm py-2">{displayValue}</p>}
    </div>
  );
}

function getDefaults(order: OrderDetail) {
  return {
    header: {
      customer_name: order.customer_name || '',
      po_number: order.po_number || '',
      po_date: order.po_date || '',
      delivery_date: order.delivery_date || '',
      special_instructions: order.special_instructions || '',
    },
    line_items: order.line_items.map((item) => ({
      id: item.id,
      line_number: item.line_number,
      product_code: item.product_code || '',
      product_description: item.product_description || '',
      colour: item.colour || '',
      quantity: item.quantity,
      unit_price: item.unit_price ? Number(item.unit_price) : 0,
      line_total: item.line_total ? Number(item.line_total) : 0,
      confidence: item.confidence,
      needs_review: item.needs_review,
    })),
  };
}
