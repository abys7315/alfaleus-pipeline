import { usePipelineSSE } from '../hooks/useSSE';
import './PipelinePage.css';

const STAGES = ['website', 'linkedin', 'news', 'scoring', 'drafts'];

function StageIcon({ stage, current, status }) {
  const passed = STAGES.indexOf(current) > STAGES.indexOf(stage);
  const active = current === stage;
  const failed = active && status === 'failed';
  if (passed) return <span className="stage-icon stage-done">✓</span>;
  if (failed) return <span className="stage-icon stage-fail">✗</span>;
  if (active) return <span className="stage-icon stage-active"><span className="spinner-sm" /></span>;
  return <span className="stage-icon stage-pending">○</span>;
}

export default function PipelinePage() {
  const { activePipelines } = usePipelineSSE();

  return (
    <div className="pipeline-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Pipeline Monitor</h1>
          <p className="page-sub">Real-time enrichment progress across all active leads</p>
        </div>
        <div className="active-count">
          <span className="pulse-dot" />
          {activePipelines.length} active
        </div>
      </div>

      {activePipelines.length === 0 ? (
        <div className="pipeline-empty card-glass">
          <div className="empty-icon">🔄</div>
          <h3>No active enrichments</h3>
          <p className="text-muted">Upload a CSV or add a lead to see live pipeline progress here</p>
        </div>
      ) : (
        <div className="pipeline-list">
          {activePipelines.map(item => (
            <div key={item.lead_id} className="pipeline-card card-glass">
              <div className="pipeline-card-header">
                <div className="pipeline-lead-info">
                  <div className="avatar avatar-sm">
                    {(item.name || item.company || '?')[0]?.toUpperCase()}
                  </div>
                  <div>
                    <div className="pipeline-name">{item.name || 'Unknown'}</div>
                    <div className="pipeline-company">{item.company || '—'}</div>
                  </div>
                </div>
                <span className={`status-badge ${item.stage === 'complete' ? 'badge-success' : item.stage === 'failed' ? 'badge-danger' : 'badge-info'}`}>
                  {item.stage === 'complete' ? '✅ Complete' : item.stage === 'failed' ? '❌ Failed' : '⚡ Enriching'}
                </span>
              </div>

              <div className="stage-track">
                {STAGES.map((stage, i) => (
                  <div key={stage} className="stage-item">
                    <StageIcon stage={stage} current={item.stage} status={item.status} />
                    <span className="stage-label">{stage.charAt(0).toUpperCase() + stage.slice(1)}</span>
                    {i < STAGES.length - 1 && <div className={`stage-connector ${STAGES.indexOf(item.stage) > i ? 'done' : ''}`} />}
                  </div>
                ))}
              </div>

              {item.stage === 'complete' && (
                <div className="pipeline-result">
                  <span className="result-item">ICP Score: <strong style={{color: 'var(--accent-secondary)'}}>{item.data?.icp_score ?? '—'}</strong></span>
                  <span className="result-item">Signals: <strong style={{color: 'var(--accent-primary)'}}>{item.data?.signal_count ?? 0}</strong></span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
