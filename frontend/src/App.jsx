import { useEffect, useState } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CreditCard,
  Database,
  LayoutDashboard,
  Menu,
  Radar,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Table2,
  X,
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const initialForm = {
  amount: '313.30',
  hour: '3',
  transaction_frequency: '6',
  average_amount: '272.06',
  recipient_is_new: false,
  device_changed: true,
  location_changed: false,
  transaction_type: 'transfer',
  account_age_days: '134',
  previous_failed_transactions: '0',
}

const navigation = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'analyze', label: 'Analyze transaction', icon: Radar },
  { id: 'history', label: 'Transaction history', icon: Table2 },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
]

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed with status ${response.status}`)
  }
  return response.json()
}

function formatTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0)
}

function riskClass(level) {
  return level?.toLowerCase().replace(' ', '-') || 'safe'
}

function App() {
  const [view, setView] = useState('dashboard')
  const [isMobileNavOpen, setMobileNavOpen] = useState(false)
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [apiStatus, setApiStatus] = useState('checking')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function loadWorkspace() {
    setLoading(true)
    try {
      const [health, history, stats] = await Promise.all([
        request('/health'),
        request('/transactions?limit=50'),
        request('/analytics'),
      ])
      setApiStatus(health.status === 'ok' ? 'online' : 'offline')
      setTransactions(history)
      setAnalytics(stats)
      setError('')
    } catch (loadError) {
      setApiStatus('offline')
      setError(loadError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWorkspace()
  }, [])

  function updateField(event) {
    const { name, value, type, checked } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  async function analyzeTransaction(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        amount: Number(form.amount),
        hour: Number(form.hour),
        transaction_frequency: Number(form.transaction_frequency),
        average_amount: Number(form.average_amount),
        recipient_is_new: Number(form.recipient_is_new),
        device_changed: Number(form.device_changed),
        location_changed: Number(form.location_changed),
        transaction_type: form.transaction_type,
        account_age_days: Number(form.account_age_days),
        previous_failed_transactions: Number(form.previous_failed_transactions),
      }
      const prediction = await request('/predict', { method: 'POST', body: JSON.stringify(payload) })
      setResult(prediction)
      setView('analyze')
      await loadWorkspace()
    } catch (submitError) {
      setError(submitError.message)
    } finally {
      setSubmitting(false)
    }
  }

  function navigate(nextView) {
    setView(nextView)
    setMobileNavOpen(false)
  }

  const flaggedCount = (analytics?.suspicious_count || 0) + (analytics?.high_risk_count || 0)

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isMobileNavOpen ? 'sidebar-open' : ''}`}>
        <div className="brand-lockup">
          <div className="brand-mark"><ShieldCheck size={21} strokeWidth={2.4} /></div>
          <div><strong>RazorGuard</strong><span>AI risk operations</span></div>
          <button className="icon-button sidebar-close" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="sidebar-label">Workspace</div>
        <nav className="main-nav">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${view === id ? 'nav-active' : ''}`} onClick={() => navigate(id)}>
              <Icon size={18} /><span>{label}</span>{view === id && <ChevronRight className="nav-arrow" size={16} />}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="system-card">
            <span className={`status-dot ${apiStatus}`} />
            <div><strong>API connection</strong><span>{apiStatus === 'online' ? 'Model service online' : 'Service unavailable'}</span></div>
          </div>
          <span className="version-label">RAZORGUARD / v1.0.0</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="icon-button menu-toggle" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="breadcrumbs"><span>Risk operations</span><ChevronRight size={14} /><strong>{navigation.find((item) => item.id === view)?.label}</strong></div>
          <div className="topbar-actions"><span className="live-pill"><span className="pulse-dot" /> Live environment</span><button className="avatar" aria-label="User profile">RG</button></div>
        </header>

        <div className="page-wrap">
          {error && <div className="error-banner"><AlertCircle size={17} /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error"><X size={16} /></button></div>}
          {view === 'dashboard' && <Dashboard analytics={analytics} transactions={transactions} flaggedCount={flaggedCount} loading={loading} onNavigate={navigate} />}
          {view === 'analyze' && <Analyze form={form} result={result} submitting={submitting} updateField={updateField} onSubmit={analyzeTransaction} />}
          {view === 'history' && <History transactions={transactions} loading={loading} onRefresh={loadWorkspace} />}
          {view === 'analytics' && <Analytics analytics={analytics} transactions={transactions} loading={loading} />}
        </div>
      </main>
    </div>
  )
}

function PageIntro({ eyebrow, title, description, action }) {
  return <div className="page-intro"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>
}

function Dashboard({ analytics, transactions, flaggedCount, loading, onNavigate }) {
  return <>
    <PageIntro eyebrow="Command center / 01" title="Good morning, operator." description="Monitor transaction risk, investigate signals, and keep decisions moving with confidence." action={<button className="button button-primary" onClick={() => onNavigate('analyze')}><Radar size={17} /> Analyze transaction</button>} />
    <div className="metric-grid">
      <MetricCard icon={Activity} label="Transactions reviewed" value={analytics?.total_predictions ?? '—'} note="Across this workspace" tone="cyan" loading={loading} />
      <MetricCard icon={AlertCircle} label="Flagged for review" value={flaggedCount} note="Suspicious + high risk" tone="amber" loading={loading} />
      <MetricCard icon={ShieldCheck} label="High-risk decisions" value={analytics?.high_risk_count ?? '—'} note="Require human review" tone="red" loading={loading} />
      <MetricCard icon={BarChart3} label="Average risk score" value={analytics ? `${analytics.average_risk_score.toFixed(1)}%` : '—'} note="Across analyzed traffic" tone="violet" loading={loading} />
    </div>
    <div className="dashboard-grid">
      <section className="panel hero-panel">
        <div className="panel-kicker"><Sparkles size={15} /> Live decisioning</div>
        <h2>Turn uncertainty into a<br /><em>clear next action.</em></h2>
        <p>Submit a transaction for an instant model-backed risk assessment with explainable signals and a recorded audit trail.</p>
        <button className="text-button" onClick={() => onNavigate('analyze')}>Open risk checker <ArrowUpRight size={16} /></button>
        <div className="hero-lines"><span /><span /><span /><span /></div>
      </section>
      <section className="panel distribution-panel">
        <PanelHeader title="Risk distribution" meta="Current workspace" icon={SlidersHorizontal} />
        {analytics ? <div className="distribution-list"><RiskBar label="Safe" count={analytics.safe_count} total={analytics.total_predictions} tone="safe" /><RiskBar label="Suspicious" count={analytics.suspicious_count} total={analytics.total_predictions} tone="suspicious" /><RiskBar label="High risk" count={analytics.high_risk_count} total={analytics.total_predictions} tone="high-risk" /></div> : <EmptyState compact text="Waiting for analytics" />}
        <div className="distribution-foot"><span>Flagged rate</span><strong>{analytics?.total_predictions ? `${((flaggedCount / analytics.total_predictions) * 100).toFixed(1)}%` : '—'}</strong></div>
      </section>
    </div>
    <section className="panel recent-panel">
      <PanelHeader title="Recent decisions" meta="Latest 5" icon={Clock3} action={<button className="text-button muted" onClick={() => onNavigate('history')}>View history <ArrowUpRight size={15} /></button>} />
      <TransactionTable transactions={transactions.slice(0, 5)} loading={loading} />
    </section>
  </>
}

function Analyze({ form, result, submitting, updateField, onSubmit }) {
  return <>
    <PageIntro eyebrow="Decision engine / 02" title="Analyze a transaction." description="Run a real-time assessment using the same feature schema and trained model as the API." />
    <div className="analyze-layout">
      <form className="panel transaction-form" onSubmit={onSubmit}>
        <div className="form-heading"><div className="section-icon cyan"><CreditCard size={18} /></div><div><h2>Transaction signals</h2><p>Provide the details available at authorization time.</p></div></div>
        <div className="field-grid">
          <Field label="Transaction amount" name="amount" type="number" value={form.amount} onChange={updateField} min="0.01" step="0.01" prefix="$" />
          <Field label="Average amount" name="average_amount" type="number" value={form.average_amount} onChange={updateField} min="0.01" step="0.01" prefix="$" />
          <Field label="Transaction hour" name="hour" type="number" value={form.hour} onChange={updateField} min="0" max="23" suffix="24h" />
          <Field label="Transactions this period" name="transaction_frequency" type="number" value={form.transaction_frequency} onChange={updateField} min="1" max="30" />
          <Field label="Account age" name="account_age_days" type="number" value={form.account_age_days} onChange={updateField} min="1" max="3000" suffix="days" />
          <Field label="Previous failed attempts" name="previous_failed_transactions" type="number" value={form.previous_failed_transactions} onChange={updateField} min="0" max="8" />
          <label className="field"><span>Transaction type</span><select name="transaction_type" value={form.transaction_type} onChange={updateField}><option value="purchase">Purchase</option><option value="transfer">Transfer</option><option value="withdrawal">Withdrawal</option><option value="subscription">Subscription</option></select></label>
        </div>
        <div className="signal-block"><div className="signal-label">Context changes <span>Binary risk signals</span></div><div className="toggle-grid"><Toggle name="recipient_is_new" label="New recipient" checked={form.recipient_is_new} onChange={updateField} /><Toggle name="device_changed" label="Device changed" checked={form.device_changed} onChange={updateField} /><Toggle name="location_changed" label="Location changed" checked={form.location_changed} onChange={updateField} /></div></div>
        <div className="form-actions"><span><Database size={14} /> Saved to audit trail</span><button className="button button-primary" type="submit" disabled={submitting}>{submitting ? <><RefreshCw className="spin" size={17} /> Analyzing...</> : <><Radar size={17} /> Analyze transaction</>}</button></div>
      </form>
      <ResultCard result={result} />
    </div>
  </>
}

function ResultCard({ result }) {
  if (!result) return <section className="panel result-card result-empty"><div className="empty-orbit"><Radar size={27} /></div><h2>Awaiting analysis</h2><p>Submit transaction details to see the model decision, risk signals, and recommended action here.</p><div className="empty-note"><ShieldCheck size={15} /> Powered by RazorGuard AI</div></section>
  const levelClass = riskClass(result.risk_level)
  return <section className={`panel result-card result-${levelClass}`}><div className="result-top"><div><div className="eyebrow">Decision returned</div><h2>{result.risk_level}</h2></div><span className={`risk-badge ${levelClass}`}>{result.risk_level}</span></div><div className="score-ring" style={{ '--score': `${result.risk_score * 3.6}deg` }}><div><strong>{result.risk_score.toFixed(1)}</strong><span>risk score</span></div></div><div className="result-action"><span>Recommended action</span><strong>{result.recommended_action}</strong></div><div className="reasons"><div className="reasons-title">Why this decision <span>{result.transaction_id}</span></div>{result.reasons.map((reason) => <div className="reason" key={reason}><CheckCircle2 size={15} />{reason}</div>)}</div></section>
}

function History({ transactions, loading, onRefresh }) {
  return <><PageIntro eyebrow="Audit trail / 03" title="Transaction history." description="Every analyzed transaction is recorded here for review and operational follow-up." action={<button className="button button-secondary" onClick={onRefresh}><RefreshCw size={16} /> Refresh</button>} /><section className="panel table-panel"><PanelHeader title="All recent decisions" meta={`${transactions.length} records loaded`} icon={Table2} /><TransactionTable transactions={transactions} loading={loading} /></section></>
}

function Analytics({ analytics, transactions, loading }) {
  const total = analytics?.total_predictions || 0
  const flagged = (analytics?.suspicious_count || 0) + (analytics?.high_risk_count || 0)
  return <><PageIntro eyebrow="Signal intelligence / 04" title="Analytics overview." description="Understand how risk is moving across the decisions recorded by the model." /><div className="analytics-kpis"><MetricCard icon={Activity} label="Total transactions" value={analytics?.total_predictions ?? '—'} note="Stored predictions" tone="cyan" loading={loading} /><MetricCard icon={AlertCircle} label="Detected risk" value={flagged} note="Suspicious or high risk" tone="amber" loading={loading} /><MetricCard icon={BarChart3} label="Flagged rate" value={total ? `${((flagged / total) * 100).toFixed(1)}%` : '—'} note="Share of decisions" tone="red" loading={loading} /></div><div className="analytics-grid"><section className="panel chart-panel"><PanelHeader title="Risk distribution" meta="All recorded decisions" icon={BarChart3} />{analytics ? <div className="large-bars"><LargeBar label="Safe" value={analytics.safe_count} total={total} tone="safe" /><LargeBar label="Suspicious" value={analytics.suspicious_count} total={total} tone="suspicious" /><LargeBar label="High risk" value={analytics.high_risk_count} total={total} tone="high-risk" /></div> : <EmptyState text="No analytics available" />}</section><section className="panel insight-panel"><PanelHeader title="Operational readout" meta="Model signals" icon={Search} /><div className="insight"><span className="insight-index">01</span><div><strong>Average risk score</strong><p>{analytics ? `${analytics.average_risk_score.toFixed(1)}% across all decisions.` : 'Waiting for model data.'}</p></div></div><div className="insight"><span className="insight-index">02</span><div><strong>Latest activity</strong><p>{transactions[0] ? `Last decision ${formatTime(transactions[0].created_at)}.` : 'No transactions recorded yet.'}</p></div></div><div className="insight"><span className="insight-index">03</span><div><strong>Audit coverage</strong><p>Predictions are persisted for review and follow-up.</p></div></div></section></div></>
}

function MetricCard({ icon: Icon, label, value, note, tone, loading }) { return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18} /></div><div className="metric-content"><span>{label}</span><strong>{loading ? <i className="skeleton short" /> : value}</strong><small>{note}</small></div><ArrowUpRight className="metric-arrow" size={16} /></div> }
function PanelHeader({ title, meta, icon: Icon, action }) { return <div className="panel-header"><div className="panel-title"><Icon size={17} /><h2>{title}</h2><span>{meta}</span></div>{action}</div> }
function RiskBar({ label, count, total, tone }) { return <div className="risk-bar"><div><span>{label}</span><strong>{count}</strong></div><div className="bar-track"><span className={tone} style={{ width: `${total ? Math.max((count / total) * 100, count ? 3 : 0) : 0}%` }} /></div></div> }
function LargeBar({ label, value, total, tone }) { return <div className="large-bar"><div className="large-bar-label"><span><i className={`legend-dot ${tone}`} />{label}</span><strong>{value}<small>{total ? ` / ${((value / total) * 100).toFixed(1)}%` : ''}</small></strong></div><div className="large-track"><span className={tone} style={{ width: `${total ? Math.max((value / total) * 100, value ? 3 : 0) : 0}%` }} /></div></div> }
function Field({ label, name, type, value, onChange, min, max, step, prefix, suffix }) { return <label className="field"><span>{label}</span><div className="input-wrap">{prefix && <i>{prefix}</i>}<input name={name} type={type} value={value} onChange={onChange} min={min} max={max} step={step} required />{suffix && <em>{suffix}</em>}</div></label> }
function Toggle({ name, label, checked, onChange }) { return <label className="toggle"><input type="checkbox" name={name} checked={checked} onChange={onChange} /><span className="toggle-track"><span /></span><b>{label}</b></label> }
function TransactionTable({ transactions, loading }) { if (loading) return <div className="table-loading"><RefreshCw className="spin" size={18} /> Loading transaction history...</div>; if (!transactions.length) return <EmptyState text="No transactions analyzed yet" />; return <div className="table-scroll"><table><thead><tr><th>Transaction</th><th>Amount</th><th>Risk level</th><th>Score</th><th>Timestamp</th><th /></tr></thead><tbody>{transactions.map((transaction) => <tr key={`${transaction.id}-${transaction.transaction_id}`}><td><div className="transaction-id"><span className="table-avatar"><CreditCard size={14} /></span><div><strong>{transaction.transaction_id}</strong><small>{transaction.transaction_type}</small></div></div></td><td>{formatMoney(transaction.amount)}</td><td><span className={`risk-badge ${riskClass(transaction.risk_level)}`}><i />{transaction.risk_level}</span></td><td><strong className="score-value">{transaction.risk_score.toFixed(1)}%</strong></td><td className="timestamp">{formatTime(transaction.created_at)}</td><td><ChevronRight size={16} className="row-chevron" /></td></tr>)}</tbody></table></div> }
function EmptyState({ text, compact = false }) { return <div className={`empty-state ${compact ? 'compact' : ''}`}><div className="empty-icon"><Database size={18} /></div><span>{text}</span></div> }

export default App