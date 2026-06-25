import { useEffect, useState } from 'react';
import { tradesApi } from '../services/api';
import { History, TrendingUp, DollarSign, Target, Award } from 'lucide-react';

export default function Trades() {
  const [history, setHistory] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      tradesApi.getHistory(50),
      tradesApi.getOpenPositions(),
      tradesApi.getPerformance(),
    ]).then(([h, p, perf]) => {
      setHistory(h.data.trades || []);
      setPositions(p.data.positions || []);
      setPerformance(perf.data);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Yukleniyor...</div>;

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Trade Gecmisi</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Islem gecmisi ve performans analizi</p>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Toplam Islem</span>
            <History size={20} color="var(--accent-blue)" />
          </div>
          <span className="stat-value">{performance?.total_trades || 0}</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Kazanma Orani</span>
            <Target size={20} color="var(--accent-green)" />
          </div>
          <span className="stat-value text-green">{(performance?.win_rate || 0).toFixed(1)}%</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Toplam PnL</span>
            <DollarSign size={20} color="var(--accent-purple)" />
          </div>
          <span className={`stat-value ${(performance?.total_pnl || 0) >= 0 ? 'text-green' : 'text-red'}`}>
            ${(performance?.total_pnl || 0).toFixed(2)}
          </span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Profit Factor</span>
            <Award size={20} color="var(--accent-yellow)" />
          </div>
          <span className="stat-value">{(performance?.profit_factor || 0).toFixed(2)}</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Performans Detaylari</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { label: 'Kazanan Islem', value: performance?.winning_trades || 0, color: 'text-green' },
              { label: 'Kaybeden Islem', value: performance?.losing_trades || 0, color: 'text-red' },
              { label: 'Ortalama Kazanc', value: `${(performance?.avg_win || 0).toFixed(2)}%`, color: 'text-green' },
              { label: 'Ortalama Kayip', value: `${(performance?.avg_loss || 0).toFixed(2)}%`, color: 'text-red' },
              { label: 'Sharpe Ratio', value: (performance?.sharpe_ratio || 0).toFixed(3), color: 'text-blue' },
              { label: 'Max Drawdown', value: `${(performance?.max_drawdown || 0).toFixed(2)}%`, color: 'text-red' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted">{item.label}</span>
                <span className={item.color} style={{ fontWeight: 600, fontFamily: 'monospace' }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Acik Pozisyonlar</h3>
          {positions.length === 0 ? (
            <div className="empty-state">
              <TrendingUp size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
              <p>Acik pozisyon yok</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Sembol</th>
                  <th>Miktar</th>
                  <th>Deger</th>
                  <th>24s</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((p, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 600 }}>{p.symbol}</td>
                    <td style={{ fontFamily: 'monospace' }}>{p.amount?.toFixed(4)}</td>
                    <td style={{ fontFamily: 'monospace' }}>${p.value?.toFixed(2)}</td>
                    <td className={p.change_24h >= 0 ? 'text-green' : 'text-red'}>
                      {p.change_24h >= 0 ? '+' : ''}{p.change_24h?.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Islem Gecmisi</h3>
        {history.length === 0 ? (
          <div className="empty-state">
            <History size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
            <p>Henuz islem gecmisi yok</p>
            <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Canli trade baslatildiginda islemler burada gorunecek
            </p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tarih</th>
                <th>Sembol</th>
                <th>Yon</th>
                <th>Fiyat</th>
                <th>Miktar</th>
                <th>PnL</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              {history.map((t, i) => (
                <tr key={i}>
                  <td className="text-muted">{new Date(t.timestamp).toLocaleString('tr-TR')}</td>
                  <td style={{ fontWeight: 600 }}>{t.symbol}</td>
                  <td>
                    <span className={`badge ${t.side === 'buy' ? 'badge-green' : 'badge-red'}`}>
                      {t.side === 'buy' ? 'ALIS' : 'SATIS'}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace' }}>${t.price?.toFixed(2)}</td>
                  <td style={{ fontFamily: 'monospace' }}>{t.amount?.toFixed(4)}</td>
                  <td className={t.pnl >= 0 ? 'text-green' : 'text-red'} style={{ fontFamily: 'monospace' }}>
                    {t.pnl >= 0 ? '+' : ''}${t.pnl?.toFixed(2)}
                  </td>
                  <td><span className="badge badge-blue">{t.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
