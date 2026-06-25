import { NavLink, useLocation } from 'react-router-dom';
import './Layout.css';

const NAV = [
  { to: '/', icon: '⚡', label: 'Dashboard', exact: true },
  { to: '/upload', icon: '📤', label: 'Upload CSV' },
  { to: '/pipeline', icon: '🔄', label: 'Pipeline' },
  { to: '/icp', icon: '🎯', label: 'ICP Config' },
];

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-bolt">⚡</span>
          <span className="logo-text">Alfaleus</span>
        </div>
        <nav className="sidebar-nav">
          {NAV.map(({ to, icon, label, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) => `nav-item ${isActive ? 'nav-item--active' : ''}`}
            >
              <span className="nav-icon">{icon}</span>
              <span className="nav-label">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="version-badge">v1.0.0</div>
        </div>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
