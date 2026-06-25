import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLeads } from '../hooks/useLeads';
import { deleteLead, retryEnrichment, syncToCRM } from '../api/client';
import './Dashboard.css';

const STATUS_COLORS = {
  pending: 'var(--text-muted)',
  enriching: 'var(--accent-primary)',
  enriched: 'var(--accent-secondary)',
  failed: 'var(--accent-danger)',
};

function ScoreBar({ score }) {
  const color = score >= 80 ? '#00d4aa' : score >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="score-bar-wrap">
      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${score || 0}%`, background: color }} />
      </div>
      <span className="score-val" style={{ color }}>{score ? Math.round(score) : '—'}</span>
    </div>
  );
}

function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card card-glass">
      <div className="stat-icon" style={{ color }}>{icon}</div>
      <div className="stat-body">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState('created_at');
  const [selected, setSelected] = useState(new Set());

  const { leads, total, loading, refetch } = useLeads({
    search: search || undefined,
    status: statusFilter || undefined,
    min_score: minScore > 0 ? minScore : undefined,
    sort_by: sortBy,
    limit: 100,
  });

  const stats = useMemo(() => {
    const enriched = leads.filter(l => l.status === 'enriched').length;
    const avgScore = leads.length > 0
      ? Math.round(leads.reduce((s, l) => s + (l.total_score || 0), 0) / leads.length)
      : 0;
    const synced = leads.filter(l => l.crm_sync_status === 'synced' || l.crm_sync_status === 'updated').length;
    return { total: total, enriched, avgScore, synced };
  }, [leads, total]);

  const toggleSelect = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Delete this lead?')) return;
    await deleteLead(id);
    refetch();
  };

  const handleRetry = async (id, e) => {
    e.stopPropagation();
    await retryEnrichment(id);
    refetch();
  };

  const handleSync = async (id, e) => {
    e.stopPropagation();
    await syncToCRM(id);
    setTimeout(refetch, 1000);
  };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1 className="page-title">Lead Intelligence</h1>
          <p className="page-sub">Your enriched, scored, and ready-to-reach leads</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/upload')}>
          + Upload CSV
        </button>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <StatCard label="Total Leads" value={stats.total} icon="👥" color="var(--accent-primary)" />
        <StatCard label="Enriched" value={stats.enriched} icon="✅" color="var(--accent-secondary)" />
        <StatCard label="Avg ICP Score" value={`${stats.avgScore}`} icon="🎯" color="var(--accent-warning)" />
        <StatCard label="CRM Synced" value={stats.synced} icon="🔗" color="#a78bfa" />
      </div>

      {/* Filters */}
      <div className="filter-bar card-glass">
        <input
          className="input search-input"
          placeholder="🔍 Search by name or company..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="enriching">Enriching</option>
          <option value="enriched">Enriched</option>
          <option value="failed">Failed</option>
        </select>
        <div className="score-filter">
          <label className="filter-label">Min Score: <strong>{minScore}</strong></label>
          <input type="range" min="0" max="100" value={minScore}
            onChange={e => setMinScore(Number(e.target.value))} className="range-input" />
        </div>
        <select className="select" value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option value="created_at">Sort: Newest</option>
          <option value="total_score">Sort: Score</option>
          <option value="company">Sort: Company</option>
          <option value="name">Sort: Name</option>
        </select>
      </div>

      {/* Bulk Actions */}
      {selected.size > 0 && (
        <div className="bulk-bar card-glass">
          <span>{selected.size} selected</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setSelected(new Set())}>Clear</button>
        </div>
      )}

      {/* Table */}
      <div className="table-wrap card">
        {loading ? (
          <div className="skeleton-rows">
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton skeleton-row" />)}
          </div>
        ) : leads.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No leads yet</h3>
            <p>Upload a CSV to start enriching leads</p>
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>Upload CSV</button>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th width="36">
                  <input type="checkbox" onChange={e => setSelected(e.target.checked ? new Set(leads.map(l => l.id)) : new Set())} />
                </th>
                <th>Name / Contact</th>
                <th>Company</th>
                <th>ICP Score</th>
                <th>Top Signal</th>
                <th>Industry</th>
                <th>Status</th>
                <th>CRM</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leads.map(lead => (
                <tr key={lead.id} onClick={() => navigate(`/leads/${lead.id}`)} className="table-row">
                  <td onClick={e => e.stopPropagation()}>
                    <input type="checkbox" checked={selected.has(lead.id)}
                      onChange={() => toggleSelect(lead.id)} />
                  </td>
                  <td>
                    <div className="lead-name-cell">
                      <div className="avatar">{(lead.name || lead.company || '?')[0].toUpperCase()}</div>
                      <div>
                        <div className="lead-name">{lead.name || '—'}</div>
                        <div className="lead-email">{lead.email || lead.domain || ''}</div>
                      </div>
                    </div>
                  </td>
                  <td className="company-cell">{lead.company || '—'}</td>
                  <td><ScoreBar score={lead.total_score} /></td>
                  <td>
                    {lead.top_buying_signal
                      ? <span className="signal-badge">{lead.top_buying_signal.slice(0, 50)}{lead.top_buying_signal.length > 50 ? '...' : ''}</span>
                      : <span className="text-muted">—</span>}
                  </td>
                  <td>
                    {lead.industry
                      ? <span className="badge badge-info">{lead.industry.slice(0, 25)}</span>
                      : <span className="text-muted">—</span>}
                  </td>
                  <td>
                    <div className="status-cell">
                      <span className={`status-dot status-${lead.status}`} />
                      <span className="status-text">{lead.status}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`crm-status crm-${lead.crm_sync_status || 'none'}`}>
                      {lead.crm_sync_status === 'synced' || lead.crm_sync_status === 'updated' ? '✓' :
                       lead.crm_sync_status === 'failed' ? '✗' :
                       lead.crm_sync_status === 'pending' ? '⏳' : '—'}
                    </span>
                  </td>
                  <td onClick={e => e.stopPropagation()}>
                    <div className="action-buttons">
                      {lead.status === 'failed' && (
                        <button className="btn-icon" title="Retry" onClick={e => handleRetry(lead.id, e)}>🔄</button>
                      )}
                      {lead.status === 'enriched' && (
                        <button className="btn-icon" title="Sync to Notion" onClick={e => handleSync(lead.id, e)}>🔗</button>
                      )}
                      <button className="btn-icon btn-icon--danger" title="Delete" onClick={e => handleDelete(lead.id, e)}>🗑</button>
                    </div>
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
