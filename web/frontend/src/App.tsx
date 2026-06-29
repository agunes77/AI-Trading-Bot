import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Prices from './pages/Prices';
import Chart from './pages/Chart';
import Strategies from './pages/Strategies';
import Trades from './pages/Trades';
import AI from './pages/AI';
import DataManagement from './pages/DataManagement';
import TradingAgentsPage from './pages/TradingAgents';
import StrategyBuilder from './pages/StrategyBuilder';
import PineScriptEditor from './pages/PineScriptEditor';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="prices" element={<Prices />} />
          <Route path="chart" element={<Chart />} />
          <Route path="strategies" element={<Strategies />} />
          <Route path="builder" element={<StrategyBuilder />} />
          <Route path="pine-script" element={<PineScriptEditor />} />
          <Route path="data" element={<DataManagement />} />
          <Route path="trading-agents" element={<TradingAgentsPage />} />
          <Route path="trades" element={<Trades />} />
          <Route path="ai" element={<AI />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;