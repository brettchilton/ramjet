import { useState, useEffect } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { AuthGuard } from '@/components/AuthGuard';
import { useStockableProducts, useProductDetail, useGenerateLabels } from '@/hooks/useStock';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Printer, Loader2 } from 'lucide-react';

export const Route = createFileRoute('/stock/labels')({
  component: LabelsPage,
});

function LabelsPage() {
  return (
    <AuthGuard>
      <LabelsContent />
    </AuthGuard>
  );
}

function LabelsContent() {
  const { data: products, isLoading: productsLoading } = useStockableProducts();
  const generateLabels = useGenerateLabels();

  const [productCode, setProductCode] = useState('');
  const [colour, setColour] = useState('');
  const [quantityPerCarton, setQuantityPerCarton] = useState('');
  const [numberOfLabels, setNumberOfLabels] = useState('20');
  const [boxType, setBoxType] = useState<'full' | 'partial'>('full');
  const [productionDate, setProductionDate] = useState(
    new Date().toISOString().split('T')[0]
  );

  const { data: productDetail } = useProductDetail(productCode);

  // Available colours from product material specs
  const availableColours = productDetail?.materials?.map((m) => m.colour) ?? [];

  // Auto-fill quantity from packaging spec when product changes
  useEffect(() => {
    if (productDetail?.packaging?.qty_per_carton) {
      setQuantityPerCarton(String(productDetail.packaging.qty_per_carton));
    }
  }, [productDetail]);

  // Reset colour when product changes
  useEffect(() => {
    setColour('');
  }, [productCode]);

  const canSubmit =
    productCode &&
    colour &&
    Number(quantityPerCarton) > 0 &&
    Number(numberOfLabels) > 0 &&
    !generateLabels.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    generateLabels.mutate({
      product_code: productCode,
      colour,
      quantity_per_carton: Number(quantityPerCarton),
      number_of_labels: Number(numberOfLabels),
      box_type: boxType,
      production_date: productionDate,
    });
  };

  return (
    <div className="container max-w-2xl mx-auto py-8 px-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl flex items-center gap-2">
            <Printer className="h-6 w-6" />
            Generate Labels
          </CardTitle>
          <CardDescription>
            Generate QR code labels for stock cartons. Labels will download as a
            printable A4 PDF.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Product Select */}
            <div className="space-y-2">
              <Label htmlFor="product" className="text-base">
                Product
              </Label>
              <Select value={productCode} onValueChange={setProductCode}>
                <SelectTrigger id="product" className="w-full h-12 text-base">
                  <SelectValue placeholder="Select a product..." />
                </SelectTrigger>
                <SelectContent>
                  {productsLoading ? (
                    <SelectItem value="_loading" disabled>
                      Loading products...
                    </SelectItem>
                  ) : (
                    products?.map((p) => (
                      <SelectItem key={p.product_code} value={p.product_code}>
                        {p.product_code} — {p.product_description}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Colour Select */}
            <div className="space-y-2">
              <Label htmlFor="colour" className="text-base">
                Colour
              </Label>
              <Select
                value={colour}
                onValueChange={setColour}
                disabled={!productCode || availableColours.length === 0}
              >
                <SelectTrigger id="colour" className="w-full h-12 text-base">
                  <SelectValue
                    placeholder={
                      !productCode
                        ? 'Select a product first'
                        : availableColours.length === 0
                          ? 'No colours available'
                          : 'Select a colour...'
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {availableColours.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Quantity per carton */}
            <div className="space-y-2">
              <Label htmlFor="quantity" className="text-base">
                Quantity per carton
              </Label>
              <Input
                id="quantity"
                type="number"
                min={1}
                value={quantityPerCarton}
                onChange={(e) => setQuantityPerCarton(e.target.value)}
                placeholder="e.g. 500"
                className="h-12 text-base"
              />
            </div>

            {/* Number of labels */}
            <div className="space-y-2">
              <Label htmlFor="labelCount" className="text-base">
                Number of labels
              </Label>
              <Input
                id="labelCount"
                type="number"
                min={1}
                max={200}
                value={numberOfLabels}
                onChange={(e) => setNumberOfLabels(e.target.value)}
                placeholder="e.g. 20"
                className="h-12 text-base"
              />
            </div>

            {/* Box type */}
            <div className="space-y-2">
              <Label className="text-base">Box type</Label>
              <div className="flex gap-6">
                <label className="flex items-center gap-2 cursor-pointer text-base">
                  <input
                    type="radio"
                    name="boxType"
                    value="full"
                    checked={boxType === 'full'}
                    onChange={() => setBoxType('full')}
                    className="w-5 h-5"
                  />
                  <span className="inline-flex items-center gap-1.5">
                    <span className="w-4 h-4 rounded bg-pink-300 border border-pink-400" />
                    Full
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-base">
                  <input
                    type="radio"
                    name="boxType"
                    value="partial"
                    checked={boxType === 'partial'}
                    onChange={() => setBoxType('partial')}
                    className="w-5 h-5"
                  />
                  <span className="inline-flex items-center gap-1.5">
                    <span className="w-4 h-4 rounded bg-yellow-300 border border-yellow-400" />
                    Partial
                  </span>
                </label>
              </div>
            </div>

            {/* Production date */}
            <div className="space-y-2">
              <Label htmlFor="productionDate" className="text-base">
                Production date
              </Label>
              <Input
                id="productionDate"
                type="date"
                value={productionDate}
                onChange={(e) => setProductionDate(e.target.value)}
                className="h-12 text-base"
              />
            </div>

            {/* Error display */}
            {generateLabels.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {generateLabels.error?.message || 'Failed to generate labels'}
                </AlertDescription>
              </Alert>
            )}

            {/* Success display */}
            {generateLabels.isSuccess && (
              <Alert>
                <AlertDescription>
                  Labels generated and downloaded successfully.
                </AlertDescription>
              </Alert>
            )}

            {/* Submit */}
            <Button
              type="submit"
              disabled={!canSubmit}
              className="w-full h-14 text-lg"
            >
              {generateLabels.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Printer className="mr-2 h-5 w-5" />
                  Generate & Download PDF
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
