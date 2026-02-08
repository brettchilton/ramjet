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
import type { CustomerMetric } from '@/types/analytics';
import { formatCurrency, formatCompactCurrency, formatNumber } from '@/utils/formatters';
import { useChartTheme, CHART_COLORS } from '@/utils/chartColors';

interface TopCustomersChartProps {
  data: CustomerMetric[];
}

function ChartView({ data }: { data: CustomerMetric[] }) {
  const theme = useChartTheme();
  const color = CHART_COLORS[3]; // emerald

  const chartData = data.map((d) => ({
    name: d.customer_name.length > 18
      ? d.customer_name.slice(0, 16) + '...'
      : d.customer_name,
    revenue: parseFloat(d.revenue),
    fullName: d.customer_name,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} horizontal={false} />
          <XAxis
            type="number"
            stroke={theme.axisColor}
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => formatCompactCurrency(v)}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke={theme.axisColor}
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={120}
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
              payload?.[0]?.payload?.fullName || ''
            }
          />
          <Bar
            dataKey="revenue"
            fill={color}
            radius={[0, 4, 4, 0]}
            animationDuration={600}
          />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ListView({ data }: { data: CustomerMetric[] }) {
  return (
    <div className="max-h-[280px] overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Customer</TableHead>
            <TableHead className="text-right">Revenue</TableHead>
            <TableHead className="text-right">Orders</TableHead>
            <TableHead className="text-right">Units</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.customer_name}>
              <TableCell className="text-sm font-medium">{row.customer_name}</TableCell>
              <TableCell className="text-right text-sm">{formatCurrency(row.revenue)}</TableCell>
              <TableCell className="text-right text-sm">{formatNumber(row.order_count)}</TableCell>
              <TableCell className="text-right text-sm">{formatNumber(row.unit_count)}</TableCell>
            </TableRow>
          ))}
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No customer data
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function TopCustomersChart({ data }: TopCustomersChartProps) {
  return (
    <ChartCard
      title="Top Customers"
      description="By revenue"
      chart={<ChartView data={data} />}
      list={<ListView data={data} />}
    />
  );
}
