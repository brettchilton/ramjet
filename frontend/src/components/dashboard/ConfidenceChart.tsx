import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
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
import type { ConfidenceBucket } from '@/types/analytics';
import { useChartTheme, CONFIDENCE_COLORS } from '@/utils/chartColors';
import { formatNumber } from '@/utils/formatters';

interface ConfidenceChartProps {
  data: ConfidenceBucket[];
}

function ChartView({ data }: { data: ConfidenceBucket[] }) {
  const theme = useChartTheme();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} vertical={false} />
          <XAxis
            dataKey="bucket"
            stroke={theme.axisColor}
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke={theme.axisColor}
            fontSize={12}
            tickLine={false}
            axisLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: theme.tooltipBg,
              border: `1px solid ${theme.tooltipBorder}`,
              borderRadius: '8px',
              fontSize: '13px',
            }}
            formatter={(value: number | undefined) => [value ?? 0, 'Orders']}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} animationDuration={600}>
            {data.map((entry) => (
              <Cell
                key={entry.bucket}
                fill={CONFIDENCE_COLORS[entry.bucket] || '#6b7280'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function ListView({ data }: { data: ConfidenceBucket[] }) {
  return (
    <div className="max-h-[280px] overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Confidence</TableHead>
            <TableHead className="text-right">Count</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.bucket}>
              <TableCell className="text-sm">
                <span className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: CONFIDENCE_COLORS[row.bucket] || '#6b7280' }}
                  />
                  {row.bucket}
                </span>
              </TableCell>
              <TableCell className="text-right text-sm">{formatNumber(row.count)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function ConfidenceChart({ data }: ConfidenceChartProps) {
  return (
    <ChartCard
      title="AI Confidence Distribution"
      description="Extraction confidence scores"
      chart={<ChartView data={data} />}
      list={<ListView data={data} />}
    />
  );
}
