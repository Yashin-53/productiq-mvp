import { useEffect, useState } from 'react';
import ConfidenceGauge from './ConfidenceGauge.jsx';

const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api';

function StatusBadge({ status }) {
  const labelMap = { verified: 'Verified', needs_review: 'Needs Review', not_found: 'Not Found', unverified: 'Unverified' };
  return <span className={`badge ${status}`}><span className="dot" />{labelMap[status] || status}</span>;
}

function Sidebar({ view, setView, reviewCount }) {
  const items = [
    ['dashboard', 'Dashboard'],
    ['enrich', 'Enrich Product'],
    ['dynamic', 'Try Your Own Data'],
    ['review', `Review Queue${reviewCount ? ` (${reviewCount})` : ''}`],
  ];
  return (
    <div className="sidebar">
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <div className="brand-name">ProductIQ</div>
          <div className="brand-sub">Product Intelligence</div>
        </div>
      </div>
      {items.map(([key, label]) => (
        <button key={key} className={`nav-item ${view === key ? 'active' : ''}`} onClick={() => setView(key)}>
          <span className="dot" />{label}
        </button>
      ))}
      <div className="sidebar-footer">
        UniHack MVP<br />
        Evidence-backed AI enrichment for industrial product data.
      </div>
    </div>
  );
}

