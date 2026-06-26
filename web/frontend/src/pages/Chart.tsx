import { useState, useEffect, useMemo, useRef } from 'react';
import {
  createChart, ColorType, CrosshairMode, CandlestickSeries, HistogramSeries,
  LineSeries, LineStyle
} from 'lightweight-charts';
import { pricesApi } from '../services/api';
import { RefreshCw } from 'lucide-react';

// TradingView Pro Dark Tema Renk Paleti (Birebir)
const TV_COLORS = {
  bg: '#131722',
  text: '#d1d4dc',
  grid: '#2a2e39',
  border: '#434651',
  green: '#089981',
  red: '#f23645',
  blue: '#2962ff',
  purple: '#9b4dff',
  yellow: '#f5a623',
  orange: '#ff9800',
  teal: '#26c6da',
};

const INDICATORS = [
  { id: 'ema_9', name: 'EMA 9', color: TV_COLORS.yellow },
  { id: 'ema_21', name: 'EMA 21', color: TV_COLORS.orange },
  { id: 'ema_50', name: 'EMA 50', color: TV_COLORS.red },
  { id: 'rsi', name: 'RSI 14', color: TV_COLORS.purple },
  { id: 'macd', name: 'MACD', color: TV_COLORS.blue },
  { id: 'bb', name: 'Bollinger', color: TV_COLORS.teal },
  { id: 'vwap', name: 'VWAP', color: TV_COLORS.green },
  { id: 'volume', name: 'Hacim', color: '#5d6a7d' },
];

// EMA Hesaplama yardımcı fonksiyonu (Lightweight-charts için client-side hesap)
function calcEMA(data: any[], period: number) {
  const k = 2 / (period + 1);
  const emas: any[] = [];
  let prev = data[0]?.close || 0;
  data.forEach((c, i) => {
    if (i === 0) {
      prev = c.close;
      emas.push({ time: c.time, value: prev });
    } else {
      prev = c.close * k + prev * (1 - k);
      emas.push({ time: c.time, value: prev });
    }
  });
  return emas;
}

function calcBollinger(data: any[], period: number = 20, mult: number = 2) {
  const upper: any[] = [];
  const lower: any[] = [];
  const basis: any[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i >= period - 1) {
      const slice = data.slice(i - period + 1, i + 1);
      const closes = slice.map(d => d.close);
      const mean = closes.reduce((a, b) => a + b, 0) / period;
      const variance = closes.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
      const std = Math.sqrt(variance);
      upper.push({ time: data[i].time, value: mean + mult * std });
      lower.push({ time: data[i].time, value: mean - mult * std });
      basis.push({ time: data[i].time, value: mean });
    }
  }
  return { upper, lower, basis };
}

