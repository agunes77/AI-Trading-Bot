import { useState, useEffect, useMemo, useRef } from 'react';
import { createChart, ColorType, CrosshairMode, CandlestickSeries, HistogramSeries, LineSeries, LineStyle } from 'lightweight-charts';
import { pricesApi } from '../services/api';
import { Activity, TrendingUp, BarChart3, GitBranch, Zap, RefreshCw, Maximize2 } from 'lucide-react';

const INDICATORS = [
  { id: 'ema', name: 'EMA', period: 20, color: '#3b82f6' },
  { id: 'rsi', name: 'RSI', period: 14, color: '#a855f7' },
  { id: 'macd', name: 'MACD', period: 12, color: '#06b6d4' },
  { id: 'bb', name: 'Bollinger', period: 20, color: '#eab308' },
  { id: 'vwap', name: 'VWAP', period: 20, color: '#22c55e' },
];

export default function Chart() {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeIndicators, setActiveIndicators] = useState<string[]>(['ema', 'rsi']);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await pricesApi.getCrypto(symbol, timeframe, 500);
      setData(res.data.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [symbol, timeframe]);

  const chartData = useMemo(() => data.map((d: any) => ({
    time: d.timestamp,
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
    volume: d.volume,
    rsi: d.rsi,
    macd: d.macd,
    macd_signal: d.macd_signal,
    bb_high: d.bb_high,
    bb_low: d.bb_low,
  })), [data]);

  useEffect(() => {
    if (!chartContainerRef.current || chartData.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 650,
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
        fontSize: 12,
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(51,65,85,0.3)' },
        horzLines: { color: 'rgba(51,65,85,0.3)' },
      },
      crosshair: {
        mode: CrosshairMode.Magnet,
        vertLine: { color: '#64748b', style: LineStyle.Dashed, labelBackgroundColor: '#3b82f6' },
        horzLine: { color: '#64748b', style: LineStyle.Dashed, labelBackgroundColor: '#3b82f6' },
      },
      rightPriceScale: { borderColor: '#334155', scaleMargins: { top: 0.05, bottom: 0.2 } },
      timeScale: { borderColor: '#334155', timeVisible: true, secondsVisible: false, rightOffset: 5 },
    });

    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a', downColor: '#ef5350',
      borderUpColor: '#26a69a', borderDownColor: '#ef5350',
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });
    candleSeries.setData(chartData);

    // Hacim
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' }, priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volumeSeries.setData(chartData.map(c => ({
      time: c.time, value: c.volume,
      color: c.close >= c.open ? 'rgba(38,166,154,0.4)' : 'rgba(239,83,80,0.4)'
    })));

    // Aktif İndikatörler
    activeIndicators.forEach(indId => {
      const ind = INDICATORS.find(i => i.id === indId);
      if (!ind) return;

      if (ind.id === 'ema') {
        const ema = chartData.map((c, i) => {
          const k = 2 / (ind.period + 1);
          let prev = chartData[0].close;
          for (let j = 1; j <= i; j++) {
            prev = chartData[j].close * k + prev * (1 - k);
          }
          return { time: c.time, value: prev };
        });
        const emaSeries = chart.addSeries(LineSeries, { color: ind.color, lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
        emaSeries.setData(ema);
      } else if (ind.id === 'rsi') {
        const rsiSeries = chart.addSeries(LineSeries, { priceScaleId: 'rsi', color: ind.color, lineWidth: 2 });
        chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.75, bottom: 0.001 } });
        rsiSeries.setData(chartData.filter(c => c.rsi > 0).map(c => ({ time: c.time, value: c.rsi })));
      } else if (ind.id === 'macd') {
        const macdSeries = chart.addSeries(LineSeries, { priceScaleId: 'macd', color: '#3b82f6', lineWidth: 2 });
        const signalSeries = chart.addSeries(LineSeries, { priceScaleId: 'macd', color: '#ef4444', lineWidth: 1 });
        chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.85, bottom: 0.001 } });
        macdSeries.setData(chartData.filter(c => c.macd > 0).map(c => ({ time: c.time, value: c.macd })));
        signalSeries.setData(chartData.filter(c => c.macd_signal > 0).map(c => ({ time: c.time, value: c.macd_signal })));
      } else if (ind.id === 'bb') {
        const bbUpper = chart.addSeries(LineSeries, { color: 'rgba(234,179,8,0.7)', lineWidth: 1, lineStyle: LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false });
        const bbLower = chart.addSeries(LineSeries, { color: 'rgba(234,179,8,0.7)', lineWidth: 1, lineStyle: LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false });
        bbUpper.setData(chartData.filter(c => c.bb_high > 0).map(c => ({ time: c.time, value: c.bb_high })));
        bbLower.setData(chartData.filter(c => c.bb_low > 0).map(c => ({ time: c.time, value: c.bb_low })));
      }
    });

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [chartData, activeIndicators]);

  const toggleIndicator = (id: string) => {
    setActiveIndicators(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Grafik & Analiz</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Profesyonel TradingView Stili Grafik</p>
        </div>
        <button className="btn btn-outline" onClick={loadData} disabled={loading}>
          <RefreshCw size={16} style={{ marginRight: '0.5rem' }} /> Yenile
        </button>
      </div>

      <div style={{
        display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap',
        alignItems: 'center', padding: '0.75rem', background: 'var(--bg-card)', borderRadius: 10,
      }}>
        <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ width: 180 }}>
          <option value="BTC/USDT">Bitcoin (BTC/USDT)</option>
          <option value="ETH/USDT">Ethereum (ETH/USDT)</option>
          <option value="BNB/USDT">BNB/USDT</option>
          <option value="SOL/USDT">Solana (SOL/USDT)</option>
          <option value="XRP/USDT">XRP/USDT</option>
          <option value="ADA/USDT">Cardano (ADA/USDT)</option>
          <option value="DOGE/USDT">Dogecoin (DOGE/USDT)</option>
        </select>

        <div style={{ display: 'flex', gap: '0.25rem' }}>
          {['15m', '1h', '4h', '1d'].map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)} style={{
              padding: '0.4rem 0.75rem', borderRadius: 6,
              border: timeframe === tf ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
              background: timeframe === tf ? 'var(--accent-blue)' : 'var(--bg-primary)',
              color: timeframe === tf ? 'white' : 'var(--text-primary)',
              cursor: 'pointer', fontSize: '0.8rem', fontWeight: 500,
            }}>{tf}</button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {INDICATORS.map(ind => (
            <button key={ind.id} onClick={() => toggleIndicator(ind.id)} style={{
              display: 'flex', alignItems: 'center', gap: '0.3rem',
              padding: '0.3rem 0.6rem', borderRadius: 5,
              border: activeIndicators.includes(ind.id) ? `1px solid ${ind.color}` : '1px solid var(--border-color)',
              background: activeIndicators.includes(ind.id) ? `${ind.color}20` : 'var(--bg-primary)',
              color: activeIndicators.includes(ind.id) ? ind.color : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.75rem', fontWeight: 500,
            }}>
              <span style={{ width: 10, height: 2, background: ind.color, borderRadius: 1 }} />
              {ind.name}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        background: 'var(--bg-card)', borderRadius: 12, overflow: 'hidden',
        border: '1px solid var(--border-color)', padding: '0.5rem',
      }}>
        {loading ? (
          <div className="loading" style={{ height: 650 }}>Veri Yükleniyor...</div>
        ) : (
          <div ref={chartContainerRef} style={{ width: '100%' }} />
        )}
      </div>

      {data.length > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem', marginTop: '1rem',
        }}>
          {[
            { label: 'Son Fiyat', value: data[data.length-1]?.close?.toFixed(2), icon: TrendingUp, color: '#3b82f6' },
            { label: '24s Değişim', value: ((data[data.length-1]?.close - data[0]?.open) / data[0]?.open * 100)?.toFixed(2) + '%', icon: Activity, color: '#22c55e' },
            { label: '24s Yüksek', value: Math.max(...data.map(d => d.high))?.toFixed(2), icon: BarChart3, color: '#eab308' },
            { label: '24s Düşük', value: Math.min(...data.map(d => d.low))?.toFixed(2), icon: Zap, color: '#ef4444' },
            { label: 'RSI (14)', value: data[data.length-1]?.rsi?.toFixed(2), icon: GitBranch, color: '#a855f7' },
            { label: 'Hacim', value: data[data.length-1]?.volume?.toLocaleString(), icon: Maximize2, color: '#06b6d4' },
          ].map((stat, i) => (
            <div key={i} className="card" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="text-muted" style={{ fontSize: '0.75rem' }}>{stat.label}</span>
                <stat.icon size={16} color={stat.color} />
              </div>
              <span style={{ fontSize: '1.1rem', fontWeight: 600, fontFamily: 'monospace' }}>{stat.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}