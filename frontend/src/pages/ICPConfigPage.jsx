import { useState, useEffect } from 'react';
import { getICP, saveICP, previewICP } from '../api/client';
import './ICPConfigPage.css';

const SENIORITY_OPTIONS = ['Individual Contributor', 'Manager', 'Senior Manager', 'Director', 'Head of', 'VP', 'C-Level'];
const DEFAULT_ICP = {
  name: 'My ICP',
  company_size_min: 20,
  company_size_max: 500,
  target_industries: [],
  required_tech_stack: [],
  min_seniority: 'Manager',
  disqualifiers: [],
  scoring_weights: { icp_fit: 0.6, buying_signals: 0.4 },
  criterion_weights: { company_size: 25, industry: 25, tech_stack: 20, seniority: 20, disqualifier_penalty: 10 },
  score_threshold: 60,
  product_description: '',
  value_proposition: '',
};

function TagInput({ value = [], onChange, placeholder }) {
  const [input, setInput] = useState('');
  const add = () => {
    const v = input.trim();
    if (v && !value.includes(v)) onChange([...value, v]);
    setInput('');
  };
  return (
    <div className="tag-input">
      <div className="tags">
        {value.map(t => (
          <span key={t} className="tag">
            {t}
            <button className="tag-remove" onClick={() => onChange(value.filter(x => x !== t))}>×</button>
          </span>
        ))}
      </div>
      <input className="input tag-field" value={input} placeholder={placeholder}
        onChange={e => setInput(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); add(); } }} />
    </div>
  );
}

function ScorePreview({ result }) {
  if (!result) return null;
  const { icp_fit_score, buying_signal_score, total_score, breakdown } = result;
  return (
    <div className="score-preview card-glass">
      <h4>Score Result</h4>
      <div className="preview-scores">
        <div className="score-item">
          <div className="score-num" style={{ color: total_score >= 60 ? 'var(--accent-secondary)' : 'var(--accent-danger)' }}>
            {Math.round(total_score)}
          </div>
          <div className="score-lbl">Total Score</div>
        </div>
        <div className="score-item">
          <div className="score-num">{Math.round(icp_fit_score)}</div>
          <div className="score-lbl">ICP Fit</div>
        </div>
        <div className="score-item">
          <div className="score-num">{Math.round(buying_signal_score)}</div>
          <div className="score-lbl">Signals</div>
        </div>
      </div>
      {breakdown && (
        <div className="breakdown-bars">
          {Object.entries(breakdown).filter(([k]) => k !== 'disqualified').map(([k, v]) => (
            <div key={k} className="breakdown-bar">
              <span className="breakdown-key">{k.replace(/_/g, ' ')}</span>
              <div className="mini-bar"><div className="mini-fill" style={{ width: `${v.score || 0}%` }} /></div>
              <span className="breakdown-val">{v.score || 0}</span>
              {v.matched && <span className="match-check">✓</span>}
            </div>
          ))}
          {breakdown.disqualified && <div className="disq-warn">⚠ Disqualifier triggered</div>}
        </div>
      )}
    </div>
  );
}

