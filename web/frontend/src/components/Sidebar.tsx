import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Brain,
  History,
  Activity,
  Database,
  Users,
  Blocks,
} from 'lucide-react';

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/prices', icon: TrendingUp, label: 'Canli Fiyatlar' },
  { to: '/chart', icon: BarChart3, label: 'Grafik & Analiz' },
  { to: '/strategies', icon: Activity, label: 'Stratejiler' },
  { to: '/builder', icon: Blocks, label: 'Strateji Tasarimcisi' },
  { to: '/data', icon: Database, label: 'Veri Yonetimi' },
  { to: '/trading-agents', icon: Users, label: 'TradingAgents LLM' },
  { to: '/trades', icon: History, label: 'Trade Gecmisi' },
  { to: '/ai', icon: Brain, label: 'AI Model Egitimi' },
];

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8,
            background: 'linear-gradient(135deg, #3b82f6, #a855f7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <TrendingUp size={20} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>AI Trader</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>v1.0</div>
          </div>
        </div>
      </div>

      <nav>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <link.icon size={18} />
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div style={{ position: 'absolute', bottom: '1.5rem', left: 0, right: 0, padding: '0 1.5rem' }}>
        <div style={{
          padding: '0.75rem',
          background: 'var(--bg-primary)',
          borderRadius: 8,
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-green)' }} />
            Sistem Aktif
          </div>
          <div>Binance + MT5</div>
        </div>
      </div>
    </div>
  );
}