export default function Chart() {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [limit] = useState(500);
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeIndicators, setActiveIndicators] = useState<string[]>(['ema_9', 'ema_21', 'macd', 'volume']);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await pricesApi.getCrypto(symbol, timeframe, limit);
      setData(res.data.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [symbol, timeframe, limit]);

  const chartData = useMemo(() => data.map((d: any) => ({
    time: d.timestamp,
    open: d.open, high: d.high, low: d.low, close: d.close, volume: d.volume,
    rsi: d.rsi, macd: d.macd, macd_signal: d.macd_signal, bb_high: d.bb_high, bb_low: d.bb_low,
  })), [data]);

  useEffect(() => {
    if (!chartContainerRef.current || chartData.length === 0) return;

    // TİPİK TRADINGVIEW GÖRÜNÜMÜ (Professional Dark Theme)
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: window.innerHeight - 320,
      layout: {
        background: { type: ColorType.Solid, color: TV_COLORS.bg },
        textColor: TV_COLORS.text,
        fontSize: 12,
        fontFamily: 'Trebuchet MS, Roboto, Ubuntu, sans-serif',
      },
      grid: {
        vertLines: { color: TV_COLORS.grid, style: LineStyle.Solid },
        horzLines: { color: TV_COLORS.grid, style: LineStyle.Solid },
      },
      crosshair: {
        mode: CrosshairMode.Magnet,
        vertLine: { color: TV_COLORS.border, style: LineStyle.Dashed, labelBackgroundColor: '#363a45' },
        horzLine: { color: TV_COLORS.border, style: LineStyle.Dashed, labelBackgroundColor: '#363a45' },
      },
      rightPriceScale: { borderColor: TV_COLORS.border, scaleMargins: { top: 0.05, bottom: 0.25 } },
      timeScale: { borderColor: TV_COLORS.border, timeVisible: true, secondsVisible: false, rightOffset: 8, barSpacing: 8 },
    });

    chartRef.current = chart;

    // Ana Mum Serisi (Tradingview Birebir)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: TV_COLORS.green, downColor: TV_COLORS.red,
      borderUpColor: TV_COLORS.green, borderDownColor: TV_COLORS.red,
      wickUpColor: TV_COLORS.green, wickDownColor: TV_COLORS.red,
      priceLineVisible: true, priceLineColor: TV_COLORS.border, priceLineStyle: LineStyle.Dotted,
    });
    candleSeries.setData(chartData);
    candleSeries.applyOptions({ priceFormat: { type: 'price', precision: 2, minMove: 0.01 } });

    // Aktif İndikatörler
    const volumeActive = activeIndicators.includes('volume');
    if (volumeActive) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' }, priceScaleId: 'vol', color: TV_COLORS.green,
      });
      chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
      volumeSeries.setData(chartData.map(c => ({ time: c.time, value: c.volume, color: c.close >= c.open ? `${TV_COLORS.green}40` : `${TV_COLORS.red}40` })));
    }

    if (activeIndicators.includes('ema_9')) {
      const s = chart.addSeries(LineSeries, { color: TV_COLORS.yellow, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      s.setData(calcEMA(chartData, 9));
    }
    if (activeIndicators.includes('ema_21')) {
      const s = chart.addSeries(LineSeries, { color: TV_COLORS.orange, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      s.setData(calcEMA(chartData, 21));
    }
    if (activeIndicators.includes('ema_50')) {
      const s = chart.addSeries(LineSeries, { color: TV_COLORS.red, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
      s.setData(calcEMA(chartData, 50));
    }

    if (activeIndicators.includes('rsi')) {
      const rsiSeries = chart.addSeries(LineSeries, { priceScaleId: 'rsi', color: TV_COLORS.purple, lineWidth: 2, priceLineVisible: false, lastValueVisible: true });
      chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.75, bottom: 0.001 } });
      rsiSeries.setData(chartData.filter(c => c.rsi > 0).map(c => ({ time: c.time, value: c.rsi })));
      rsiSeries.createPriceLine({ price: 70, color: TV_COLORS.red, lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'OB' });
      rsiSeries.createPriceLine({ price: 30, color: TV_COLORS.green, lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'OS' });
    }

    if (activeIndicators.includes('macd')) {
      const macdSeries = chart.addSeries(LineSeries, { priceScaleId: 'macd', color: TV_COLORS.blue, lineWidth: 2, priceLineVisible: false });
      const signalSeries = chart.addSeries(LineSeries, { priceScaleId: 'macd', color: TV_COLORS.red, lineWidth: 2, priceLineVisible: false });
      const histSeries = chart.addSeries(HistogramSeries, { priceScaleId: 'macd', priceFormat: { type: 'price' } });
      chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.85, bottom: 0.001 } });
      macdSeries.setData(chartData.filter(c => c.macd > 0).map(c => ({ time: c.time, value: c.macd })));
      signalSeries.setData(chartData.filter(c => c.macd_signal > 0).map(c => ({ time: c.time, value: c.macd_signal })));
      histSeries.setData(chartData.filter(c => c.macd > 0).map(c => ({ time: c.time, value: c.macd - c.macd_signal, color: c.macd >= c.macd_signal ? `${TV_COLORS.green}60` : `${TV_COLORS.red}60` })));
    }

    if (activeIndicators.includes('bb')) {
      const up = chart.addSeries(LineSeries, { color: TV_COLORS.teal, lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      const low = chart.addSeries(LineSeries, { color: TV_COLORS.teal, lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      const mid = chart.addSeries(LineSeries, { color: `${TV_COLORS.teal}80`, lineWidth: 1, lineStyle: LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false });
      const bb = calcBollinger(chartData, 20, 2);
      up.setData(bb.upper);
      low.setData(bb.lower);
      mid.setData(bb.basis);
    }

    if (activeIndicators.includes('vwap')) {
      const v = chartData.map((c, i) => {
        if (i === 0) return { time: c.time, value: c.close };
        const slice = chartData.slice(Math.max(0, i - 20), i + 1);
        const sumPV = slice.reduce((a, b) => a + (b.close * b.volume), 0);
        const sumV = slice.reduce((a, b) => a + b.volume, 0);
        return { time: c.time, value: sumV ? sumPV / sumV : c.close };
      });
      const s = chart.addSeries(LineSeries, { color: TV_COLORS.green, lineWidth: 3, priceLineVisible: false, lastValueVisible: false, lineStyle: LineStyle.Dotted });
      s.setData(v);
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [chartData, activeIndicators, symbol, limit]);

  const toggleIndicator = (id: string) => {
    setActiveIndicators(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: TV_COLORS.text }}>Grafik & Analiz</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Profesyonel TradingView Dark Tema</p>
        </div>
        <button className="btn btn-outline" onClick={loadData} disabled={loading}>
          <RefreshCw size={16} style={{ marginRight: '0.5rem' }} /> Yenile
        </button>
      </div>

      {/* TradingView Tarzı Grafik Araç Çubuğu */}
      <div style={{
        display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap',
        alignItems: 'center', padding: '0.5rem 1rem',
        background: TV_COLORS.bg, borderRadius: 8,
        border: `1px solid ${TV_COLORS.border}`,
      }}>
        <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ width: 150, background: TV_COLORS.grid, color: TV_COLORS.text, borderColor: TV_COLORS.border }}>
          <option value="BTC/USDT">BTC/USDT</option>
          <option value="ETH/USDT">ETH/USDT</option>
          <option value="BNB/USDT">BNB/USDT</option>
          <option value="SOL/USDT">SOL/USDT</option>
          <option value="XRP/USDT">XRP/USDT</option>
          <option value="ADA/USDT">ADA/USDT</option>
        </select>

        <div style={{ width: '1px', height: '24px', background: TV_COLORS.border }} />

        <div style={{ display: 'flex', gap: '0.1rem' }}>
          {['15m', '1h', '4h', '1d'].map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)} style={{
              padding: '0.35rem 0.6rem', borderRadius: 4,
              border: 'none',
              background: timeframe === tf ? TV_COLORS.blue : 'transparent',
              color: timeframe === tf ? 'white' : TV_COLORS.text,
              cursor: 'pointer', fontSize: '0.8rem', fontWeight: 500,
            }}>{tf}</button>
          ))}
        </div>

        <div style={{ width: '1px', height: '24px', background: TV_COLORS.border }} />

        <div style={{ display: 'flex', gap: '0.1rem', flexWrap: 'wrap', flex: 1 }}>
          {INDICATORS.map(ind => (
            <button key={ind.id} onClick={() => toggleIndicator(ind.id)} style={{
              display: 'flex', alignItems: 'center', gap: '0.3rem',
              padding: '0.3rem 0.5rem', borderRadius: 4, border: 'none',
              background: activeIndicators.includes(ind.id) ? `${ind.color}30` : 'transparent',
              color: activeIndicators.includes(ind.id) ? ind.color : '#758596',
              cursor: 'pointer', fontSize: '0.75rem', fontWeight: 500,
            }}>
              <span style={{ width: 8, height: 8, background: ind.color, borderRadius: '50%' }} />
              {ind.name}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        background: TV_COLORS.bg, borderRadius: 8,
        border: `1px solid ${TV_COLORS.border}`, overflow: 'hidden',
      }}>
        {loading ? (
          <div style={{ height: 'calc(100vh - 400px)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: TV_COLORS.text }}>
            Veri Yükleniyor...
          </div>
        ) : (
          <div ref={chartContainerRef} style={{ width: '100%' }} />
        )}
      </div>
    </div>
  );
}