import { useEffect, useState } from 'react';
import { pricesApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { RefreshCw, Search } from 'lucide-react';

export default function Prices() {
  const [marketData, setMarketData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const { data: livePrices, connected } = useWebSocket('ws://localhost:8000/ws/prices');

  const loadMarket = async () => {
    setLoading(true);
    try {
      const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT', 'DOT/USDT'];
      const results = await Promise.all(symbols.map(s => pricesApi.getTicker(s, 'crypto').catch(() => null)));
      const data = results.filter(Boolean).map((r: any) => ({
        symbol: r.data.symbol,
        price: r.data.ticker?.last || 0,
        change: r.data.ticker?.percentage || 0,
        volume: r.data.ticker?.quoteVolume || 0,
        high: r.data.ticker?.high || 0,
        low: r.data.ticker?.low || 0,
        bid: r.data.ticker?.bid || 0,
        ask: r.data.ticker?.ask || 0,
      }));
      setMarketData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadMarket(); }, []);

  const filtered = marketData.filter(m => m.symbol.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Canli Fiyatlar</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            Gercek zamanli piyasa verileri
            <span style={{ marginLeft: '0.5rem' }}>
              <span className={`badge ${connected ? 'badge-green' : 'badge-red'}`}>
                {connected ? 'Canli' : 'Baglanti Yok'}
              </span>
            </span>
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadMarket}>
          <RefreshCw size={16} style={{ marginRight: '0.5rem' }} />
          Yenile
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem', position: 'relative', maxWidth: 300 }}>
        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
        <input
          className="input"
          placeholder="Sembol ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: '2.5rem' }}
        />
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {filtered.slice(0, 4).map((m) => {
          const live = livePrices[m.symbol];
          const price = live?.price || m.price;
          const change = live?.change_24h || m.change;
          return (
            <div className="card stat-card" key={m.symbol}>
              <span className="stat-label">{m.symbol}</span>
              <span className="stat-value" style={{ fontSize: '1.25rem' }}>
                ${price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
              <span className={`badge ${change >= 0 ? 'badge-green' : 'badge-red'}`}>
                {change >= 0 ? '+' : ''}{change?.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>Tum Piyasalar</h3>
        {loading ? (
          <div className="loading">Yukleniyor...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Sembol</th>
                <th>Fiyat</th>
                <th>24s Degisim</th>
                <th>Bid</th>
                <th>Ask</th>
                <th>24s Hacim</th>
                <th>24s Yuksek</th>
                <th>24s Dusuk</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m) => {
                const live = livePrices[m.symbol];
                const price = live?.price || m.price;
                const change = live?.change_24h || m.change;
                return (
                  <tr key={m.symbol}>
                    <td style={{ fontWeight: 600 }}>{m.symbol}</td>
                    <td style={{ fontFamily: 'monospace' }}>${price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className={change >= 0 ? 'text-green' : 'text-red'} style={{ fontFamily: 'monospace' }}>
                      {change >= 0 ? '+' : ''}{change?.toFixed(2)}%
                    </td>
                    <td style={{ fontFamily: 'monospace' }}>${m.bid?.toFixed(2)}</td>
                    <td style={{ fontFamily: 'monospace' }}>${m.ask?.toFixed(2)}</td>
                    <td>${(m.volume / 1e6)?.toFixed(1)}M</td>
                    <td>${m.high?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${m.low?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
