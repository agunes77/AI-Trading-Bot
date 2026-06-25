import { useEffect, useState } from 'react';
import { aiApi } from '../services/api';
import { Brain, Play, Trash2, Database, Cpu, Clock, HardDrive } from 'lucide-react';

export default function AI() {
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);

  const [source, setSource] = useState('crypto');
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [algorithm, setAlgorithm] = useState('PPO');
  const [timeframe, setTimeframe] = useState('1h');
  const [days, setDays] = useState(365);
  const [timesteps, setTimesteps] = useState(100000);

  const loadModels = async () => {
    setLoading(true);
    try {
      const res = await aiApi.listModels();
      setModels(res.data.models || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadModels(); }, []);

  const startTraining = async () => {
    setTraining(true);
    setTrainResult(null);
    try {
      const res = await aiApi.train({ source, symbol, algorithm, timeframe, days, timesteps });
      setTrainResult(res.data);
      loadModels();
    } catch (e: any) {
      setTrainResult({ error: e.response?.data?.detail || 'Egitim hatasi' });
    } finally {
      setTraining(false);
    }
  };

  const deleteModel = async (name: string) => {
    if (!confirm(`"${name}" modelini silmek istediginize emin misiniz?`)) return;
    try {
      await aiApi.deleteModel(name);
      loadModels();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>AI Model Egitimi</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>Reinforcement Learning agent egitin ve yonetin</p>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} color="var(--accent-purple)" />
            Egitim Parametreleri
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Kaynak</label>
                <select className="select" value={source} onChange={(e) => setSource(e.target.value)}>
                  <option value="crypto">Kripto</option>
                  <option value="forex">Forex</option>
                </select>
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Sembol</label>
                <input className="input" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
              </div>
            </div>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Algoritma</label>
                <select className="select" value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
                  <option value="PPO">PPO (Proximal Policy Optimization)</option>
                  <option value="DQN">DQN (Deep Q-Network)</option>
                  <option value="A2C">A2C (Advantage Actor-Critic)</option>
                </select>
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Zaman Dilimi</label>
                <select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                  <option value="15m">15 dakika</option>
                  <option value="1h">1 saat</option>
                  <option value="4h">4 saat</option>
                  <option value="1d">1 gun</option>
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Gecmis Veri (Gun)</label>
                <input className="input" type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Egitim Adimi</label>
                <input className="input" type="number" value={timesteps} onChange={(e) => setTimesteps(Number(e.target.value))} />
              </div>
            </div>
            <button className="btn btn-primary" onClick={startTraining} disabled={training} style={{ width: '100%', padding: '0.75rem' }}>
              {training ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <div style={{ width: 16, height: 16, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                  Egitim Devam Ediyor...
                </span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <Play size={16} /> Egitimi Baslat
                </span>
              )}
            </button>
          </div>

          {trainResult && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: trainResult.error ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)', borderRadius: 8 }}>
              {trainResult.error ? (
                <p className="text-red">{trainResult.error}</p>
              ) : (
                <>
                  <p className="text-green" style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{trainResult.message}</p>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    <div>Egitim Verisi: {trainResult.train_size} satir</div>
                    <div>Dogrulama Verisi: {trainResult.eval_size} satir</div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Brain size={18} color="var(--accent-blue)" />
            Algoritma Bilgisi
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>PPO (Proximal Policy Optimization)</div>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                En populer ve stabil RL algoritmasi. Surekli ve kesikli aksiyon alanlarinda calisir.
                Finansal piyasalar icin onerilir.
              </p>
            </div>
            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>DQN (Deep Q-Network)</div>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                Kesikli aksiyon alanlari icin uygun. Buyuk/satis/bekle gibi kararlar icin kullanilir.
                Daha basit ama etkili.
              </p>
            </div>
            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>A2C (Advantage Actor-Critic)</div>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                PPO'nun daha hizli ama daha az stabil versiyonu. Hizli prototipleme icin uygun.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={18} color="var(--accent-green)" />
          Kayitli Modeller ({models.length})
        </h3>
        {loading ? (
          <div className="loading">Yukleniyor...</div>
        ) : models.length === 0 ? (
          <div className="empty-state">
            <Database size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
            <p>Henuz kayitli model yok</p>
            <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Egitim baslattiginizda modeller burada gorunecek
            </p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Model Adi</th>
                <th>Boyut</th>
                <th>Olusturulma</th>
                <th>Islem</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.name}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Brain size={16} color="var(--accent-purple)" />
                      <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>{m.name}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <HardDrive size={14} className="text-muted" />
                      {m.size_mb?.toFixed(2)} MB
                    </span>
                  </td>
                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={14} className="text-muted" />
                      {new Date(m.created_at).toLocaleString('tr-TR')}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-danger" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      onClick={() => deleteModel(m.name)}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