function Dashboard({ setView, openProduct }) {
  const [data, setData] = useState(null);
  useEffect(() => { fetch(`${API}/products`).then(r => r.json()).then(setData); }, []);
  if (!data) return <div className="page-sub">Loading catalog...</div>;
  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Product Intelligence Dashboard</h1>
        <p className="page-sub">Minimal input, enriched into evidence-backed product records.</p>
      </div>
      <div className="grid-4">
        <div className="stat-card"><div className="stat-label">Products Enriched</div><div className="stat-value">{data.total}</div></div>
        <div className="stat-card"><div className="stat-label">Verified</div><div className="stat-value verified">{data.verified}</div></div>
        <div className="stat-card"><div className="stat-label">Needs Review</div><div className="stat-value review">{data.needs_review}</div></div>
        <div className="stat-card"><div className="stat-label">Avg Confidence</div><div className="stat-value accent">{data.avg_confidence}%</div></div>
      </div>
      <div className="panel">
        <table className="table">
          <thead><tr><th>Part Number</th><th>Brand</th><th>Category</th><th>Confidence</th><th>Status</th></tr></thead>
          <tbody>
            {data.products.map(p => (
              <tr key={p.id} className="clickable" onClick={() => openProduct(p.id)}>
                <td className="mono">{p.part_number}</td>
                <td>{p.brand}</td>
                <td>{p.category}</td>
                <td className="mono">{p.overall_confidence}%</td>
                <td><StatusBadge status={p.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <button className="btn" onClick={() => setView('enrich')}>+ Enrich Product</button>
        <button className="btn secondary" onClick={() => setView('dynamic')}>Try Your Own Data</button>
        <a className="btn secondary" href={`${API}/export/csv`} download style={{ textDecoration: 'none' }}>
          Export CSV
        </a>
      </div>
    </>
  );
}

function EnrichPicker({ onPick }) {
  const [candidates, setCandidates] = useState([]);
  useEffect(() => { fetch(`${API}/products/candidates`).then(r => r.json()).then(setCandidates); }, []);
  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Enrich a Product</h1>
        <p className="page-sub">Pick a sparse input record. The pipeline will research, extract, validate, and score confidence — with evidence for every field.</p>
      </div>
      <div className="picker-grid">
        {candidates.map(c => (
          <div key={c.id} className="picker-card" onClick={() => onPick(c.id)}>
            <div className="pn">{c.mfg_part_num}</div>
            <div className="desc">{c.part_desc}</div>
            <div className="brand">{c.brand}</div>
          </div>
        ))}
      </div>
    </>
  );
}

const PROCESS_STEPS = [
  'Normalizing input',
  'Discovering manufacturer sources',
  'Processing source documents',
  'Extracting attributes (AI)',
  'Cross-source validation',
  'Calculating confidence scores',
];

function Processing({ onDone }) {
  const [stepIdx, setStepIdx] = useState(0);
  useEffect(() => {
    if (stepIdx >= PROCESS_STEPS.length) { onDone(); return; }
    const t = setTimeout(() => setStepIdx(i => i + 1), 380);
    return () => clearTimeout(t);
  }, [stepIdx]);
  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Running Enrichment Pipeline</h1>
        <p className="page-sub">Evidence-first — no value is written without a traceable source.</p>
      </div>
      <div className="process-steps">
        {PROCESS_STEPS.map((s, i) => (
          <div key={s} className={`process-step ${i < stepIdx ? 'done' : i === stepIdx ? 'active' : ''}`}>
            <span className="check">{i < stepIdx ? '✓' : ''}</span>{s}
          </div>
        ))}
      </div>
    </>
  );
}

function AttrRow({ attr, onClick }) {
  const color =
    attr.status === 'verified' ? 'var(--verified)'
    : attr.status === 'high' ? '#a3d977'
    : attr.status === 'needs_review' ? 'var(--review)'
    : 'var(--conflict)';
  return (
    <div className="attr-row" onClick={onClick}>
      <div>
        <div className="attr-key">{attr.label}</div>
        <div className={`attr-value ${attr.value ? '' : 'empty'}`}>
          {attr.value ? `${attr.value}${attr.unit ? ' ' + attr.unit : ''}` : 'Not found'}
        </div>
      </div>
      {attr.value && <span className="conf-pill" style={{ background: `${color}22`, color }}>{attr.confidence}%{attr.conflict ? ' ⚠' : ''}</span>}
    </div>
  );
}

function EvidenceDrawer({ attr, onClose, onDecision }) {
  if (!attr) return null;
  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3>{attr.label}</h3>
            <div className="profile-sub">Attribute evidence & validation</div>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
          <ConfidenceGauge value={attr.confidence} size={120} label={attr.status === 'not_found' ? 'No Evidence' : attr.conflict ? 'Conflict' : 'Confidence'} />
        </div>

        {attr.conflict && (
          <div style={{ background: 'rgba(242,102,90,.1)', border: '1px solid var(--conflict)', borderRadius: 6, padding: '10px 14px', fontSize: 13, marginBottom: 10 }}>
            ⚠ Sources disagree on this value. Manufacturer-priority resolution applied; flagged for human review.
          </div>
        )}

        {attr.all_sources.length === 0 && (
          <div className="evidence-block"><div className="evidence-text">No supporting source document contained this attribute. Left blank rather than inferred.</div></div>
        )}

        {attr.all_sources.map((s, i) => (
          <div key={i} className="evidence-block">
            <div className="evidence-source">
              {s.source_url ? (
                <a href={s.source_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-2)', textDecoration: 'underline' }}>
                  {s.source_name} ↗
                </a>
              ) : s.source_name}
              {' · '}{s.source_type.replace('_', ' ')}
            </div>
            <div className="evidence-text">"{s.evidence}"</div>
            <div className="evidence-value">{s.value}</div>
          </div>
        ))}

        {attr.status !== 'not_found' && (
          <div className="pill-row">
            <button className="btn small" onClick={() => onDecision('accept')}>Accept</button>
            <button className="btn secondary small" onClick={() => onDecision('reject')}>Reject</button>
          </div>
        )}
      </div>
    </div>
  );
}

