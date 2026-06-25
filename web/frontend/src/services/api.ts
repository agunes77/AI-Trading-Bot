import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary'),
  getPortfolio: () => api.get('/dashboard/portfolio'),
  getMarketOverview: () => api.get('/dashboard/market-overview'),
};

export const pricesApi = {
  getCrypto: (symbol: string, timeframe?: string, limit?: number) =>
    api.get(`/prices/crypto/${encodeURIComponent(symbol)}`, { params: { timeframe, limit } }),
  getForex: (symbol: string, timeframe?: string, limit?: number) =>
    api.get(`/prices/forex/${encodeURIComponent(symbol)}`, { params: { timeframe, limit } }),
  getTicker: (symbol: string, source?: string) =>
    api.get(`/prices/ticker/${encodeURIComponent(symbol)}`, { params: { source } }),
  getOrderbook: (symbol: string, limit?: number) =>
    api.get(`/prices/orderbook/${encodeURIComponent(symbol)}`, { params: { limit } }),
};

export const strategiesApi = {
  list: () => api.get('/strategies/list'),
  backtest: (data: any) => api.post('/strategies/backtest', data),
  compare: (data: any) => api.post('/strategies/compare', data),
  top: (data: any) => api.post('/strategies/top', data),
};

export const tradesApi = {
  getHistory: (limit?: number) => api.get('/trades/history', { params: { limit } }),
  getOpenPositions: () => api.get('/trades/open-positions'),
  getPerformance: () => api.get('/trades/performance'),
};

export const aiApi = {
  listModels: () => api.get('/ai/models'),
  train: (data: any) => api.post('/ai/train', data),
  getModel: (name: string) => api.get(`/ai/model/${name}`),
  deleteModel: (name: string) => api.delete(`/ai/model/${name}`),
};

export const dataApi = {
  getSources: () => api.get('/data/sources'),
  getDukascopyInstruments: () => api.get('/data/dukascopy/instruments'),
  download: (data: any) => api.post('/data/download', data),
  getDownloaded: () => api.get('/data/downloaded'),
  getSourceData: (source: string) => api.get(`/data/downloaded/${source}`),
  deleteData: (source: string, filename: string) => api.delete(`/data/downloaded/${source}/${filename}`),
  preview: (source: string, filename: string, rows?: number) => api.get(`/data/preview/${source}/${filename}`, { params: { rows } }),
};

export const tradingAgentsApi = {
  getStatus: () => api.get('/trading-agents/status'),
  getProviders: () => api.get('/trading-agents/providers'),
  getAgents: () => api.get('/trading-agents/agents'),
  analyze: (data: any) => api.post('/trading-agents/analyze', data),
  execute: (data: any) => api.post('/trading-agents/execute', data),
};

export const strategyBuilderApi = {
  getNodes: () => api.get('/strategy-builder/nodes'),
  getStrategies: () => api.get('/strategy-builder/strategies'),
  getStrategy: (id: string) => api.get(`/strategy-builder/strategies/${id}`),
  saveStrategy: (data: any) => api.post('/strategy-builder/strategies', data),
  updateStrategy: (id: string, data: any) => api.put(`/strategy-builder/strategies/${id}`, data),
  deleteStrategy: (id: string) => api.delete(`/strategy-builder/strategies/${id}`),
  runStrategy: (data: any) => api.post('/strategy-builder/run', data),
  runSavedStrategy: (id: string, data: any) => api.post(`/strategy-builder/strategies/${id}/run`, data),
  runPineScript: (data: any) => api.post('/strategy-builder/pine/run', data),
  parsePineScript: (data: any) => api.post('/strategy-builder/pine/parse', data),
  getPinePresets: () => api.get('/strategy-builder/pine/presets'),
  getPinePreset: (name: string) => api.get(`/strategy-builder/pine/presets/${name}`),
};

export default api;
