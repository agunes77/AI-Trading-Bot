import { useState, useEffect } from 'react';
import { Database, Download, Trash2, Eye, RefreshCw, HardDrive } from 'lucide-react';
import { dataApi } from '../services/api';

interface DataFile {
  filename: string;
  path: string;
  size_mb: number;
  created: string;
  modified: string;
}

interface DataSource {
  id: string;
  name: string;
  description: string;
  instruments_count: number;
  since_year: number;
  formats: string[];
  timeframes: string[];
}

export default function DataManagement() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [downloadedData, setDownloadedData] = useState<Record<string, DataFile[]>>({});
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const [downloadForm, setDownloadForm] = useState({
    source: 'dukascopy',
    instrument: 'EURUSD',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    timeframe: 'hourly'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sourcesRes, dataRes] = await Promise.all([
        dataApi.getSources(),
        dataApi.getDownloaded()
      ]);
      setSources(sourcesRes.data.sources);
      setDownloadedData(dataRes.data);
    } catch (error) {
      console.error('Veri yukleme hatasi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await dataApi.download(downloadForm);
      alert('Indirme baslatildi. Arka planda devam ediyor.');
      setTimeout(loadData, 2000);
    } catch (error) {
      console.error('Indirme hatasi:', error);
      alert('Indirme hatasi: ' + (error as any).message);
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async (source: string, filename: string) => {
    if (!confirm(`"${filename}" silinecek. Emin misiniz?`)) return;
    
    try {
      await dataApi.deleteData(source, filename);
      loadData();
    } catch (error) {
      console.error('Silme hatasi:', error);
      alert('Silme hatasi: ' + (error as any).message);
    }
  };

  const handlePreview = async (source: string, filename: string) => {
    setPreviewLoading(true);
    try {
      const res = await dataApi.preview(source, filename, 50);
      setPreview(res.data);
    } catch (error) {
      console.error('Onizleme hatasi:', error);
      alert('Onizleme hatasi: ' + (error as any).message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const allFiles = Object.entries(downloadedData).flatMap(([source, files]) =>
    files.map(f => ({ ...f, source }))
  );

  const totalSize = allFiles.reduce((sum, f) => sum + f.size_mb, 0);

  return (
    <div>
      <div className="header">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Veri Yonetimi</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            Gecmis veri indirme ve yonetim
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadData}>
          <RefreshCw size={16} style={{ marginRight: '0.5rem' }} />
          Yenile
        </button>
      </div>

      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Veri Kaynaklari</span>
            <Database size={20} color="var(--accent-blue)" />
          </div>
          <span className="stat-value">{sources.length}</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Indirilen Dosyalar</span>
            <HardDrive size={20} color="var(--accent-green)" />
          </div>
          <span className="stat-value">{allFiles.length}</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Toplam Boyut</span>
            <Database size={20} color="var(--accent-purple)" />
          </div>
          <span className="stat-value">{totalSize.toFixed(1)} MB</span>
        </div>
        <div className="card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Dukascopy Destek</span>
            <Download size={20} color="var(--accent-yellow)" />
          </div>
          <span className="stat-value">1000+</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Download size={18} color="var(--accent-blue)" />
            Veri Indir
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Kaynak</label>
              <select
                className="select"
                value={downloadForm.source}
                onChange={(e) => setDownloadForm({ ...downloadForm, source: e.target.value })}
              >
                {sources.map(s => (
                  <option key={s.id} value={s.id}>{s.name} - {s.description}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Enstruman</label>
              <input
                className="input"
                value={downloadForm.instrument}
                onChange={(e) => setDownloadForm({ ...downloadForm, instrument: e.target.value })}
                placeholder="EURUSD, BTCUSD, AAPL..."
              />
            </div>
            <div className="grid-2">
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Baslangic Tarihi</label>
                <input
                  className="input"
                  type="date"
                  value={downloadForm.start_date}
                  onChange={(e) => setDownloadForm({ ...downloadForm, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Bitis Tarihi</label>
                <input
                  className="input"
                  type="date"
                  value={downloadForm.end_date}
                  onChange={(e) => setDownloadForm({ ...downloadForm, end_date: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="text-muted" style={{ fontSize: '0.75rem', display: 'block', marginBottom: '0.25rem' }}>Zaman Dilimi</label>
              <select
                className="select"
                value={downloadForm.timeframe}
                onChange={(e) => setDownloadForm({ ...downloadForm, timeframe: e.target.value })}
              >
                <option value="tick">Tick</option>
                <option value="minutely">Dakikalik</option>
                <option value="hourly">Saatlik</option>
                <option value="daily">Gunluk</option>
              </select>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleDownload}
              disabled={downloading}
              style={{ width: '100%', padding: '0.75rem' }}
            >
              {downloading ? (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <RefreshCw size={16} className="animate-spin" />
                  Indiriliyor...
                </span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                  <Download size={16} /> Veri Indir
                </span>
              )}
            </button>
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={18} color="var(--accent-green)" />
            Veri Kaynaklari
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {sources.map(source => (
              <div key={source.id} style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{source.name}</div>
                <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                  {source.description}
                </p>
                <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
                  <span className="text-muted">
                    <strong className="text-blue">{source.instruments_count}+</strong> enstruman
                  </span>
                  <span className="text-muted">
                    <strong className="text-green">{source.since_year}</strong>'den beri
                  </span>
                </div>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                  {source.timeframes.map(tf => (
                    <span key={tf} className="badge badge-blue" style={{ fontSize: '0.7rem' }}>{tf}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <HardDrive size={18} color="var(--accent-purple)" />
          Indirilen Veriler ({allFiles.length})
        </h3>
        {loading ? (
          <div className="loading">Yukleniyor...</div>
        ) : allFiles.length === 0 ? (
          <div className="empty-state">
            <Database size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
            <p>Henuz indirilmis veri yok</p>
            <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Yukaridan veri indirebilirsiniz
            </p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Dosya Adi</th>
                <th>Kaynak</th>
                <th>Boyut</th>
                <th>Olusturulma</th>
                <th>Islem</th>
              </tr>
            </thead>
            <tbody>
              {allFiles.map((file) => (
                <tr key={file.filename}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Database size={16} color="var(--accent-blue)" />
                      <span style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {file.filename}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-blue">{file.source}</span>
                  </td>
                  <td style={{ fontFamily: 'monospace' }}>{file.size_mb.toFixed(2)} MB</td>
                  <td className="text-muted" style={{ fontSize: '0.85rem' }}>
                    {new Date(file.created).toLocaleString('tr-TR')}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn btn-outline"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        onClick={() => handlePreview(file.source, file.filename)}
                        disabled={previewLoading}
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        onClick={() => handleDelete(file.source, file.filename)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {preview && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Eye size={18} color="var(--accent-yellow)" />
            Onizleme: {preview.filename}
          </h3>
          <div className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Toplam {preview.total_rows} satir, {preview.preview_rows} satir gosteriliyor
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  {preview.columns.map((col: string) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.data.map((row: any, i: number) => (
                  <tr key={i}>
                    {preview.columns.map((col: string) => (
                      <td key={col} style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {typeof row[col] === 'number' ? row[col].toFixed(4) : String(row[col] || '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
