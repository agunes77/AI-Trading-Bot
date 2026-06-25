import { useEffect, useState } from 'react';
import { pricesApi } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, LineChart, Line } from 'recharts';

export default function Chart() {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [indicator, setIndicator] = useState('rsi');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await pricesApi.getCrypto(symbol, timeframe, 200);
      setData(res.data.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [symbol, timeframe]);

  const chartData = data.map((d: any) => ({
    time: new Date(d.timestamp).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    close: d.close,
    open: d.open,
    high: d.high,
    low: d.low,
    volume: d.volume,
    rsi: d.rsi,
    macd: d.macd,
    macd_signal: d.macd_signal,
    bb_high: d.bb_high,
    bb_low: d.bb_low,
  }));

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Grafik & Analiz</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Teknik analiz ve indikator gorunumu</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)} style={{ width: 180 }}>
          <option value="BTC/USDT">BTC/USDT</option>
          <option value="ETH/USDT">ETH/USDT</option>
          <option value="BNB/USDT">BNB/USDT</option>
          <option value="SOL/USDT">SOL/USDT</option>
          <option value="XRP/USDT">XRP/USDT</option>
        </select>

        <select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)} style={{ width: 120 }}>
          <option value="15m">15m</option>
          <option value="1h">1h</option>
          <option value="4h">4h</option>
          <option value="1d">1d</option>
        </select>

        <select className="select" value={indicator} onChange={(e) => setIndicator(e.target.value)} style={{ width: 180 }}>
          <option value="rsi">RSI</option>
          <option value="macd">MACD</option>
          <option value="bb">Bollinger Bands</option>
          <option value="volume">Hacim</option>
        </select>
      </div>

      {loading ? (
        <div className="loading">Yukleniyor...</div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
              {symbol} Fiyat Grafigi ({timeframe})
            </h3>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval="preserveStartEnd" />
                <YAxis stroke="#64748b" fontSize={10} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Area type="monotone" dataKey="close" stroke="#3b82f6" fill="url(#colorClose)" strokeWidth={2} />
                {indicator === 'bb' && (
                  <>
                    <Line type="monotone" dataKey="bb_high" stroke="#22c55e" strokeWidth={1} dot={false} strokeDasharray="5 5" />
                    <Line type="monotone" dataKey="bb_low" stroke="#ef4444" strokeWidth={1} dot={false} strokeDasharray="5 5" />
                  </>
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
                {indicator === 'rsi' ? 'RSI (14)' : indicator === 'macd' ? 'MACD' : indicator === 'volume' ? 'Hacim' : 'Indikator'}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                {indicator === 'rsi' ? (
                  <LineChart data={chartData}>
                    <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval="preserveStartEnd" />
                    <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                    <Line type="monotone" dataKey="rsi" stroke="#a855f7" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey={() => 70} stroke="#ef4444" strokeWidth={1} dot={false} strokeDasharray="5 5" />
                    <Line type="monotone" dataKey={() => 30} stroke="#22c55e" strokeWidth={1} dot={false} strokeDasharray="5 5" />
                  </LineChart>
                ) : indicator === 'macd' ? (
                  <LineChart data={chartData}>
                    <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval="preserveStartEnd" />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                    <Line type="monotone" dataKey="macd" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="macd_signal" stroke="#ef4444" strokeWidth={1} dot={false} />
                  </LineChart>
                ) : (
                  <BarChart data={chartData}>
                    <XAxis dataKey="time" stroke="#64748b" fontSize={10} interval="preserveStartEnd" />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                    <Bar dataKey="volume" fill="#3b82f6" opacity={0.7} />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Fiyat Bilgileri</h3>
              {chartData.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span className="text-muted">Son Fiyat</span>
                    <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                      ${chartData[chartData.length - 1].close?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span className="text-muted">Acilis</span>
                    <span style={{ fontFamily: 'monospace' }}>${chartData[chartData.length - 1].open?.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span className="text-muted">Yuksek</span>
                    <span className="text-green" style={{ fontFamily: 'monospace' }}>${chartData[chartData.length - 1].high?.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span className="text-muted">Dusuk</span>
                    <span className="text-red" style={{ fontFamily: 'monospace' }}>${chartData[chartData.length - 1].low?.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                    <span className="text-muted">RSI</span>
                    <span className="text-purple" style={{ fontFamily: 'monospace' }}>{chartData[chartData.length - 1].rsi?.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0' }}>
                    <span className="text-muted">Hacim</span>
                    <span style={{ fontFamily: 'monospace' }}>{chartData[chartData.length - 1].volume?.toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
