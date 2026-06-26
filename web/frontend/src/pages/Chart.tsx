import { useState } from 'react';
import TradingViewChart from '../components/TradingViewChart';

export default function Chart() {
  const [symbol, setSymbol] = useState('BINANCE:BTCUSDT');
  const [interval, setInterval] = useState('60');
  const [studies, setStudies] = useState<string[]>(['RSI@tv-basicstudies', 'MACD@tv-basicstudies']);

  const symbols = [
    { value: 'BINANCE:BTCUSDT', label: 'Bitcoin (BTC/USDT)' },
    { value: 'BINANCE:ETHUSDT', label: 'Ethereum (ETH/USDT)' },
    { value: 'BINANCE:BNBUSDT', label: 'BNB/USDT' },
    { value: 'BINANCE:SOLUSDT', label: 'Solana (SOL/USDT)' },
    { value: 'BINANCE:XRPUSDT', label: 'Ripple (XRP/USDT)' },
    { value: 'BINANCE:ADAUSDT', label: 'Cardano (ADA/USDT)' },
    { value: 'BINANCE:DOGEUSDT', label: 'Dogecoin (DOGE/USDT)' },
    { value: 'OANDA:EURUSD', label: 'EUR/USD (Forex)' },
    { value: 'OANDA:GBPUSD', label: 'GBP/USD (Forex)' },
    { value: 'OANDA:USDJPY', label: 'USD/JPY (Forex)' },
    { value: 'OANDA:XAUUSD', label: 'Altın (XAU/USD)' },
  ];

  const intervals = [
    { value: '1', label: '1dk' },
    { value: '5', label: '5dk' },
    { value: '15', label: '15dk' },
    { value: '30', label: '30dk' },
    { value: '60', label: '1s' },
    { value: '240', label: '4s' },
    { value: 'D', label: '1g' },
    { value: 'W', label: '1h' },
  ];

  const availableStudies = [
    { value: 'RSI@tv-basicstudies', label: 'RSI' },
    { value: 'MACD@tv-basicstudies', label: 'MACD' },
    { value: 'Stochastic@tv-basicstudies', label: 'Stochastic' },
    { value: 'BB@tv-basicstudies', label: 'Bollinger Bands' },
    { value: 'Volume@tv-basicstudies', label: 'Volume' },
    { value: 'EMA@tv-basicstudies', label: 'EMA' },
    { value: 'IchimokuCloud@tv-basicstudies', label: 'Ichimoku' },
    { value: 'ADX@tv-basicstudies', label: 'ADX' },
    { value: 'ATR@tv-basicstudies', label: 'ATR' },
    { value: 'Supertrend@tv-basicstudies', label: 'Supertrend' },
  ];

  const toggleStudy = (study: string) => {
    setStudies(prev =>
      prev.includes(study)
        ? prev.filter(s => s !== study)
        : [...prev, study]
    );
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Grafik & Analiz</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            TradingView Professional Charting
          </p>
        </div>
      </div>

      <div style={{
        display: 'flex',
        gap: '0.75rem',
        marginBottom: '1rem',
        flexWrap: 'wrap',
        alignItems: 'center',
        padding: '0.75rem',
        background: 'var(--bg-card)',
        borderRadius: 10,
      }}>
        <select
          className="select"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          style={{ width: 220 }}
        >
          {symbols.map(s => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>

        <div style={{ display: 'flex', gap: '0.25rem' }}>
          {intervals.map(tf => (
            <button
              key={tf.value}
              onClick={() => setInterval(tf.value)}
              style={{
                padding: '0.4rem 0.75rem',
                borderRadius: 6,
                border: interval === tf.value ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                background: interval === tf.value ? 'var(--accent-blue)' : 'var(--bg-primary)',
                color: interval === tf.value ? 'white' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 500,
              }}
            >
              {tf.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {availableStudies.map(s => (
            <button
              key={s.value}
              onClick={() => toggleStudy(s.value)}
              style={{
                padding: '0.3rem 0.6rem',
                borderRadius: 5,
                border: studies.includes(s.value) ? '1px solid var(--accent-green)' : '1px solid var(--border-color)',
                background: studies.includes(s.value) ? 'rgba(34,197,94,0.15)' : 'var(--bg-primary)',
                color: studies.includes(s.value) ? 'var(--accent-green)' : 'var(--text-secondary)',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 12,
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
      }}>
        <TradingViewChart
          symbol={symbol}
          interval={interval}
          studies={studies}
        />
      </div>
    </div>
  );
}