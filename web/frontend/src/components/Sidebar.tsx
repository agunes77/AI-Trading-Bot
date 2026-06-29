import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, BarChart3, Brain, History,
  Activity, Database, Users, Blocks, Bot, Code2
} from 'lucide-react';

const tradingLinks = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/prices', icon: TrendingUp, label: 'Canlı Fiyatlar' },
  { to: '/chart', icon: BarChart3, label: 'Grafik & Analiz' },
];

const strategyLinks = [
  { to: '/strategies', icon: Activity, label: 'Stratejiler' },
  { to: '/builder', icon: Blocks, label: 'Strateji Tasarımcısı' },
  { to: '/pine-script', icon: Code2, label: 'Pine Script Editör' },
  { to: '/trading-agents', icon: Users, label: 'TradingAgents LLM' },
];

const systemLinks = [
  { to: '/trades', icon: History, label: 'Trade Geçmişi' },
  { to: '/data', icon: Database, label: 'Veri Yönetimi' },
  { to: '/ai', icon: Brain, label: 'AI Model Eğitimi' },
];

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div style={{ padding: '0 1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: 'var(--accent-blue)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Bot size={20} color="white" />
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', whiteSpace: 'nowrap' }}>AI Trading</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>v2.0 Professional</div>
          </div>
        </div>
      </div>

      <div style={{ paddingLeft: '1rem', marginTop: '1rem', marginBottom: '0.3rem', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        TRADING
      </div>
      <nav>
        {tradingLinks.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.to === '/'} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <link.icon size={16} />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{ paddingLeft: '1rem', marginTop: '1rem', marginBottom: '0.3rem', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        STRATEJİ
      </div>
      <nav>
        {strategyLinks.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.to === '/'} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <link.icon size={16} />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{ paddingLeft: '1rem', marginTop: '1rem', marginBottom: '0.3rem', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        SİSTEM
      </div>
      <nav>
        {systemLinks.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.to === '/'} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <link.icon size={16} />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{ marginTop: 'auto', padding: '0 1rem' }}>
        <div style={{
          padding: '0.75rem',
          background: 'var(--bg-primary)',
          borderRadius: 6,
          fontSize: '0.7rem',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-color)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.3rem', fontWeight: 600 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 4px var(--accent-green)' }} />
            Çalışıyor
          </div>
          <div style={{ color: 'var(--text-muted)' }}>Binance • MT5</div>
        </div>
      </div>
    </div>
  );
}