function ProductProfile({ productId, onBack }) {
  const [product, setProduct] = useState(null);
  const [drawerKey, setDrawerKey] = useState(null);

  const load = () => fetch(`${API}/products/${productId}`).then(r => r.json()).then(setProduct);
  useEffect(() => { load(); }, [productId]);

  if (!product) return <div className="page-sub">Loading...</div>;
  const attrs = Object.values(product.attributes);
  const drawerAttr = drawerKey ? product.attributes[drawerKey] : null;

  const decide = async (action) => {
    await fetch(`${API}/review/${productId}/${drawerKey}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }),
    });
    setDrawerKey(null);
    load();
  };

  return (
    <>
      <button className="btn secondary small" style={{ marginBottom: 18 }} onClick={onBack}>← Back</button>
      <div className="profile-header">
        <div>
          <div className="profile-title">{product.part_number}</div>
          <div className="profile-sub">{product.brand} · {product.category}</div>
          <div className="profile-sub">{product.short_description}</div>
          <div style={{ marginTop: 10 }}><StatusBadge status={product.status} /></div>
        </div>
        <ConfidenceGauge value={product.overall_confidence} label="Overall Confidence" />
      </div>

      <div className="panel" style={{ padding: '14px 18px', marginBottom: 20, display: 'flex', gap: 32 }}>
        <div><div className="attr-key">Completeness</div><div className="mono" style={{ fontWeight: 700 }}>{product.completeness_pct}% of schema fields</div></div>
        <div><div className="attr-key">Source Documents</div><div className="mono" style={{ fontWeight: 700 }}>{product.source_documents.length}</div></div>
        <div><div className="attr-key">Flagged for Review</div><div className="mono" style={{ fontWeight: 700 }}>{product.review_needed.length} attributes</div></div>
      </div>

      <p className="page-sub" style={{ marginBottom: 10 }}>Click any attribute to see its source evidence.</p>
      <div className="attr-grid">
        {attrs.map(a => <AttrRow key={a.key} attr={a} onClick={() => setDrawerKey(a.key)} />)}
      </div>

      <EvidenceDrawer attr={drawerAttr} onClose={() => setDrawerKey(null)} onDecision={decide} />
    </>
  );
}

function ReviewQueue({ openProduct }) {
  const [data, setData] = useState(null);
  const load = () => fetch(`${API}/review-queue`).then(r => r.json()).then(setData);
  useEffect(() => { load(); }, []);

  const decide = async (item, action) => {
    await fetch(`${API}/review/${item.product_id}/${item.attribute_key}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }),
    });
    load();
  };

  if (!data) return <div className="page-sub">Loading...</div>;
  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Human Review Queue</h1>
        <p className="page-sub">Low-confidence or conflicting attributes wait here instead of being silently guessed.</p>
      </div>
      <div className="panel">
        {data.items.length === 0 && <div style={{ padding: 24 }} className="page-sub">Queue is empty — everything is verified.</div>}
        {data.items.map((item, i) => (
          <div className="review-item" key={i}>
            <div className="review-item-head">
              <div>
                <span className="mono" style={{ fontWeight: 700, cursor: 'pointer' }} onClick={() => openProduct(item.product_id)}>{item.part_number}</span>
                {' — '}{item.attribute_label}
              </div>
              <span className="conf-pill" style={{ background: 'rgba(240,169,58,.15)', color: 'var(--review)' }}>{item.confidence}%{item.conflict ? ' conflict' : ''}</span>
            </div>
            {item.all_sources.map((s, j) => (
              <div key={j} style={{ fontSize: 12.5, color: 'var(--text-dim)', marginTop: 4 }}>
                <span style={{ color: 'var(--accent-2)' }}>{s.source_name}:</span> {s.value}
              </div>
            ))}
            <div className="pill-row">
              <button className="btn small" onClick={() => decide(item, 'accept')}>Accept top value</button>
              <button className="btn secondary small" onClick={() => decide(item, 'reject')}>Clear field</button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function DynamicTester() {
  const defaultForm = {
    partNumber: 'TEST-999',
    description: 'Test power supply',
    sourceText: 'Input 100-240V AC. Output 12V DC, 5A, 60W. DIN rail mounting.',
  };

  const [activeTab, setActiveTab] = useState('quick');
  const [form, setForm] = useState(defaultForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [csvResult, setCsvResult] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvError, setCsvError] = useState('');

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const handleQuickSubmit = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const payload = {
        mfg_part_num: form.partNumber,
        part_desc: form.description,
        e1_brand: '',
        unilog_brand: '',
        dib_brand: '',
        part_manuf: 'Test Manufacturer',
        documents: [
          {
            source_name: 'Quick Test',
            source_type: 'manufacturer_website',
            text: form.sourceText,
          },
        ],
      };

      const response = await fetch(`${API}/enrich/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Enrichment failed');
      }
      setResult(data);
    } catch (err) {
      setError(err.message || 'Unable to run enrichment.');
    } finally {
      setLoading(false);
    }
  };

  const handleCsvSubmit = async (event) => {
    event.preventDefault();
    if (!csvFile) {
      setCsvError('Select a CSV file first.');
      return;
    }

    setCsvLoading(true);
    setCsvError('');
    setCsvResult(null);

    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await fetch(`${API}/enrich/upload-csv`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'CSV upload failed');
      }

      setCsvResult(data);
    } catch (err) {
      setCsvError(err.message || 'Unable to upload CSV.');
    } finally {
      setCsvLoading(false);
    }
  };

  const attributeRows = result ? Object.values(result.attributes || {}) : [];

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Try Your Own Data</h1>
        <p className="page-sub">Run the real enrichment pipeline live on ad-hoc product data or upload a CSV using the challenge schema.</p>
      </div>

      <div className="panel" style={{ marginBottom: 18 }}>
        <div className="pill-row" style={{ marginBottom: 12 }}>
          <button className={`btn small ${activeTab === 'quick' ? '' : 'secondary'}`} onClick={() => setActiveTab('quick')}>Quick Test</button>
          <button className={`btn small ${activeTab === 'csv' ? '' : 'secondary'}`} onClick={() => setActiveTab('csv')}>Bulk CSV Upload</button>
        </div>

        {activeTab === 'quick' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
              <label className="field">
                <span>Part Number</span>
                <input value={form.partNumber} onChange={(e) => updateField('partNumber', e.target.value)} />
              </label>
              <label className="field">
                <span>Description</span>
                <input value={form.description} onChange={(e) => updateField('description', e.target.value)} />
              </label>
            </div>

            <label className="field" style={{ marginTop: 12 }}>
              <span>Source text</span>
              <textarea value={form.sourceText} onChange={(e) => updateField('sourceText', e.target.value)} rows={6} />
            </label>

            <div className="pill-row" style={{ marginTop: 12 }}>
              <button className="btn" onClick={handleQuickSubmit} disabled={loading}>
                {loading ? 'Running…' : 'Run Enrichment Pipeline'}
              </button>
            </div>

            {error && <div className="error-box">{error}</div>}

            {result && (
              <div style={{ marginTop: 18 }}>
                <div className="profile-header" style={{ alignItems: 'center' }}>
                  <div>
                    <div className="profile-title">{result.part_number}</div>
                    <div className="profile-sub">{result.brand} · {result.category}</div>
                    <div className="profile-sub">{result.short_description}</div>
                  </div>
                  <ConfidenceGauge value={result.overall_confidence} label="Overall Confidence" />
                </div>

                <div className="panel" style={{ marginTop: 16, padding: '12px 16px' }}>
                  <div className="attr-grid">
                    {attributeRows.map((attr) => (
                      <div key={attr.key} className="attr-row" style={{ cursor: 'default' }}>
                        <div>
                          <div className="attr-key">{attr.label}</div>
                          <div className={`attr-value ${attr.value ? '' : 'empty'}`}>
                            {attr.value ? `${attr.value}${attr.unit ? ' ' + attr.unit : ''}` : 'Not found'}
                          </div>
                        </div>
                        {attr.value && (
                          <span className="conf-pill">
                            {attr.confidence}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {attributeRows.filter((attr) => attr.primary_evidence).length > 0 && (
                  <div className="panel" style={{ marginTop: 16, padding: '12px 16px' }}>
                    <div className="attr-key" style={{ marginBottom: 10 }}>Evidence trail</div>
                    {attributeRows
                      .filter((attr) => attr.primary_evidence)
                      .slice(0, 5)
                      .map((attr) => (
                        <div key={attr.key} className="evidence-block" style={{ marginBottom: 8 }}>
                          <div className="evidence-source">{attr.label}</div>
                          <div className="evidence-text">"{attr.primary_evidence}"</div>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'csv' && (
          <div>
            <form onSubmit={handleCsvSubmit}>
              <label className="field">
                <span>CSV file</span>
                <input type="file" accept=".csv" onChange={(e) => setCsvFile(e.target.files[0])} />
              </label>

              <div className="pill-row" style={{ marginTop: 12 }}>
                <button className="btn" type="submit" disabled={csvLoading}>
                  {csvLoading ? 'Uploading…' : 'Upload & Enrich CSV'}
                </button>
              </div>
            </form>

            {csvError && <div className="error-box">{csvError}</div>}

            {csvResult && (
              <div style={{ marginTop: 18 }}>
                {csvResult.truncated && (
                  <div style={{ background: 'rgba(240,169,58,.12)', border: '1px solid var(--review)', borderRadius: 6, padding: '10px 14px', fontSize: 13, marginBottom: 16 }}>
                    ⚠ Your file has {csvResult.total_rows_in_file} valid rows. Processed the first {csvResult.rows_processed} — capped for responsiveness in this MVP (not silently dropped, just limited per batch).
                  </div>
                )}
                <div className="panel" style={{ padding: '12px 16px' }}>
                  <div className="attr-key">Rows processed: {csvResult.rows_processed}{csvResult.truncated ? ` / ${csvResult.total_rows_in_file}` : ''}</div>
                  <div className="profile-sub">Average confidence: {csvResult.avg_confidence}%</div>
                </div>

                <div className="attr-grid" style={{ marginTop: 16 }}>
                  {csvResult.results.map((item) => (
                    <div key={item.id} className="attr-row" style={{ cursor: 'default' }}>
                      <div>
                        <div className="attr-key">{item.part_number}</div>
                        <div className="attr-value">{item.category}</div>
                      </div>
                      <span className="conf-pill">{item.overall_confidence}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default function App() {
  const [view, setView] = useState('dashboard');
  const [selectedId, setSelectedId] = useState(null);
  const [pendingId, setPendingId] = useState(null);
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    fetch(`${API}/review-queue`).then(r => r.json()).then(d => setReviewCount(d.count));
  }, [view]);

  const openProduct = (id) => { setSelectedId(id); setView('profile'); };

  const handlePick = (id) => { setPendingId(id); setView('processing'); };
  const handleProcessingDone = async () => {
    await fetch(`${API}/products/${pendingId}/enrich`, { method: 'POST' });
    setSelectedId(pendingId);
    setView('profile');
  };

  return (
    <div className="app-shell">
      <Sidebar
        view={view === 'profile' || view === 'processing' ? 'enrich' : view}
        setView={setView}
        reviewCount={reviewCount}
      />
      <div className="main">
        {view === 'dashboard' && <Dashboard setView={setView} openProduct={openProduct} />}
        {view === 'enrich' && <EnrichPicker onPick={handlePick} />}
        {view === 'processing' && <Processing onDone={handleProcessingDone} />}
        {view === 'profile' && <ProductProfile productId={selectedId} onBack={() => setView('dashboard')} />}
        {view === 'review' && <ReviewQueue openProduct={openProduct} />}
        {view === 'dynamic' && <DynamicTester />}
      </div>
    </div>
  );
}
