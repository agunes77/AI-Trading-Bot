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
  type NodeTypes,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Editor from '@monaco-editor/react';
import { strategyBuilderApi } from '../services/api';
import {
  Save, Play, FolderOpen, Trash2, Plus, Activity, TrendingUp,
  BarChart2, GitMerge, Sliders, ArrowUp, ArrowDown, ShoppingCart,
  Zap, GitBranch, History, Ampersand, PlusCircle, Minus, Circle,
  Code2, Blocks, FileCode
} from 'lucide-react';

interface NodeCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  type: string;
  inputs: Array<{ id: string; name: string; type: string }>;
  outputs: Array<{ id: string; name: string; type: string }>;
  parameters: Record<string, any>;
}

function CustomNode({ data }: { data: any }) {
  return (
    <div style={{
      background: data.color || '#3b82f6',
      border: '2px solid rgba(255,255,255,0.2)',
      borderRadius: 8,
      padding: '10px 15px',
      minWidth: 150,
      color: 'white',
      fontSize: '0.85rem',
      fontWeight: 600,
    }}>
      {data.inputs?.map((input: any) => (
        <Handle
          key={input.id}
          type="target"
          position={Position.Left}
          id={input.id}
          style={{ top: 'auto', background: '#fff' }}
        />
      ))}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>{data.name}</span>
      </div>
      {data.parameters && Object.keys(data.parameters).length > 0 && (
        <div style={{ fontSize: '0.7rem', opacity: 0.8, marginTop: '0.25rem' }}>
          {Object.entries(data.parameters).map(([key, value]) => (
            <div key={key}>{key}: {String(value)}</div>
          ))}
        </div>
      )}
      {data.outputs?.map((output: any) => (
        <Handle
          key={output.id}
          type="source"
          position={Position.Right}
          id={output.id}
          style={{ top: 'auto', background: '#fff' }}
        />
      ))}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

const PINE_PRESETS: Record<string, string> = {
  'RSI + MACD Stratejisi': `//@version=5
indicator("RSI + MACD Strategy", overlay=false)

// Input parametreleri
rsiLen = input.int(14, "RSI Period")
fastLen = input.int(12, "MACD Fast")
slowLen = input.int(26, "MACD Slow")
sigLen = input.int(9, "MACD Signal")

// İndikatör hesaplamaları
rsiVal = ta.rsi(close, rsiLen)
[macdLine, signalLine, histLine] = ta.macd(close, fastLen, slowLen, sigLen)

// Koşullar
rsiOversold = rsiVal < 30
rsiOverbought = rsiVal > 70
macdBullish = ta.crossover(macdLine, signalLine)
macdBearish = ta.crossunder(macdLine, signalLine)

// Sinyaller
longCondition = rsiOversold and macdBullish
shortCondition = rsiOverbought and macdBearish

// Plot
plot(rsiVal, "RSI", color=purple)
hline(70, "Overbought", color=red)
hline(30, "Oversold", color=green)`,

  'Bollinger Bant Kırılım': `//@version=5
indicator("BB Breakout", overlay=true)

// Input
length = input.int(20, "Length")
mult = input.float(2.0, "Std Dev")

// Bollinger Bands
[upper, middle, lower] = ta.bb(close, length, mult)

// Kırılım koşulları
breakoutUp = ta.crossover(close, upper)
breakoutDown = ta.crossunder(close, lower)

// Plot
plot(upper, "Upper", color=red)
plot(middle, "Middle", color=blue)
plot(lower, "Lower", color=green)`,

  'EMA Cross Stratejisi': `//@version=5
indicator("EMA Cross", overlay=true)

// EMA hesaplama
fastEma = ta.ema(close, 9)
slowEma = ta.ema(close, 21)

// Kesişim sinyalleri
bullishCross = ta.crossover(fastEma, slowEma)
bearishCross = ta.crossunder(fastEma, slowEma)

// Plot
plot(fastEma, "Fast EMA", color=blue)
plot(slowEma, "Slow EMA", color=red)`,

  'Supertrend Stratejisi': `//@version=5
indicator("Supertrend", overlay=true)

// Supertrend
factor = input.float(3.0, "Factor")
period = input.int(10, "Period")
[st, direction] = ta.supertrend(factor, period)

// Plot
plot(st, "Supertrend", color=direction > 0 ? green : red, linewidth=2)`,

  'Stochastic + RSI': `//@version=5
indicator("Stoch + RSI", overlay=false)

// Stochastic
[k, d] = ta.stoch(high, low, close, 14, 3)

// RSI
rsiVal = ta.rsi(close, 14)

// Koşullar
stochOversold = k < 20
stochOverbought = k > 80
rsiOversold = rsiVal < 30
rsiOverbought = rsiVal > 70

// Plot
plot(k, "%K", color=blue)
plot(d, "%D", color=red)
hline(80, "Overbought", color=red)
hline(20, "Oversold", color=green)`,

  'ATR Trailing Stop': `//@version=5
indicator("ATR Trailing Stop", overlay=true)

// ATR
atrPeriod = input.int(14, "ATR Period")
atrMult = input.float(2.0, "ATR Multiplier")
atr = ta.atr(high, low, close, atrPeriod)

// Trailing Stop
trailStop = close - (atr * atrMult)

// Plot
plot(trailStop, "Trailing Stop", color=orange, linewidth=2)
plot(close, "Close", color=blue)`,

  'MACD Histogram Reversal': `//@version=5
indicator("MACD Hist Reversal", overlay=false)

// MACD
fastLen = input.int(12, "Fast")
slowLen = input.int(26, "Slow")
sigLen = input.int(9, "Signal")
[macdLine, signalLine, histLine] = ta.macd(close, fastLen, slowLen, sigLen)

// Histogram dönüş
histBullish = ta.crossover(histLine, 0)
histBearish = ta.crossunder(histLine, 0)

// Plot
plot(histLine, "Histogram", color=histLine > 0 ? green : red, style=plot.style_histogram)
plot(macdLine, "MACD", color=blue)
plot(signalLine, "Signal", color=red)`,

  'Volume Breakout': `//@version=5
indicator("Volume Breakout", overlay=false)

// Volume
volPeriod = input.int(20, "Volume SMA Period")
volMult = input.float(2.0, "Volume Multiplier")
volSma = ta.sma(volume, volPeriod)

// Koşul
highVolume = volume > volSma * volMult
priceUp = close > close[1]

// Plot
plot(volume, "Volume", color=highVolume and priceUp ? green : red, style=plot.style_histogram)
plot(volSma, "Vol SMA", color=orange)`,

  'Ichimoku Cloud': `//@version=5
indicator("Ichimoku", overlay=true)

// Ichimoku bileşenleri
conversionLine = (ta.highest(high, 9) + ta.lowest(low, 9)) / 2
baseLine = (ta.highest(high, 26) + ta.lowest(low, 26)) / 2
leadingSpanA = (conversionLine + baseLine) / 2
leadingSpanB = (ta.highest(high, 52) + ta.lowest(low, 52)) / 2

// Plot
plot(conversionLine, "Conversion", color=blue)
plot(baseLine, "Base", color=red)
plot(leadingSpanA, "Span A", color=green, offset=26)
plot(leadingSpanB, "Span B", color=red, offset=26)`,

  'VWAP Stratejisi': `//@version=5
indicator("VWAP Strategy", overlay=true)

// VWAP
vwapVal = ta.vwma(close, 20)

// Koşullar
aboveVwap = close > vwapVal
belowVwap = close < vwapVal

// Plot
plot(vwapVal, "VWAP", color=purple, linewidth=2)`,
};

export default function StrategyBuilder() {
  const [mode, setMode] = useState<'visual' | 'code'>('visual');
  
  // Visual editor states
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [categories, setCategories] = useState<Record<string, NodeCategory[]>>({});
  
  // Code editor states
  const [pineCode, setPineCode] = useState(PINE_PRESETS['RSI + MACD Stratejisi']);
  const [selectedPreset, setSelectedPreset] = useState('RSI + MACD Stratejisi');
  
  // Common states
  const [savedStrategies, setSavedStrategies] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [strategyName, setStrategyName] = useState('Yeni Strateji');
  const [strategyId, setStrategyId] = useState('');

  useEffect(() => {
    loadNodeLibrary();
    loadSavedStrategies();
  }, []);

  const loadNodeLibrary = async () => {
    try {
      const res = await strategyBuilderApi.getNodes();
      setCategories(res.data.categories);
    } catch (error) {
      console.error('Node kütüphanesi yükleme hatası:', error);
    }
  };

  const loadSavedStrategies = async () => {
    try {
      const res = await strategyBuilderApi.getStrategies();
      setSavedStrategies(res.data.strategies);
    } catch (error) {
      console.error('Strateji listesi yükleme hatası:', error);
    }
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = (category: NodeCategory) => {
    const id = `${category.id}_${Date.now()}`;
    const newNode: Node = {
      id,
      type: 'custom',
      position: { x: Math.random() * 400 + 200, y: Math.random() * 300 + 100 },
      data: { ...category, label: category.name },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const runVisualStrategy = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await strategyBuilderApi.runStrategy({
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.data.id,
          data: { parameters: n.data.parameters },
        })),
        edges: edges.map(e => ({
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
        })),
        source: 'crypto',
        symbol: 'BTC/USDT',
        timeframe: '1h',
        days: 365,
      });
      setResult(res.data);
    } catch (error) {
      console.error('Strateji çalıştırma hatası:', error);
      alert('Hata: ' + (error as any).message);
    } finally {
      setRunning(false);
    }
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
      console.error('Pine Script çalıştırma hatası:', error);
      alert('Hata: ' + (error as any).message);
    } finally {
      setRunning(false);
    }
  };

  const runStrategy = mode === 'visual' ? runVisualStrategy : runPineScript;

  const saveStrategy = async () => {
    const id = strategyId || `strategy_${Date.now()}`;
    try {
      await strategyBuilderApi.saveStrategy({
        id,
        name: strategyName,
        description: '',
        mode,
        nodes: mode === 'visual' ? nodes.map(n => ({
          id: n.id, type: n.data.id, position: n.position, data: n.data,
        })) : [],
        edges: mode === 'visual' ? edges.map(e => ({
          source: e.source, target: e.target,
          sourceHandle: e.sourceHandle, targetHandle: e.targetHandle,
        })) : [],
        pine_code: mode === 'code' ? pineCode : '',
      });
      setStrategyId(id);
      alert('Strateji kaydedildi!');
      loadSavedStrategies();
    } catch (error) {
      console.error('Kaydetme hatası:', error);
      alert('Hata: ' + (error as any).message);
    }
  };

  const loadStrategy = async (id: string) => {
    try {
      const res = await strategyBuilderApi.getStrategy(id);
      const strategy = res.data;
      setStrategyId(id);
      setStrategyName(strategy.name);
      
      if (strategy.mode === 'code' && strategy.pine_code) {
        setMode('code');
        setPineCode(strategy.pine_code);
      } else if (strategy.mode === 'visual') {
        setMode('visual');
        const loadedNodes = (strategy.nodes || []).map((n: any) => ({
          id: n.id, type: 'custom', position: n.position, data: n.data,
        }));
        setNodes(loadedNodes);
        setEdges(strategy.edges || []);
      }
    } catch (error) {
      console.error('Yükleme hatası:', error);
    }
  };

  const deleteStrategy = async (id: string) => {
    if (!confirm('Strateji silinecek. Emin misiniz?')) return;
    try {
      await strategyBuilderApi.deleteStrategy(id);
      loadSavedStrategies();
      if (strategyId === id) {
        setNodes([]);
        setEdges([]);
        setStrategyId('');
      }
    } catch (error) {
      console.error('Silme hatası:', error);
    }
  };

  const clearCanvas = () => {
    setNodes([]);
    setEdges([]);
    setStrategyId('');
    setStrategyName('Yeni Strateji');
    setResult(null);
  };

  const loadPreset = (name: string) => {
    setSelectedPreset(name);
    setPineCode(PINE_PRESETS[name] || '');
  };

  const getIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      'trending-up': TrendingUp, 'activity': Activity, 'bar-chart-2': BarChart2,
      'git-merge': GitMerge, 'sliders': Sliders, 'arrow-up': ArrowUp,
      'arrow-down': ArrowDown, 'shopping-cart': ShoppingCart, 'zap': Zap,
      'git-branch': GitBranch, 'history': History, 'ampersand': Ampersand,
      'plus': PlusCircle, 'minus': Minus, 'circle': Circle,
    };
    const Icon = icons[iconName] || Circle;
    return <Icon size={16} />;
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 4rem)', gap: '1rem' }}>
      {/* Sol Panel */}
      <div style={{ width: 280, background: 'var(--bg-card)', borderRadius: 12, padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Mod Seçimi */}
        <div>
          <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>Tasarım Modu</h3>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className={`btn ${mode === 'visual' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setMode('visual')}
              style={{ flex: 1, fontSize: '0.8rem' }}
            >
              <Blocks size={14} style={{ marginRight: '0.25rem' }} />
              Görsel
            </button>
            <button
              className={`btn ${mode === 'code' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setMode('code')}
              style={{ flex: 1, fontSize: '0.8rem' }}
            >
              <Code2 size={14} style={{ marginRight: '0.25rem' }} />
              Pine Script
            </button>
          </div>
        </div>

        {/* Görsel Mod: Node Kütüphanesi */}
        {mode === 'visual' && (
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>Node Kütüphanesi</h3>
            {Object.entries(categories).map(([category, nodeDefs]) => (
              <div key={category} style={{ marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  {category}
                </div>
                {nodeDefs.map((nodeDef) => (
                  <button
                    key={nodeDef.id}
                    onClick={() => addNode(nodeDef)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.5rem',
                      width: '100%', padding: '0.4rem', marginBottom: '0.2rem',
                      background: 'var(--bg-primary)', border: '1px solid var(--border-color)',
                      borderRadius: 6, cursor: 'pointer', color: 'var(--text-primary)',
                      fontSize: '0.75rem', textAlign: 'left',
                    }}
                  >
                    <div style={{
                      width: 22, height: 22, borderRadius: 4,
                      background: nodeDef.color, display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      color: 'white', flexShrink: 0,
                    }}>
                      {getIcon(nodeDef.icon)}
                    </div>
                    <span>{nodeDef.name}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Kod Modu: Presetler */}
        {mode === 'code' && (
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              <FileCode size={14} style={{ display: 'inline', marginRight: '0.25rem' }} />
              TradingView Presetleri
            </h3>
            {Object.keys(PINE_PRESETS).map((name) => (
              <button
                key={name}
                onClick={() => loadPreset(name)}
                style={{
                  display: 'block', width: '100%', padding: '0.5rem',
                  marginBottom: '0.25rem', background: selectedPreset === name ? 'var(--accent-blue)' : 'var(--bg-primary)',
                  border: '1px solid var(--border-color)', borderRadius: 6,
                  cursor: 'pointer', color: 'var(--text-primary)',
                  fontSize: '0.75rem', textAlign: 'left',
                }}
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Orta Panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {/* Üst Bar */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            className="input"
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            placeholder="Strateji adı"
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={saveStrategy}>
            <Save size={16} style={{ marginRight: '0.5rem' }} />
            Kaydet
          </button>
          <button className="btn btn-success" onClick={runStrategy} disabled={running}>
            {running ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ width: 16, height: 16, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                Çalışıyor...
              </span>
            ) : (
              <>
                <Play size={16} style={{ marginRight: '0.5rem' }} />
                Çalıştır
              </>
            )}
          </button>
          <button className="btn btn-outline" onClick={clearCanvas}>
            <Plus size={16} style={{ marginRight: '0.5rem' }} />
            Yeni
          </button>
        </div>

        {/* Editör Alanı */}
        <div style={{ flex: 1, background: 'var(--bg-card)', borderRadius: 12, overflow: 'hidden' }}>
          {mode === 'visual' ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background />
              <Panel position="top-right">
                <div style={{ background: 'var(--bg-card)', padding: '0.5rem', borderRadius: 6, fontSize: '0.75rem' }}>
                  Node: {nodes.length} | Bağlantı: {edges.length}
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
                minimap: { enabled: true },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                tabSize: 4,
              }}
            />
          )}
        </div>

        {/* Sonuç Paneli */}
        {result && (
          <div style={{ background: 'var(--bg-card)', borderRadius: 12, padding: '1rem', maxHeight: 250, overflowY: 'auto' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              Backtest Sonuçları {result.name && `— ${result.name}`}
            </h3>
            {result.error ? (
              <div style={{ color: 'var(--accent-red)', padding: '0.5rem' }}>
                Hata: {result.error}
              </div>
            ) : result.performance ? (
              <div className="grid-4">
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Toplam Getiri</div>
                  <div className={result.performance.total_return_pct >= 0 ? 'text-green' : 'text-red'} style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {result.performance.total_return_pct.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Max Drawdown</div>
                  <div className="text-red" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {result.performance.max_drawdown_pct.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Sharpe Ratio</div>
                  <div className="text-blue" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {result.performance.sharpe_ratio.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Kazanma Oranı</div>
                  <div className="text-yellow" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {result.performance.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Toplam İşlem</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.performance.total_trades}</div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Kazanan</div>
                  <div className="text-green" style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.performance.winning_trades}</div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Kaybeden</div>
                  <div className="text-red" style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.performance.losing_trades}</div>
                </div>
                <div>
                  <div className="text-muted" style={{ fontSize: '0.75rem' }}>Son Bakiye</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>${result.performance.final_equity?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Sağ Panel: Kayıtlı Stratejiler */}
      <div style={{ width: 280, background: 'var(--bg-card)', borderRadius: 12, padding: '1rem', overflowY: 'auto' }}>
        <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.75rem' }}>Kayıtlı Stratejiler</h3>
        {savedStrategies.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 1rem' }}>
            <FolderOpen size={32} style={{ marginBottom: '0.5rem', opacity: 0.3 }} />
            <p style={{ fontSize: '0.85rem' }}>Henüz strateji yok</p>
          </div>
        ) : (
          savedStrategies.map((strategy) => (
            <div key={strategy.id} style={{
              padding: '0.75rem', background: 'var(--bg-primary)',
              borderRadius: 6, marginBottom: '0.5rem',
              border: strategyId === strategy.id ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{strategy.name}</div>
                <button
                  className="btn btn-danger"
                  style={{ padding: '0.25rem', fontSize: '0.7rem' }}
                  onClick={() => deleteStrategy(strategy.id)}
                >
                  <Trash2 size={12} />
                </button>
              </div>
              <div className="text-muted" style={{ fontSize: '0.7rem', marginBottom: '0.25rem' }}>
                {strategy.mode === 'code' ? '📝 Pine Script' : '🧱 Görsel'} | {strategy.node_count || 0} node | {new Date(strategy.updated_at).toLocaleDateString('tr-TR')}
              </div>
              <button
                className="btn btn-outline"
                style={{ width: '100%', fontSize: '0.75rem', padding: '0.25rem' }}
                onClick={() => loadStrategy(strategy.id)}
              >
                <FolderOpen size={12} style={{ marginRight: '0.25rem' }} />
                Yükle
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
