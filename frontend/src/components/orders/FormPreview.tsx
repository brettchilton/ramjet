import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  fetchProductSpecs,
  calculateMaterials,
  getOfficeOrderUrl,
  getWorksOrderUrl,
} from '@/services/orderService';
import { Download, FileSpreadsheet } from 'lucide-react';
import type { OrderDetail, OrderLineItem } from '@/types/orders';

interface FormPreviewProps {
  order: OrderDetail;
}

export function FormPreview({ order }: FormPreviewProps) {
  const isApproved = order.status === 'approved';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Form Preview</h3>
        {isApproved && order.has_office_order && (
          <Button variant="outline" size="sm" asChild>
            <a
              href={getOfficeOrderUrl(order.id)}
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Download Office Order
            </a>
          </Button>
        )}
      </div>

      <Tabs defaultValue="office-order">
        <TabsList className="w-full justify-start flex-wrap h-auto gap-1">
          <TabsTrigger value="office-order" className="gap-1.5">
            <FileSpreadsheet className="h-3.5 w-3.5" />
            Office Order
          </TabsTrigger>
          {order.line_items.map((item) => (
            <TabsTrigger
              key={item.id}
              value={`wo-${item.id}`}
              className="gap-1.5"
            >
              WO: {item.product_code || `Line ${item.line_number}`}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="office-order" className="mt-4">
          <OfficeOrderPreview order={order} />
        </TabsContent>

        {order.line_items.map((item) => (
          <TabsContent key={item.id} value={`wo-${item.id}`} className="mt-4">
            <WorksOrderPreview
              order={order}
              lineItem={item}
              isApproved={isApproved}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

function OfficeOrderPreview({ order }: { order: OrderDetail }) {
  const grandTotal = order.line_items.reduce(
    (sum, item) => sum + (Number(item.line_total) || 0),
    0
  );

  return (
    <div className="rounded-md border overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-muted/50">
            <th colSpan={7} className="p-3 text-left text-base font-bold border-b">
              Office Order
            </th>
          </tr>
        </thead>
        <tbody>
          {/* Header info */}
          <tr className="border-b">
            <td className="p-2 font-medium text-muted-foreground" colSpan={2}>
              Customer
            </td>
            <td className="p-2" colSpan={5}>
              {order.customer_name || '—'}
            </td>
          </tr>
          <tr className="border-b">
            <td className="p-2 font-medium text-muted-foreground" colSpan={2}>
              PO Number
            </td>
            <td className="p-2" colSpan={2}>
              {order.po_number || '—'}
            </td>
            <td className="p-2 font-medium text-muted-foreground">PO Date</td>
            <td className="p-2" colSpan={2}>
              {order.po_date || '—'}
            </td>
          </tr>
          <tr className="border-b">
            <td className="p-2 font-medium text-muted-foreground" colSpan={2}>
              Delivery Date
            </td>
            <td className="p-2" colSpan={5}>
              {order.delivery_date || '—'}
            </td>
          </tr>
          {order.special_instructions && (
            <tr className="border-b">
              <td className="p-2 font-medium text-muted-foreground" colSpan={2}>
                Special Instructions
              </td>
              <td className="p-2" colSpan={5}>
                {order.special_instructions}
              </td>
            </tr>
          )}

          {/* Line items header */}
          <tr className="bg-muted/30 border-b">
            <th className="p-2 text-left">#</th>
            <th className="p-2 text-left">Product Code</th>
            <th className="p-2 text-left">Description</th>
            <th className="p-2 text-left">Colour</th>
            <th className="p-2 text-right">Qty</th>
            <th className="p-2 text-right">Unit Price</th>
            <th className="p-2 text-right">Line Total</th>
          </tr>

          {/* Line items */}
          {order.line_items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="p-2">{item.line_number}</td>
              <td className="p-2">{item.product_code || '—'}</td>
              <td className="p-2">{item.product_description || '—'}</td>
              <td className="p-2">{item.colour || '—'}</td>
              <td className="p-2 text-right">{item.quantity}</td>
              <td className="p-2 text-right">
                {item.unit_price ? `$${Number(item.unit_price).toFixed(2)}` : '—'}
              </td>
              <td className="p-2 text-right font-medium">
                {item.line_total ? `$${Number(item.line_total).toFixed(2)}` : '—'}
              </td>
            </tr>
          ))}

          {/* Grand total */}
          <tr className="bg-muted/30 font-bold">
            <td colSpan={6} className="p-2 text-right">
              Grand Total
            </td>
            <td className="p-2 text-right">${grandTotal.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function WorksOrderPreview({
  order,
  lineItem,
  isApproved,
}: {
  order: OrderDetail;
  lineItem: OrderLineItem;
  isApproved: boolean;
}) {
  const productCode = lineItem.matched_product_code || lineItem.product_code;
  const hasProduct = !!lineItem.matched_product_code;

  const { data: productSpecs, isLoading: specsLoading } = useQuery({
    queryKey: ['productSpecs', productCode],
    queryFn: () => fetchProductSpecs(productCode!),
    enabled: hasProduct,
  });

  const { data: calculation, isLoading: calcLoading } = useQuery({
    queryKey: [
      'calculation',
      productCode,
      lineItem.colour,
      lineItem.quantity,
    ],
    queryFn: () =>
      calculateMaterials(productCode!, lineItem.colour!, lineItem.quantity),
    enabled: hasProduct && !!lineItem.colour,
  });

  const isLoading = specsLoading || calcLoading;

  // Find matching material spec for this colour
  const materialSpec = productSpecs?.materials?.find(
    (m) => m.colour?.toLowerCase() === lineItem.colour?.toLowerCase()
  );

  return (
    <div className="space-y-4">
      {isApproved && (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" asChild>
            <a
              href={getWorksOrderUrl(order.id, lineItem.id)}
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Download Works Order
            </a>
          </Button>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : !hasProduct ? (
        <div className="rounded-md border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800 p-4 text-sm text-amber-800 dark:text-amber-400">
          Product not matched — specifications unavailable. The product code "
          {lineItem.product_code}" could not be matched to a product in the
          catalog.
        </div>
      ) : (
        <div className="rounded-md border overflow-hidden">
          <table className="w-full text-sm">
            <tbody>
              {/* Order Details */}
              <SectionHeader>Order Details</SectionHeader>
              <KvRow label="Customer" value={order.customer_name} />
              <KvRow label="PO Number" value={order.po_number} />
              <KvRow label="Product Code" value={productCode} />
              <KvRow label="Description" value={lineItem.product_description} />
              <KvRow label="Colour" value={lineItem.colour} />
              <KvRow label="Quantity" value={String(lineItem.quantity)} />
              <KvRow
                label="Delivery Date"
                value={order.delivery_date}
              />

              {/* Manufacturing Specs */}
              {productSpecs?.manufacturing && (
                <>
                  <SectionHeader>Manufacturing Specs</SectionHeader>
                  <KvRow
                    label="Mould No."
                    value={productSpecs.manufacturing.mould_no}
                  />
                  <KvRow
                    label="Cycle Time"
                    value={
                      productSpecs.manufacturing.cycle_time_seconds
                        ? `${productSpecs.manufacturing.cycle_time_seconds}s`
                        : undefined
                    }
                  />
                  <KvRow
                    label="Shot Weight"
                    value={
                      productSpecs.manufacturing.shot_weight_grams
                        ? `${productSpecs.manufacturing.shot_weight_grams}g`
                        : undefined
                    }
                  />
                  <KvRow
                    label="Cavities"
                    value={
                      productSpecs.manufacturing.num_cavities
                        ? String(productSpecs.manufacturing.num_cavities)
                        : undefined
                    }
                  />
                  <KvRow
                    label="Product Weight"
                    value={
                      productSpecs.manufacturing.product_weight_grams
                        ? `${productSpecs.manufacturing.product_weight_grams}g`
                        : undefined
                    }
                  />
                  <KvRow
                    label="Est. Running Time"
                    value={
                      productSpecs.manufacturing.estimated_running_time_hours
                        ? `${productSpecs.manufacturing.estimated_running_time_hours}hrs`
                        : undefined
                    }
                  />
                  <KvRow
                    label="Machine Min. Req."
                    value={productSpecs.manufacturing.machine_min_requirements}
                  />
                </>
              )}

              {/* Material Specs */}
              {materialSpec && (
                <>
                  <SectionHeader>Material Specs</SectionHeader>
                  <KvRow label="Material Grade" value={materialSpec.material_grade} />
                  <KvRow label="Material Type" value={materialSpec.material_type} />
                  <KvRow label="Colour No." value={materialSpec.colour_no} />
                  <KvRow
                    label="Colour Supplier"
                    value={materialSpec.colour_supplier}
                  />
                  <KvRow
                    label="MB Add Rate"
                    value={
                      materialSpec.mb_add_rate
                        ? `${materialSpec.mb_add_rate}%`
                        : undefined
                    }
                  />
                  <KvRow label="Additive" value={materialSpec.additive} />
                  <KvRow
                    label="Additive Add Rate"
                    value={
                      materialSpec.additive_add_rate
                        ? `${materialSpec.additive_add_rate}%`
                        : undefined
                    }
                  />
                  <KvRow
                    label="Additive Supplier"
                    value={materialSpec.additive_supplier}
                  />
                </>
              )}

              {/* Material Requirements */}
              {calculation && (
                <>
                  <SectionHeader>Material Requirements</SectionHeader>
                  <KvRow
                    label="Base Material"
                    value={`${calculation.material_requirements.base_material_kg.toFixed(2)} kg`}
                  />
                  <KvRow
                    label="Masterbatch"
                    value={`${calculation.material_requirements.masterbatch_kg.toFixed(2)} kg`}
                  />
                  <KvRow
                    label="Additive"
                    value={`${calculation.material_requirements.additive_kg.toFixed(2)} kg`}
                  />
                  <KvRow
                    label="Total Material"
                    value={`${calculation.material_requirements.total_material_kg.toFixed(2)} kg`}
                  />
                </>
              )}

              {/* Packaging */}
              {productSpecs?.packaging && (
                <>
                  <SectionHeader>Packaging</SectionHeader>
                  <KvRow
                    label="Qty per Bag"
                    value={
                      productSpecs.packaging.qty_per_bag
                        ? String(productSpecs.packaging.qty_per_bag)
                        : undefined
                    }
                  />
                  <KvRow label="Bag Size" value={productSpecs.packaging.bag_size} />
                  <KvRow
                    label="Qty per Carton"
                    value={
                      productSpecs.packaging.qty_per_carton
                        ? String(productSpecs.packaging.qty_per_carton)
                        : undefined
                    }
                  />
                  <KvRow
                    label="Carton Size"
                    value={productSpecs.packaging.carton_size}
                  />
                  <KvRow
                    label="Cartons per Pallet"
                    value={
                      productSpecs.packaging.cartons_per_pallet
                        ? String(productSpecs.packaging.cartons_per_pallet)
                        : undefined
                    }
                  />
                  <KvRow
                    label="Cartons per Layer"
                    value={
                      productSpecs.packaging.cartons_per_layer
                        ? String(productSpecs.packaging.cartons_per_layer)
                        : undefined
                    }
                  />
                </>
              )}

              {/* Packaging Requirements */}
              {calculation && (
                <>
                  <SectionHeader>Packaging Requirements</SectionHeader>
                  <KvRow
                    label="Bags Needed"
                    value={String(calculation.packaging_requirements.bags_needed)}
                  />
                  <KvRow
                    label="Bag Size"
                    value={calculation.packaging_requirements.bag_size}
                  />
                  <KvRow
                    label="Cartons Needed"
                    value={String(calculation.packaging_requirements.cartons_needed)}
                  />
                  <KvRow
                    label="Carton Size"
                    value={calculation.packaging_requirements.carton_size}
                  />
                </>
              )}

              {/* Notes */}
              {order.special_instructions && (
                <>
                  <SectionHeader>Notes</SectionHeader>
                  <tr className="border-b">
                    <td className="p-2" colSpan={2}>
                      {order.special_instructions}
                    </td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <tr className="bg-muted/50">
      <td colSpan={2} className="p-2 font-semibold text-sm">
        {children}
      </td>
    </tr>
  );
}

function KvRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <tr className="border-b">
      <td className="p-2 font-medium text-muted-foreground w-1/3">{label}</td>
      <td className="p-2">{value || '—'}</td>
    </tr>
  );
}
