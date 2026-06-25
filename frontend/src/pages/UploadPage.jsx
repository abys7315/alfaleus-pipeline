import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadCSV } from '../api/client';
import { validateCSV } from '../utils/csvValidator';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();
  const fileRef = useRef();
  const [file, setFile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = async (f) => {
    setFile(f);
    setResult(null);
    setError(null);
    const v = await validateCSV(f);
    setValidation(v);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const onUpload = async () => {
    if (!file || !validation?.valid) return;
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await uploadCSV(fd);
      setResult(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload CSV</h1>
          <p className="page-sub">Drop your lead list and let Alfaleus do the research</p>
        </div>
      </div>

      {!result ? (
        <>
          {/* Drop Zone */}
          <div
            className={`drop-zone card-glass ${dragging ? 'drop-zone--active' : ''} ${file ? 'drop-zone--filled' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current.click()}
          >
            <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }}
              onChange={e => e.target.files[0] && handleFile(e.target.files[0])} />
            <div className="drop-icon">{file ? '📄' : '📂'}</div>
            {file ? (
              <div className="drop-file-info">
                <div className="drop-filename">{file.name}</div>
                <div className="drop-filesize">{(file.size / 1024).toFixed(1)} KB</div>
              </div>
            ) : (
              <div className="drop-text">
                <strong>Drop your CSV here</strong> or click to browse
                <div className="drop-hint">Supports: name+company, email, or domain columns</div>
              </div>
            )}
          </div>

          {/* Validation Status */}
          {validation && (
            <div className={`validation-panel card ${validation.valid ? 'validation--success' : 'validation--error'}`}>
              <div className="validation-header">
                <span className="validation-icon">{validation.valid ? '✅' : '❌'}</span>
                <strong>{validation.valid ? 'CSV is valid' : 'Validation failed'}</strong>
                {validation.total && <span className="validation-count">{validation.total} rows detected</span>}
              </div>
              {validation.errors?.map((err, i) => (
                <div key={i} className="validation-error">⚠ {err}</div>
              ))}
            </div>
          )}

          {/* Preview Table */}
          {validation?.preview?.length > 0 && (
            <div className="preview-section">
              <h3 className="section-title">Preview (first 5 rows)</h3>
              <div className="table-wrap card">
                <table className="data-table preview-table">
                  <thead>
                    <tr>{Object.keys(validation.preview[0]).map(h => <th key={h}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {validation.preview.map((row, i) => (
                      <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{v || '—'}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {error && <div className="error-banner">❌ {error}</div>}

          <div className="upload-actions">
            <button className="btn btn-ghost" onClick={() => navigate('/')}>Cancel</button>
            <button
              className="btn btn-primary"
              disabled={!validation?.valid || uploading}
              onClick={onUpload}
            >
              {uploading ? <><span className="spinner-sm" /> Uploading...</> : `⚡ Enrich ${validation?.total || ''} Leads`}
            </button>
          </div>
        </>
      ) : (
        <div className="upload-success card-glass">
          <div className="success-icon">🚀</div>
          <h2>Enrichment Started!</h2>
          <p>
            <strong className="highlight">{result.queued}</strong> leads queued for enrichment
            {result.skipped > 0 && <span className="text-muted"> ({result.skipped} skipped)</span>}
          </p>
          <div className="success-actions">
            <button className="btn btn-primary" onClick={() => navigate('/pipeline')}>
              📊 Watch Pipeline
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/')}>
              📋 View Dashboard
            </button>
          </div>
        </div>
      )}

      {/* Domain enrichment bonus */}
      <div className="domain-enrichment card-glass">
        <h3>🔍 Domain-Level Enrichment</h3>
        <p className="text-muted">Discover leads from a company domain automatically</p>
        <DomainForm />
      </div>
    </div>
  );
}

function DomainForm() {
  const navigate = useNavigate();
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const submit = async () => {
    if (!domain) return;
    setLoading(true);
    try {
      const { submitDomainLead } = await import('../api/client');
      const res = await submitDomainLead(domain);
      setResult(res.data);
    } catch (e) {
      setResult({ error: e.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="domain-form">
      <div className="domain-input-row">
        <input className="input" placeholder="e.g. stripe.com" value={domain}
          onChange={e => setDomain(e.target.value)} onKeyDown={e => e.key === 'Enter' && submit()} />
        <button className="btn btn-secondary" onClick={submit} disabled={loading || !domain}>
          {loading ? <span className="spinner-sm" /> : 'Discover Leads'}
        </button>
      </div>
      {result && !result.error && (
        <p className="domain-result">
          ✅ Discovered {result.discovered} leads from {result.domain}.
          <button className="link-btn" onClick={() => navigate('/')}>View in dashboard →</button>
        </p>
      )}
      {result?.error && <p className="error-text">{result.error}</p>}
    </div>
  );
}