export default function ICPConfigPage() {
  const [icp, setIcp] = useState(DEFAULT_ICP);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [sampleLead, setSampleLead] = useState({
    company_size: '51-200', industry: 'SaaS', tech_stack: ['React', 'Node.js'],
    contact_role: 'VP of Engineering', funding_status: 'Series B',
  });
  const [previewResult, setPreviewResult] = useState(null);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    getICP().then(r => { if (r.data) setIcp({ ...DEFAULT_ICP, ...r.data }); }).catch(() => {});
  }, []);

  const update = (field, val) => setIcp(prev => ({ ...prev, [field]: val }));
  const updateWeights = (key, val) => {
    const fit = key === 'icp_fit' ? parseFloat(val) : icp.scoring_weights.icp_fit;
    setIcp(prev => ({ ...prev, scoring_weights: { icp_fit: fit, buying_signals: +(1 - fit).toFixed(2) } }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveICP(icp);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    setPreviewing(true);
    try {
      const res = await previewICP(sampleLead);
      setPreviewResult(res.data);
    } catch (e) {
      alert('Save your ICP first before previewing.');
    } finally {
      setPreviewing(false);
    }
  };

  return (
    <div className="icp-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">ICP Configuration</h1>
          <p className="page-sub">Define your Ideal Customer Profile for semantic lead scoring</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saved ? '✅ Saved!' : saving ? 'Saving...' : '💾 Save ICP'}
        </button>
      </div>

      <div className="icp-layout">
        <div className="icp-form">
          {/* Section 1: Company */}
          <div className="icp-section card">
            <h3 className="section-header">🏢 Company Criteria</h3>
            <div className="field-group">
              <label className="field-label">Company Size Range</label>
              <div className="size-range">
                <input type="number" className="input input-sm" value={icp.company_size_min}
                  onChange={e => update('company_size_min', +e.target.value)} />
                <span className="range-sep">to</span>
                <input type="number" className="input input-sm" value={icp.company_size_max}
                  onChange={e => update('company_size_max', +e.target.value)} />
                <span className="range-unit">employees</span>
              </div>
            </div>
            <div className="field-group">
              <label className="field-label">Target Industries <span className="field-hint">Press Enter to add</span></label>
              <TagInput value={icp.target_industries} onChange={v => update('target_industries', v)} placeholder="e.g. SaaS, Fintech, Healthcare..." />
            </div>
            <div className="field-group">
              <label className="field-label">Required Tech Stack <span className="field-hint">Press Enter to add</span></label>
              <TagInput value={icp.required_tech_stack} onChange={v => update('required_tech_stack', v)} placeholder="e.g. React, Salesforce, AWS..." />
            </div>
          </div>

          {/* Section 2: Contact */}
          <div className="icp-section card">
            <h3 className="section-header">👤 Contact Criteria</h3>
            <div className="field-group">
              <label className="field-label">Minimum Seniority</label>
              <select className="select" value={icp.min_seniority} onChange={e => update('min_seniority', e.target.value)}>
                {SENIORITY_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="field-group">
              <label className="field-label">Disqualifiers <span className="field-hint">Companies/industries to exclude</span></label>
              <TagInput value={icp.disqualifiers} onChange={v => update('disqualifiers', v)} placeholder="e.g. competitor name, agency, non-profit..." />
            </div>
          </div>

          {/* Section 3: Scoring Formula */}
          <div className="icp-section card">
            <h3 className="section-header">⚖️ Scoring Formula</h3>
            <p className="section-desc">Total Score = (ICP Fit × {icp.scoring_weights.icp_fit}) + (Signals × {icp.scoring_weights.buying_signals})</p>
            <div className="field-group">
              <label className="field-label">ICP Fit Weight: <strong>{icp.scoring_weights.icp_fit}</strong> (Signals: {icp.scoring_weights.buying_signals})</label>
              <input type="range" min="0.1" max="0.9" step="0.1" className="range-input"
                value={icp.scoring_weights.icp_fit} onChange={e => updateWeights('icp_fit', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">Score Threshold for Outreach Drafts: <strong>{icp.score_threshold}</strong></label>
              <input type="range" min="0" max="100" className="range-input"
                value={icp.score_threshold} onChange={e => update('score_threshold', +e.target.value)} />
            </div>
          </div>

          {/* Section 4: Product */}
          <div className="icp-section card">
            <h3 className="section-header">💼 Product Context</h3>
            <div className="field-group">
              <label className="field-label">Product Description</label>
              <textarea className="textarea" rows={3} placeholder="What does your product do?"
                value={icp.product_description} onChange={e => update('product_description', e.target.value)} />
            </div>
            <div className="field-group">
              <label className="field-label">Value Proposition</label>
              <textarea className="textarea" rows={2} placeholder="Why should they buy it?"
                value={icp.value_proposition} onChange={e => update('value_proposition', e.target.value)} />
            </div>
          </div>
        </div>

        {/* Section 5: Live Preview */}
        <div className="icp-preview-panel">
          <div className="icp-section card">
            <h3 className="section-header">🔮 Live Score Preview</h3>
            <p className="section-desc">Test how your ICP scores a sample lead</p>
            <div className="field-group">
              <label className="field-label">Company Size</label>
              <input className="input" value={sampleLead.company_size}
                onChange={e => setSampleLead(p => ({ ...p, company_size: e.target.value }))} />
            </div>
            <div className="field-group">
              <label className="field-label">Industry</label>
              <input className="input" value={sampleLead.industry}
                onChange={e => setSampleLead(p => ({ ...p, industry: e.target.value }))} />
            </div>
            <div className="field-group">
              <label className="field-label">Contact Role</label>
              <input className="input" value={sampleLead.contact_role}
                onChange={e => setSampleLead(p => ({ ...p, contact_role: e.target.value }))} />
            </div>
            <button className="btn btn-secondary" style={{ width: '100%' }} onClick={handlePreview} disabled={previewing}>
              {previewing ? 'Scoring...' : '⚡ Score This Lead'}
            </button>
            <ScorePreview result={previewResult} />
          </div>
        </div>
      </div>
    </div>
  );
}
