"use client";

import { useMemo } from "react";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import type { ComparisonMetric } from "@/lib/contracts";
import { formatMetric } from "@/lib/format";

interface ComparisonTableProps {
  metrics: ComparisonMetric[];
  tickers: string[];
}

export function ComparisonTable({ metrics, tickers }: ComparisonTableProps) {
  const columns = useMemo<ColumnDef<ComparisonMetric>[]>(
    () => [
      {
        id: "metric",
        header: "Metric",
        cell: ({ row }) => <>{row.original.label}{row.original.unit ? <span className="telemetry"> / {row.original.unit}</span> : null}</>,
      },
      ...tickers.map<ColumnDef<ComparisonMetric>>((ticker) => ({
        id: ticker,
        header: ticker,
        cell: ({ row }) => (
          <data value={String(row.original.values[ticker] ?? "")}>{formatMetric(row.original.values[ticker] ?? null, row.original.unit)}</data>
        ),
      })),
    ],
    [tickers],
  );
  const table = useReactTable({ data: metrics, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="table-scroll" tabIndex={0} aria-label="Scrollable cross-stock comparison table">
      <table className="comparison-table">
        <caption>Cross-stock comparison. Scroll horizontally on narrow screens.</caption>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} scope="col">
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  {cell.column.id !== "metric" && row.original.preferred_ticker === cell.column.id ? <span className="preferred-mark">Preferred</span> : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
