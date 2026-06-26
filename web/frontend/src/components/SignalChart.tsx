import { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createSeriesMarkers,
  LineStyle,
} from 'lightweight-charts';

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  [key: string]: any;
}

interface Marker {
  timestamp: string;
  price: number;
  index: number;
  type: string;
}

interface SignalChartProps {
  candles: Candle[];
  buyMarkers: Marker[];
  sellMarkers: Marker[];
}

export default function SignalChart({ candles, buyMarkers, sellMarkers }: SignalChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current || candles.length === 0) return;

    const chartOptions = {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: 'rgba(51,65,85,0.5)' },
        horzLines: { color: 'rgba(51,65,85,0.5)' },
      },
      crosshair: {
        mode: CrosshairMode.Magnet,
        vertLine: { color: '#64748b', lineWidth: 1, style: LineStyle.Dashed, labelBackgroundColor: '#3b82f6' },
        horzLine: { color: '#64748b', lineWidth: 1, style: LineStyle.Dashed, labelBackgroundColor: '#3b82f6' },
      },
      rightPriceScale: { borderColor: '#334155', scaleMargins: { top: 0.05, bottom: 0.15 } },
      timeScale: { borderColor: '#334155', timeVisible: true, secondsVisible: false, rightOffset: 5 },
    };

    const chart = createChart(chartContainerRef.current, chartOptions);

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceLineColor: '#64748b',
    });

    const candleData = candles.map((c) => ({
      time: c.timestamp as any,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeries.setData(candleData);

    if ('rsi' in candles[0] && candles[0].rsi > 0) {
      const rsiSeries = chart.addSeries(LineSeries, {
        priceScaleId: 'rsi',
        color: '#a855f7',
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 1, minMove: 0.1 },
      });
      chart.priceScale('rsi').applyOptions({
        scaleMargins: { top: 0.75, bottom: 0.001 },
      });
      rsiSeries.setData(candles.map((c) => ({ time: c.timestamp as any, value: c.rsi })));
    }

    if ('macd' in candles[0] && candles[0].macd > 0) {
      const macdSeries = chart.addSeries(LineSeries, {
        priceScaleId: 'macd',
        color: '#3b82f6',
        lineWidth: 2,
      });
      const signalSeries = chart.addSeries(LineSeries, {
        priceScaleId: 'macd',
        color: '#ef4444',
        lineWidth: 1,
      });
      chart.priceScale('macd').applyOptions({
        scaleMargins: { top: 0.85, bottom: 0.001 },
      });
      macdSeries.setData(candles.map((c) => ({ time: c.timestamp as any, value: c.macd })));
      signalSeries.setData(candles.map((c) => ({ time: c.timestamp as any, value: c.macd_signal })));
    }

    if ('bb_high' in candles[0] && candles[0].bb_high > 0) {
      const bbUpper = chart.addSeries(LineSeries, {
        color: 'rgba(34,197,94,0.6)',
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      const bbLower = chart.addSeries(LineSeries, {
        color: 'rgba(239,68,68,0.6)',
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bbUpper.setData(candles.map((c) => ({ time: c.timestamp as any, value: c.bb_high })));
      bbLower.setData(candles.map((c) => ({ time: c.timestamp as any, value: c.bb_low })));
    }

    if ('uppershadow' in candles[0]) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeries.setData(
        candles.map((c) => ({
          time: c.timestamp as any,
          value: c.volume,
          color: c.close >= c.open ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)',
        }))
      );
    } else {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeries.setData(
        candles.map((c) => ({
          time: c.timestamp as any,
          value: c.volume,
          color: c.close >= c.open ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)',
        }))
      );
    }

    const allMarkers: any[] = [
      ...buyMarkers.map((m) => ({
        time: m.timestamp as any,
        position: 'belowBar' as const,
        color: '#22c55e',
        shape: 'arrowUp' as const,
        text: 'AL',
      })),
      ...sellMarkers.map((m) => ({
        time: m.timestamp as any,
        position: 'aboveBar' as const,
        color: '#ef4444',
        shape: 'arrowDown' as const,
        text: 'SAT',
      })),
    ];

    allMarkers.sort((a, b) => (a.time < b.time ? -1 : 1));

    if (allMarkers.length > 0) {
      createSeriesMarkers(candleSeries, allMarkers);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [candles, buyMarkers, sellMarkers]);

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.75rem',
        padding: '0 4px',
      }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <div style={{ width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderBottom: '10px solid #22c55e' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>AL ({buyMarkers.length})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <div style={{ width: 0, height: 0, borderLeft: '6px solid transparent', borderRight: '6px solid transparent', borderTop: '10px solid #ef4444' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>SAT ({sellMarkers.length})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <div style={{ width: 12, height: 3, background: '#a855f7' }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>RSI</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <div style={{ width: 12, height: 3, background: '#3b82f6' }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>MACD</span>
          </div>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          {candles.length} mum verisi
        </span>
      </div>
      <div
        ref={chartContainerRef}
        style={{
          width: '100%',
          borderRadius: 8,
          overflow: 'hidden',
          border: '1px solid var(--border-color)',
        }}
      />
    </div>
  );
}