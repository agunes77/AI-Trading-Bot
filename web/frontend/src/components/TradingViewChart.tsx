import { useEffect, useRef, memo } from 'react';

interface TradingViewChartProps {
  symbol: string;
  theme?: 'light' | 'dark';
  interval?: string;
  studies?: string[];
  height?: number;
}

function TradingViewChart({
  symbol,
  theme = 'dark',
  interval = '60',
  studies = ['RSI@tv-basicstudies', 'MACD@tv-basicstudies'],
}: TradingViewChartProps) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;

    container.current.innerHTML = '<div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>';

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: symbol,
      interval: interval,
      timezone: 'Europe/Istanbul',
      theme: theme,
      style: '1',
      locale: 'tr',
      toolbar_bg: '#1e293b',
      enable_publishing: false,
      allow_symbol_change: true,
      hide_side_toolbar: false,
      withdateranges: true,
      details: false,
      studies: studies,
      backgroundColor: '#0f172a',
      gridColor: '#334155',
      support_host: 'https://www.tradingview.com',
    });

    container.current.appendChild(script);
  }, [symbol, theme, interval, JSON.stringify(studies)]);

  return (
    <div
      className="tradingview-widget-container"
      ref={container}
      style={{ height: `calc(100vh - 8rem)`, width: '100%' }}
    />
  );
}

export default memo(TradingViewChart);