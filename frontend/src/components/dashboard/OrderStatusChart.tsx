import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
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
import type { StatusBreakdown } from '@/types/analytics';
import { useChartTheme, STATUS_COLORS } from '@/utils/chartColors';
import { formatPercent } from '@/utils/formatters';

interface OrderStatusChartProps {
  data: StatusBreakdown[];
}

function ChartView({ data }: { data: StatusBreakdown[] }) {
  const theme = useChartTheme();
  const total = data.reduce((sum, d) => sum + d.count, 0);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={110}
            paddingAngle={3}
            dataKey="count"
            nameKey="status"
            animationDuration={600}
            stroke="none"
          >
            {data.map((entry) => (
              <Cell
                key={entry.status}
                fill={STATUS_COLORS[entry.status] || '#6b7280'}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: theme.tooltipBg,
              border: `1px solid ${theme.tooltipBorder}`,
              borderRadius: '8px',
              fontSize: '13px',
            }}
            formatter={(value: number | undefined, name: string | undefined) => [
              `${value ?? 0} (${formatPercent(((value ?? 0) / total) * 100)})`,
              (name ?? '').charAt(0).toUpperCase() + (name ?? '').slice(1),
            ]}
          />
          {/* Center label */}
          <text
            x="50%"
            y="48%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-foreground"
            fontSize={28}
            fontWeight={700}
          >
            {total}
          </text>
          <text
            x="50%"
            y="58%"
            textAnchor="middle"
            dominantBaseline="middle"
            fill={theme.textColor}
            fontSize={12}
          >
            orders
          </text>
        </PieChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ListView({ data }: { data: StatusBreakdown[] }) {
  return (
    <div className="max-h-[280px] overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Count</TableHead>
            <TableHead className="text-right">%</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.status}>
              <TableCell className="text-sm">
                <span className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: STATUS_COLORS[row.status] || '#6b7280' }}
                  />
                  {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
                </span>
              </TableCell>
              <TableCell className="text-right text-sm">{row.count}</TableCell>
              <TableCell className="text-right text-sm">{formatPercent(row.percentage)}</TableCell>
            </TableRow>
          ))}
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={3} className="text-center text-muted-foreground">
                No data
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function OrderStatusChart({ data }: OrderStatusChartProps) {
  return (
    <ChartCard
      title="Order Status"
      description="Breakdown by status"
      chart={<ChartView data={data} />}
      list={<ListView data={data} />}
    />
  );
}
