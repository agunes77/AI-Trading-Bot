import { useEffect, useRef, useState } from 'react';

interface PriceUpdate {
  type: string;
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [data, setData] = useState<Record<string, PriceUpdate>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'price_update') {
          setData((prev) => ({ ...prev, [msg.symbol]: msg }));
        }
      } catch (e) {}
    };

    return () => {
      ws.close();
    };
  }, [url]);

  return { data, connected };
}
