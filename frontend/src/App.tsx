import { useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Insights from './pages/Insights';
import Transactions from './pages/Transactions';
import Upload from './pages/Upload';

export default function App() {
  const [dark, setDark] = useState(false);
  return (
    <div className={dark ? 'dark' : ''}>
      <div className="app">
        <header>
          <h1>💰 PennyWise</h1>
          <nav>
            <NavLink to="/" end>대시보드</NavLink>
            <NavLink to="/transactions">거래 내역</NavLink>
            <NavLink to="/upload">업로드</NavLink>
            <NavLink to="/insights">인사이트</NavLink>
          </nav>
          <button onClick={() => setDark((d) => !d)}>{dark ? '☀️ 라이트' : '🌙 다크'}</button>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/insights" element={<Insights />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
