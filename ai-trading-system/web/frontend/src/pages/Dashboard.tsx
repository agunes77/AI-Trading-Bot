import { useEffect, useState } from 'react';
import { dashboardApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { TrendingUp, TrendingDown, Activity, Wallet, BarChart3 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#a855f7', '#ef4444', '#06b6d4'];

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [market, setMarket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { data: livePrices } = useWebSocket('ws://localhost:8000/ws/prices');

  useEffect(() => {
    Promise.all([
      dashboardApi.getSummary(),
      dashboardApi.getMarketOverview(),
    ]).then(([s, m]) => {
      setSummary(s.data);
      setMarket(m.data);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Yukleniyor...</div>;

  const portfolio = summary?.portfolio;
  const markets = market?.markets || [];
  const isProfit = (portfolio?.total_pnl || 0) >= 0;

  const equityData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    value: 10000 + Math.random() * 500 * (i + 1) + (Math.random() - 0.5) * 200,
  }));

  const pieData = portfolio?.assets?.length > 0
    ? portfolio.assets.map((a: any) => ({ name: a.symbol, value: a.amount }))
    : [{ name: 'USDT', value: 10000 }];

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Dashboard</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Portfoy ozeti ve piyasa durumu</p>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Toplam Bakiye</span>
            <Wallet size={20} color="var(--accent-blue)" />
          </div>
          <span className="stat-value">${(portfolio?.total_balance || 10000).toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          <span className={`badge ${isProfit ? 'badge-green' : 'badge-red'}`}>
            {isProfit ? '+' : ''}{portfolio?.total_pnl_pct?.toFixed(2) || '0.00'}%
          </span>
        </div>

        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Toplam PnL</span>
            {isProfit ? <TrendingUp size={20} color="var(--accent-green)" /> : <TrendingDown size={20} color="var(--accent-red)" />}
          </div>
          <span className={`stat-value ${isProfit ? 'text-green' : 'text-red'}`}>
            {isProfit ? '+' : ''}${(portfolio?.total_pnl || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-muted" style={{ fontSize: '0.75rem' }}>Baslangictan bu yana</span>
        </div>

        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Acik Pozisyonlar</span>
            <Activity size={20} color="var(--accent-yellow)" />
          </div>
          <span className="stat-value">{portfolio?.open_positions || 0}</span>
          <span className="text-muted" style={{ fontSize: '0.75rem' }}>Aktif islem</span>
        </div>

        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Bugun PnL</span>
            <BarChart3 size={20} color="var(--accent-purple)" />
          </div>
          <span className="stat-value text-green">+$0.00</span>
          <span className="text-muted" style={{ fontSize: '0.75rem' }}>Gunluk performans</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Varilik Egrisi</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={equityData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorValue)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Varlik Dagilimi</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={2}>
                {pieData.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center' }}>
            {pieData.map((d: any, i: number) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}>
                <div style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length] }} />
                {d.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Piyasa Ozeti</h3>
        <table>
          <thead>
            <tr>
              <th>Sembol</th>
              <th>Fiyat</th>
              <th>24s Degisim</th>
              <th>24s Hacim</th>
              <th>24s Yuksek</th>
              <th>24s Dusuk</th>
            </tr>
          </thead>
          <tbody>
            {markets.length > 0 ? markets.map((m: any) => {
              const live = livePrices[m.symbol];
              const price = live?.price || m.price;
              const change = live?.change_24h || m.change_24h;
              return (
                <tr key={m.symbol}>
                  <td style={{ fontWeight: 600 }}>{m.symbol}</td>
                  <td>${price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td className={change >= 0 ? 'text-green' : 'text-red'}>
                    {change >= 0 ? '+' : ''}{change?.toFixed(2)}%
                  </td>
                  <td>${(m.volume_24h / 1e6)?.toFixed(1)}M</td>
                  <td>${m.high_24h?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>${m.low_24h?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                </tr>
              );
            }) : (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Piyasa verisi yuklenemedi</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
