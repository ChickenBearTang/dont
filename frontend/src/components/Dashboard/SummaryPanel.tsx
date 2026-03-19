import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';
import type { SummaryData, DailyCumulative } from './types';

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
}

function formatMonthLabel(month: string) {
  if (!month) return "";
  const [, value] = month.split("-");
  return `${Number(value)}월`;
}

interface Props {
  summary: SummaryData;
  daily: DailyCumulative[];
}

export function SummaryPanel({ summary, daily }: Props) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    
    if (chartInstance.current) {
        chartInstance.current.destroy();
    }

    chartInstance.current = new Chart(chartRef.current, {
      type: 'line',
      data: {
        labels: daily.map((row) => row.day),
        datasets: [
          {
            label: "이번 달",
            data: daily.map((row) => row.current_cumulative_amount),
            borderColor: "#ffd400",
            backgroundColor: "#ffd400",
            tension: 0.32,
            pointRadius: 0
          },
          {
            label: "전월",
            data: daily.map((row) => row.previous_cumulative_amount),
            borderColor: "#727785",
            backgroundColor: "#727785",
            tension: 0.32,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#97a0b4" }, grid: { display: false } },
          y: { ticks: { color: "#97a0b4" }, grid: { color: "rgba(255,255,255,0.08)" } }
        }
      }
    });

    return () => {
        if (chartInstance.current) {
            chartInstance.current.destroy();
            chartInstance.current = null;
        }
    };
  }, [daily]);

  // Replace text with bold matching
  const renderBannerText = (txt: string) => {
    if (!txt) return null;
    const parts = txt.split(/([0-9,]+원)/);
    return parts.map((part, i) => part.endsWith('원') ? <strong key={i}>{part}</strong> : part);
  };

  return (
    <section className="panel">
      <div className="headline">
        <h2 id="summary-month">{formatMonthLabel(summary.selected_month)}</h2>
      </div>
      <div id="summary-amount" className="summary-amount">{formatCurrency(summary.current_total_spend)}</div>
      <div id="summary-banner" className="compare-banner">{renderBannerText(summary.difference_text)}</div>
      <div className="chart-wrap">
        <canvas ref={chartRef}></canvas>
      </div>
      <div className="legend-row">
        <div className="legend-label"><span className="dot" style={{background: 'var(--yellow)'}}></span><span id="current-range">{summary.selected_month} 누적</span></div>
        <strong id="current-total">{formatCurrency(summary.current_total_spend)}</strong>
      </div>
      <div className="legend-row">
        <div className="legend-label"><span className="dot" style={{background: '#d7dce5'}}></span><span id="previous-range">{summary.previous_month} 누적</span></div>
        <strong id="previous-total">{formatCurrency(summary.previous_total_spend)}</strong>
      </div>
    </section>
  );
}
