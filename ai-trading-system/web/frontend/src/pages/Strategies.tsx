import { useEffect, useState } from 'react';
import { strategiesApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Play, List, Trophy, GitCompare } from 'lucide-react';

export default function Strategies() {
  const [strategies, setStrategies] = useState<any[]>([]);
  const [mode, setMode] = useState<'list' | 'backtest' | 'compare' | 'top'>('list');
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [source, setSource] = useState('crypto');
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [days, setDays] = useState(365);
  const [stopLoss, setStopLoss] = useState(0.02);
  const [takeProfit, setTakeProfit] = useState(0.04);
  const [result, setResult] = useState<any>(null);
  const [comparison, setComparison] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    strategiesApi.list().then(res => setStrategies(res.data.strategies || [])).catch(console.error);
  }, []);

  const runBacktest = async () => {
    if (!selectedStrategy) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await strategiesApi.backtest({
        source, symbol, strategy: selectedStrategy, timeframe, days,
        initial_balance: 10000, stop_loss: stopLoss, take_profit: takeProfit,
      });
      setResult(res.data.result);
    } catch (e: any) {
      setResult({ error: e.response?.data?.detail || 'Hata olustu' });
    } finally {
      setLoading(false);
    }
  };

  const runCompare = async () => {
    setLoading(true);
    setComparison([]);
    try {
      const res = await strategiesApi.compare({
        source, symbol, timeframe, days,
        initial_balance: 10000, stop_loss: stopLoss, take_profit: takeProfit,
      });
      setComparison(res.data.comparison || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const runTop = async () => {
    setLoading(true);
    setComparison([]);
    try {
      const res = await strategiesApi.top({
        source, symbol, timeframe, days,
        initial_balance: 10000, stop_loss: stopLoss, take_profit: takeProfit,
      });
      setComparison((res.data.top_strategies || []).map((s: any) => ({
        Strateji: s.strategy_name,
        'Getiri %': s.total_return_pct?.toFixed(2),
        'Max DD %': s.max_drawdown_pct?.toFixed(2),
        Sharpe: s.sharpe_ratio?.toFixed(3),
        Islem: s.total_trades,
        'Kazanma %': s.win_rate_pct?.toFixed(1),
      })));
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Strateji Yonetimi</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Klasik ve ozel stratejileri test edin</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button className={`btn ${mode === 'list' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setMode('list')}>
          <List size={16} style={{ marginRight: '0.5rem' }} />Liste
        </button>
        <button className={`btn ${mode === 'backtest' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setMode('backtest')}>
          <Play size={16} style={{ marginRight: '0.5rem' }} />Tek Backtest
        </button>
        <button className={`btn ${mode === 'compare' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setMode('compare')}>
          <GitCompare size={16} style={{ marginRight: '0.5rem' }} />Karsilastir
        </button>
        <button className={`btn ${mode === 'top' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setMode('top')}>
          <Trophy size={16} style={{ marginRight: '0.5rem' }} />En Iyiler
        </button>
      </div>

      {mode === 'list' && (
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
            Mevcut Stratejiler ({strategies.length})
          </h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Anahtar</th>
                <th>Ad</th>
                <th>Parametreler</th>
                <th>Islem</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s, i) => (
                <tr key={s.key}>
                  <td>{i + 1}</td>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-blue)' }}>{s.key}</td>
                  <td style={{ fontWeight: 500 }}>{s.name}</td>
                  <td className="text-muted">{s.description}</td>
                  <td>
                    <button className="btn btn-outline" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      onClick={() => { setSelectedStrategy(s.key); setMode('backtest'); }}>
                      Test Et
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(mode === 'backtest' || mode === 'compare' || mode === 'top') && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Parametreler</h3>
          <div className="grid-4">
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Kaynak</label>
              <select className="select" value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="crypto">Kripto</option>
                <option value="forex">Forex</option>
              </select>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Sembol</label>
              <input className="input" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Zaman Dilimi</label>
              <select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </select>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Gun</label>
              <input className="input" type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
            </div>
          </div>

          {mode === 'backtest' && (
            <>
              <div className="grid-3" style={{ marginTop: '1rem' }}>
                <div>
                  <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Strateji</label>
                  <select className="select" value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)}>
                    <option value="">Seciniz...</option>
                    {strategies.map(s => <option key={s.key} value={s.key}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Stop Loss (%)</label>
                  <input className="input" type="number" step="0.01" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Take Profit (%)</label>
                  <input className="input" type="number" step="0.01" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} />
                </div>
              </div>
              <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={runBacktest} disabled={loading || !selectedStrategy}>
                {loading ? 'Calisiyor...' : 'Backtest Calistir'}
              </button>
            </>
          )}

          {(mode === 'compare' || mode === 'top') && (
            <>
              <div className="grid-2" style={{ marginTop: '1rem' }}>
                <div>
                  <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Stop Loss (%)</label>
                  <input className="input" type="number" step="0.01" value={stopLoss} onChange={(e) => setStopLoss(Number(e.target.value))} />
                </div>
                <div>
                  <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Take Profit (%)</label>
                  <input className="input" type="number" step="0.01" value={takeProfit} onChange={(e) => setTakeProfit(Number(e.target.value))} />
                </div>
              </div>
              <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={mode === 'compare' ? runCompare : runTop} disabled={loading}>
                {loading ? 'Calisiyor...' : mode === 'compare' ? 'Tum Stratejileri Karsilastir' : 'En Iyileri Bul'}
              </button>
            </>
          )}
        </div>
      )}

      {mode === 'backtest' && result && !result.error && (
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Backtest Sonuclari</h3>
          <div className="grid-4" style={{ marginBottom: '1rem' }}>
            <div className="stat-card">
              <span className="stat-label">Toplam Getiri</span>
              <span className={`stat-value ${result.total_return_pct >= 0 ? 'text-green' : 'text-red'}`}>
                {result.total_return_pct >= 0 ? '+' : ''}{result.total_return_pct?.toFixed(2)}%
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Max Drawdown</span>
              <span className="stat-value text-red">{result.max_drawdown_pct?.toFixed(2)}%</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Sharpe Ratio</span>
              <span className="stat-value text-blue">{result.sharpe_ratio?.toFixed(3)}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Kazanma Orani</span>
              <span className="stat-value text-yellow">{result.win_rate_pct?.toFixed(1)}%</span>
            </div>
          </div>
          <div className="grid-3">
            <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Strateji:</span> <strong>{result.strategy_name}</strong></div>
            <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Toplam Islem:</span> <strong>{result.total_trades}</strong></div>
            <div><span className="text-muted" style={{ fontSize: '0.75rem' }}>Son Bakiye:</span> <strong>${result.final_balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></div>
          </div>
        </div>
      )}

      {(mode === 'compare' || mode === 'top') && comparison.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
            {mode === 'top' ? 'En Iyi 5 Strateji' : 'Strateji Karsilastirmasi'}
          </h3>
          <div style={{ marginBottom: '1.5rem' }}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparison}>
                <XAxis dataKey="Strateji" stroke="#64748b" fontSize={10} angle={-45} textAnchor="end" height={100} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Bar dataKey="Getiri %" name="Getiri %">
                  {comparison.map((entry, i) => (
                    <Cell key={i} fill={parseFloat(entry['Getiri %']) >= 0 ? '#22c55e' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <table>
            <thead>
              <tr>
                {Object.keys(comparison[0]).map(key => <th key={key}>{key}</th>)}
              </tr>
            </thead>
            <tbody>
              {comparison.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val, j) => <td key={j}>{val as any}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
