import { useState, useEffect } from 'react';
import { Brain, Play, Users, TrendingUp, MessageCircle, Newspaper, BarChart2, ArrowUp, ArrowDown, Briefcase, Shield, Award } from 'lucide-react';
import { tradingAgentsApi } from '../services/api';

interface AgentInfo {
  name: string;
  role: string;
  icon: string;
}

export default function TradingAgentsPage() {
  const [status, setStatus] = useState<any>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [form, setForm] = useState({
    ticker: 'AAPL',
    date: new Date().toISOString().split('T')[0],
    llm_provider: 'openai',
    deep_think_model: '',
    quick_think_model: '',
    max_debate_rounds: 2
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statusRes, providersRes, agentsRes] = await Promise.all([
        tradingAgentsApi.getStatus(),
        tradingAgentsApi.getProviders(),
        tradingAgentsApi.getAgents()
      ]);
      setStatus(statusRes.data);
      setProviders(providersRes.data.providers);
      setAgents(agentsRes.data.agents);
    } catch (error) {
      console.error('Veri yukleme hatasi:', error);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setResult(null);
    try {
      const res = await tradingAgentsApi.analyze({
        ticker: form.ticker,
        date: form.date,
        llm_provider: form.llm_provider,
        deep_think_model: form.deep_think_model || undefined,
        quick_think_model: form.quick_think_model || undefined,
        max_debate_rounds: form.max_debate_rounds
      });
      setResult(res.data);
    } catch (error) {
      console.error('Analiz hatasi:', error);
      alert('Analiz hatasi: ' + (error as any).message);
    } finally {
      setAnalyzing(false);
    }
  };

  const getAgentIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      'trending-up': TrendingUp,
      'message-circle': MessageCircle,
      'newspaper': Newspaper,
      'bar-chart-2': BarChart2,
      'arrow-up': ArrowUp,
      'arrow-down': ArrowDown,
      'briefcase': Briefcase,
      'shield': Shield,
      'award': Award
    };
    const Icon = icons[iconName] || Brain;
    return <Icon size={16} />;
  };

  const getDecisionColor = (decision: string) => {
    if (decision === 'BUY') return 'badge-green';
    if (decision === 'SELL') return 'badge-red';
    return 'badge-yellow';
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>TradingAgents LLM</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            Multi-agent LLM karar motoru
          </p>
        </div>
        <span className={`badge ${status?.available ? 'badge-green' : 'badge-red'}`}>
          {status?.available ? 'Hazir' : 'Degil'}
        </span>
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Agent Sayisi</span>
            <Users size={20} color="var(--accent-blue)" />
          </div>
          <span className="stat-value">{agents.length}</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">LLM Provider</span>
            <Brain size={20} color="var(--accent-purple)" />
          </div>
          <span className="stat-value">{providers.length}</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Durum</span>
            <Play size={20} color="var(--accent-green)" />
          </div>
          <span className="stat-value" style={{ fontSize: '1rem' }}>
            {status?.available ? 'Aktif' : 'Pasif'}
          </span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Framework</span>
            <Brain size={20} color="var(--accent-yellow)" />
          </div>
          <span className="stat-value" style={{ fontSize: '1rem' }}>LangGraph</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Brain size={18} color="var(--accent-purple)" />
            LLM Analizi
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Sembol</label>
                <input
                  className="input"
                  value={form.ticker}
                  onChange={(e) => setForm({ ...form, ticker: e.target.value })}
                  placeholder="AAPL, BTC-USD, EURUSD..."
                />
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Tarih</label>
                <input
                  className="input"
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>LLM Provider</label>
              <select
                className="select"
                value={form.llm_provider}
                onChange={(e) => setForm({ ...form, llm_provider: e.target.value })}
              >
                {providers.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Deep Think Model (opsiyonel)</label>
                <input
                  className="input"
                  value={form.deep_think_model}
                  onChange={(e) => setForm({ ...form, deep_think_model: e.target.value })}
                  placeholder="gpt-5.5, claude-opus-4-8..."
                />
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Quick Think Model (opsiyonel)</label>
                <input
                  className="input"
                  value={form.quick_think_model}
                  onChange={(e) => setForm({ ...form, quick_think_model: e.target.value })}
                  placeholder="gpt-5.4-mini..."
                />
              </div>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Maksimum Tartisma Turu</label>
              <input
                className="input"
                type="number"
                min="1"
                max="5"
                value={form.max_debate_rounds}
                onChange={(e) => setForm({ ...form, max_debate_rounds: parseInt(e.target.value) })}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={analyzing || !status?.available}
              style={{ width: '100%', padding: '0.75rem' }}
            >
              {analyzing ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <div style={{ width: 16, height: 16, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                  Analiz Yapiliyor...
                </span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <Brain size={16} /> Analiz Baslat
                </span>
              )}
            </button>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Users size={18} color="var(--accent-blue)" />
            Agent Mimarisi
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {agents.map((agent, i) => (
              <div key={i} style={{
                padding: '0.75rem',
                background: 'var(--bg-primary)',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: 6,
                  background: 'var(--accent-blue)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  flexShrink: 0
                }}>
                  {getAgentIcon(agent.icon)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{agent.name}</div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>{agent.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {result && (
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={18} color="var(--accent-yellow)" />
            Analiz Sonucu
          </h3>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.ticker}</span>
              <span className={`badge ${getDecisionColor(result.decision)}`} style={{ fontSize: '1rem', padding: '0.5rem 1rem' }}>
                {result.decision}
              </span>
              <span className="text-muted" style={{ fontSize: '0.85rem' }}>{result.date}</span>
            </div>
          </div>

          {result.state && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Object.entries(result.state).map(([key, value]) => (
                <div key={key} style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem', textTransform: 'capitalize' }}>
                    {key.replace(/_/g, ' ')}
                  </div>
                  <pre style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}

          {result.error && (
            <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.1)', borderRadius: 8 }}>
              <span className="text-red">{result.error}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
