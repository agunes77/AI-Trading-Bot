import { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  type Node,
  type Edge,
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  MiniMap,
  Panel,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Editor from '@monaco-editor/react';
import { strategyBuilderApi } from '../services/api';
import SignalChart from '../components/SignalChart';
import {
  Save, Play, FolderOpen, Trash2, Blocks, Code2, FileCode
} from 'lucide-react';

const PINE_PRESETS: Record<string, string> = {
  'RSI + MACD': `//@version=5
indicator("RSI + MACD Strategy", overlay=false)
rsiLen = input.int(14, "RSI Period")
fastLen = input.int(12, "MACD Fast")
slowLen = input.int(26, "MACD Slow")
sigLen = input.int(9, "MACD Signal")
rsiVal = ta.rsi(close, rsiLen)
[macdLine, signalLine, histLine] = ta.macd(close, fastLen, slowLen, sigLen)
rsiOversold = rsiVal < 30
macdBullish = ta.crossover(macdLine, signalLine)
longCondition = rsiOversold and macdBullish
plot(rsiVal, "RSI", color=purple)
hline(70, "Overbought", color=red)
hline(30, "Oversold", color=green)`,
  
  'Bollinger Kırılım': `//@version=5
indicator("BB Breakout", overlay=true)
length = input.int(20, "Length")
mult = input.float(2.0, "Std Dev")
[upper, middle, lower] = ta.bb(close, length, mult)
breakoutUp = ta.crossover(close, upper)
longCondition = breakoutUp
plot(upper, "Upper", color=red)
plot(middle, "Middle", color=blue)
plot(lower, "Lower", color=green)`,
  
  'Supertrend': `//@version=5
indicator("Supertrend", overlay=true)
factor = input.float(3.0, "Factor")
period = input.int(10, "Period")
[st, direction] = ta.supertrend(factor, period)
longCondition = direction > 0 and direction[1] <= 0
plot(st, "Supertrend", color=direction > 0 ? green : red, linewidth=2)`,
};

export default function PineScriptEditor() {
  const [mode, setMode] = useState<'visual' | 'code'>('code');
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [categories, setCategories] = useState<Record<string, any[]>>({});
  const [pineCode, setPineCode] = useState(PINE_PRESETS['RSI + MACD']);
  const [selectedPreset, setSelectedPreset] = useState('RSI + MACD');
  const [savedStrategies, setSavedStrategies] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [strategyName, setStrategyName] = useState('Yeni Pine Script');
  const [strategyId, setStrategyId] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [nodesRes, strategiesRes] = await Promise.all([
        strategyBuilderApi.getNodes(),
        strategyBuilderApi.getStrategies()
      ]);
      setCategories(nodesRes.data.categories);
      setSavedStrategies(strategiesRes.data.strategies);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    }
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = (category: any) => {
    const id = `${category.id}_${Date.now()}`;
    const newNode: Node = {
      id,
      type: 'custom',
      position: { x: Math.random() * 400 + 200, y: Math.random() * 300 + 100 },
      data: { ...category, label: category.name },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const runPineScript = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await strategyBuilderApi.runPineScript({
        pine_code: pineCode,
        source: 'crypto',
        symbol: 'BTC/USDT',
        timeframe: '1h',
        days: 365,
      });
      setResult(res.data);
    } catch (error) {
      console.error('Çalıştırma hatası:', error);
      alert('Hata: ' + (error as any).message);
    } finally {
      setRunning(false);
    }
  };

  const saveStrategy = async () => {
    const id = strategyId || `pine_${Date.now()}`;
    try {
      await strategyBuilderApi.saveStrategy({
        id,
        name: strategyName,
        description: 'Pine Script Stratejisi',
        mode: 'code',
        nodes: [],
        edges: [],
        pine_code: pineCode,
      });
      setStrategyId(id);
      alert('Strateji kaydedildi!');
      loadData();
    } catch (error) {
      console.error('Kaydetme hatası:', error);
    }
  };

  const loadStrategy = async (id: string) => {
    try {
      const res = await strategyBuilderApi.getStrategy(id);
      const strategy = res.data;
      setStrategyId(id);
      setStrategyName(strategy.name);
      if (strategy.pine_code) {
        setMode('code');
        setPineCode(strategy.pine_code);
      }
    } catch (error) {
      console.error('Yükleme hatası:', error);
    }
  };

  const deleteStrategy = async (id: string) => {
    if (!confirm('Silinsin mi?')) return;
    try {
      await strategyBuilderApi.deleteStrategy(id);
      loadData();
    } catch (error) {
      console.error('Silme hatası:', error);
    }
  };

  const loadPreset = (name: string) => {
    setSelectedPreset(name);
    setPineCode(PINE_PRESETS[name] || '');
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 5rem)', gap: '1rem' }}>
      {/* Sol Panel */}
      <div style={{ width: 260, background: 'var(--bg-secondary)', borderRadius: 8, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Tasarım Modu</h3>
          <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1rem' }}>
            <button
              className={`btn ${mode === 'visual' ? 'btn-success' : 'btn-outline'}`}
              onClick={() => setMode('visual')}
              style={{ flex: 1, fontSize: '0.8rem', justifyContent: 'center' }}
            >
              <Blocks size={14} />
            </button>
            <button
              className={`btn ${mode === 'code' ? 'btn-success' : 'btn-outline'}`}
              onClick={() => setMode('code')}
              style={{ flex: 1, fontSize: '0.8rem', justifyContent: 'center' }}
            >
              <Code2 size={14} /> Pine
            </button>
          </div>
        </div>

        {mode === 'code' && (
          <div>
            <h3 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              <FileCode size={12} style={{ display: 'inline', marginRight: '0.25rem' }} /> TradingView Presetleri
            </h3>
            {Object.keys(PINE_PRESETS).map((name) => (
              <button
                key={name}
                onClick={() => loadPreset(name)}
                style={{
                  display: 'block', width: '100%', padding: '0.5rem', marginBottom: '0.25rem',
                  background: selectedPreset === name ? 'var(--accent-blue)' : 'var(--bg-card)',
                  border: '1px solid var(--border-color)', borderRadius: 4,
                  cursor: 'pointer', color: 'var(--text-primary)',
                  fontSize: '0.75rem', textAlign: 'left', fontWeight: 500,
                }}
              >{name}</button>
            ))}
          </div>
        )}
        
        {mode === 'visual' && categories && Object.keys(categories).length > 0 && (
          <div>
            <h3 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Node'lar</h3>
            {Object.entries(categories).map(([category, nodeDefs]: any) => (
              <div key={category} style={{ marginBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>{category}</div>
                {nodeDefs.map((nodeDef: any) => (
                  <button key={nodeDef.id} onClick={() => addNode(nodeDef)} style={{ display: 'block', width: '100%', padding: '0.3rem 0.5rem', marginBottom: '0.1rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 4, cursor: 'pointer', color: 'var(--text-primary)', fontSize: '0.7rem', textAlign: 'left' }}>
                    {nodeDef.name}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Orta Panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            className="input"
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            placeholder="Strateji adı"
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={saveStrategy}><Save size={14} style={{ marginRight: '0.3rem' }} /> Kaydet</button>
          <button className="btn btn-success" onClick={runPineScript} disabled={running}>
            {running ? 'Çalışıyor...' : <><Play size={14} style={{ marginRight: '0.3rem' }} /> Çalıştır</>}
          </button>
        </div>

        <div style={{ flex: 1, background: 'var(--bg-secondary)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border-color)' }}>
          {mode === 'visual' ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={{ custom: CustomNode }}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background />
              <Panel position="top-right">
                <div style={{ background: 'var(--bg-card)', padding: '0.3rem', borderRadius: 4, fontSize: '0.7rem' }}>
                  N: {nodes.length} | E: {edges.length}
                </div>
              </Panel>
            </ReactFlow>
          ) : (
            <Editor
              height="100%"
              defaultLanguage="javascript"
              value={pineCode}
              onChange={(value) => setPineCode(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: true }, fontSize: 13, lineNumbers: 'on',
                scrollBeyondLastLine: false, wordWrap: 'on', automaticLayout: true, tabSize: 4,
              }}
            />
          )}
        </div>

        {result && (
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '1rem', maxHeight: '40vh', overflowY: 'auto', border: '1px solid var(--border-color)' }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Backtest Sonuçları {result.name && `— ${result.name}`}
            </h3>
            {result.error ? (
              <div className="error">{result.error}</div>
            ) : (
              <>
                {result.performance && (
                  <div className="grid-4" style={{ marginBottom: '0.75rem' }}>
                    <div className="stat-card"><span className="stat-label">Getiri</span><span className={result.performance.total_return_pct >= 0 ? 'text-green' : 'text-red'} style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.performance.total_return_pct?.toFixed(2)}%</span></div>
                    <div className="stat-card"><span className="stat-label">Max DD</span><span className="text-red" style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.performance.max_drawdown_pct?.toFixed(2)}%</span></div>
                    <div className="stat-card"><span className="stat-label">Win Rate</span><span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.performance.win_rate?.toFixed(1)}%</span></div>
                    <div className="stat-card"><span className="stat-label">Trades</span><span style={{ fontSize: '1.1rem', fontWeight: 700 }}>{result.performance.total_trades}</span></div>
                  </div>
                )}
                {result.chart_data && result.chart_data.candles && result.chart_data.candles.length > 0 && (
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
                    <h4 style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>📈 Sinyal Grafiği</h4>
                    <SignalChart candles={result.chart_data.candles} buyMarkers={result.chart_data.buy_markers || []} sellMarkers={result.chart_data.sell_markers || []} />
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Sağ Panel */}
      <div style={{ width: 240, background: 'var(--bg-secondary)', borderRadius: 8, padding: '1rem', overflowY: 'auto' }}>
        <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Kayıtlı Stratejiler</h3>
        {savedStrategies.length === 0 ? (
          <div className="empty-state" style={{ padding: '1rem' }}><FolderOpen size={24} style={{ opacity: 0.3, marginBottom: '0.3rem' }} /><p style={{ fontSize: '0.8rem' }}>Kayıtlı strateji yok</p></div>
        ) : (
          savedStrategies.map((s: any) => (
            <div key={s.id} style={{ padding: '0.5rem', background: 'var(--bg-card)', borderRadius: 4, marginBottom: '0.3rem', border: strategyId === s.id ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{s.name}</span>
                <button onClick={() => deleteStrategy(s.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-red)' }}><Trash2 size={12} /></button>
              </div>
              <button onClick={() => loadStrategy(s.id)} className="btn btn-outline" style={{ width: '100%', fontSize: '0.7rem', padding: '0.2rem', justifyContent: 'center' }}>
                <FolderOpen size={10} style={{ marginRight: '0.2rem' }} /> Yükle
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function CustomNode({ data }: { data: any }) {
  return (
    <div style={{
      background: data.color || '#2962ff',
      borderRadius: 4, padding: '8px 12px', minWidth: 120, color: 'white', fontSize: '0.8rem', fontWeight: 600,
    }}>
      {data.inputs?.map((input: any) => (
        <Handle key={input.id} type="target" position={Position.Left} id={input.id} style={{ background: 'white' }} />
      ))}
      {data.name || data.label}
      {data.outputs?.map((output: any) => (
        <Handle key={output.id} type="source" position={Position.Right} id={output.id} style={{ background: 'white' }} />
      ))}
    </div>
  );
}