import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'motion/react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ChartCard } from './ChartCard';
import type { ProductMetric } from '@/types/analytics';
import { formatCurrency, formatCompactCurrency, formatNumber } from '@/utils/formatters';
import { useChartTheme, CHART_COLORS } from '@/utils/chartColors';

interface TopProductsChartProps {
  data: ProductMetric[];
}

function ChartView({ data }: { data: ProductMetric[] }) {
  const theme = useChartTheme();
  const color = CHART_COLORS[1]; // violet

  const chartData = data.map((d) => ({
    code: d.product_code,
    revenue: parseFloat(d.revenue),
    description: d.description,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="productGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.9} />
              <stop offset="100%" stopColor={color} stopOpacity={0.5} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} vertical={false} />
          <XAxis
            dataKey="code"
            stroke={theme.axisColor}
            fontSize={11}
            tickLine={false}
            axisLine={false}
            angle={-30}
            textAnchor="end"
            height={50}
          />
          <YAxis
            stroke={theme.axisColor}
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => formatCompactCurrency(v)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: theme.tooltipBg,
              border: `1px solid ${theme.tooltipBorder}`,
              borderRadius: '8px',
              fontSize: '13px',
            }}
            formatter={(value: number | undefined) => [formatCurrency(value ?? 0), 'Revenue']}
            labelFormatter={(_, payload) =>
              payload?.[0]?.payload?.description || payload?.[0]?.payload?.code || ''
            }
          />
          <Bar
            dataKey="revenue"
            fill="url(#productGradient)"
            radius={[4, 4, 0, 0]}
            animationDuration={600}
          />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ListView({ data }: { data: ProductMetric[] }) {
  return (
    <div className="max-h-[280px] overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Code</TableHead>
            <TableHead>Description</TableHead>
            <TableHead className="text-right">Revenue</TableHead>
            <TableHead className="text-right">Qty</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.product_code}>
              <TableCell className="text-sm font-medium">{row.product_code}</TableCell>
              <TableCell className="text-sm text-muted-foreground truncate max-w-[150px]">
                {row.description || '--'}
              </TableCell>
              <TableCell className="text-right text-sm">{formatCurrency(row.revenue)}</TableCell>
              <TableCell className="text-right text-sm">{formatNumber(row.quantity)}</TableCell>
            </TableRow>
          ))}
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No product data
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function TopProductsChart({ data }: TopProductsChartProps) {
  return (
    <ChartCard
      title="Top Products"
      description="By revenue"
      chart={<ChartView data={data} />}
      list={<ListView data={data} />}
    />
  );
}
