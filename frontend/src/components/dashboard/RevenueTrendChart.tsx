import {
  AreaChart,
  Area,
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
import type { RevenueTrendPoint } from '@/types/analytics';
import { formatCurrency, formatCompactCurrency } from '@/utils/formatters';
import { useChartTheme, CHART_COLORS } from '@/utils/chartColors';

interface RevenueTrendChartProps {
  data: RevenueTrendPoint[];
}

function ChartView({ data }: { data: RevenueTrendPoint[] }) {
  const theme = useChartTheme();
  const color = CHART_COLORS[0];

  const chartData = data.map((d) => ({
    ...d,
    revenue: parseFloat(d.revenue),
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} vertical={false} />
          <XAxis
            dataKey="date"
            stroke={theme.axisColor}
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => {
              const d = new Date(v);
              return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short' });
            }}
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
            labelFormatter={(v) => {
              const d = new Date(v);
              return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric' });
            }}
            formatter={(value: number | undefined) => [formatCurrency(value ?? 0), 'Revenue']}
          />
          <Area
            type="natural"
            dataKey="revenue"
            stroke={color}
            strokeWidth={2}
            fill="url(#revenueGradient)"
            animationDuration={800}
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ListView({ data }: { data: RevenueTrendPoint[] }) {
  return (
    <div className="max-h-[280px] overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead className="text-right">Revenue</TableHead>
            <TableHead className="text-right">Orders</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.date}>
              <TableCell className="text-sm">
                {new Date(row.date).toLocaleDateString('en-AU', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </TableCell>
              <TableCell className="text-right text-sm">{formatCurrency(row.revenue)}</TableCell>
              <TableCell className="text-right text-sm">{row.order_count}</TableCell>
            </TableRow>
          ))}
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={3} className="text-center text-muted-foreground">
                No data for this period
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function RevenueTrendChart({ data }: RevenueTrendChartProps) {
  return (
    <ChartCard
      title="Revenue Trend"
      description="Approved order revenue over time"
      chart={<ChartView data={data} />}
      list={<ListView data={data} />}
    />
  );
}
