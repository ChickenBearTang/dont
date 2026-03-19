import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';
import type { TrendData } from './types';

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
}

function formatMonthLabel(month: string) {
  if (!month) return "";
  const [, value] = month.split("-");
  return `${Number(value)}월`;
}

interface Props {
  trend: TrendData;
}

export function TrendPanel({ trend }: Props) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    
    if (chartInstance.current) {
        chartInstance.current.destroy();
    }

    chartInstance.current = new Chart(chartRef.current, {
      type: 'bar',
      data: {
        labels: trend.months.map((row) => formatMonthLabel(row.month)),
        datasets: [
          {
            label: "월간 소비",
            data: trend.months.map((row) => row.total_card_spend),
            backgroundColor: trend.months.map((row) => row.is_selected_month ? "#ff3b30" : "#5e636f"),
            borderRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#97a0b4" }, grid: { display: false } },
          y: {
            ticks: { color: "#97a0b4" },
            grid: { color: "rgba(255,255,255,0.08)" }
          }
        }
      }
    });

    return () => {
        if (chartInstance.current) {
            chartInstance.current.destroy();
            chartInstance.current = null;
        }
    };
  }, [trend]);

  const avgFormat = `약 ${Math.round(trend.average_amount / 10000)}만원`;

  return (
    <section className="panel">
      <h2>6개월 평균 소비</h2>
      <div id="avg-text" style={{marginTop: 6, fontSize: 26, fontWeight: 700}}>{avgFormat}</div>
      <div className="chart-wrap">
        <canvas ref={chartRef}></canvas>
      </div>
      <div id="avg-note" className="avg-note">6개월 평균 소비 금액은 {formatCurrency(trend.average_amount)} 입니다.</div>
    </section>
  );
}
