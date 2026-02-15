import { useEffect, useState } from 'react'
import './App.css'

const API = '/api'

function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <span className="stat-icon">{icon}</span>
      <div>
        <div className="stat-value">{value.toLocaleString()}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

function EventRow({ e }) {
  return (
    <tr>
      <td className="mono">{e.order_id?.slice(0, 12)}…</td>
      <td>{e.order_status ?? '—'}</td>
      <td>{e.payment_type ?? '—'}</td>
      <td className="mono amount">{e.payment_value != null ? Number(e.payment_value).toFixed(2) : '—'}</td>
      <td className="muted">{e.order_purchase_timestamp ?? '—'}</td>
    </tr>
  )
}

export default function App() {
  const [stats, setStats] = useState({ orders_seen: 0, payments_seen: 0, joined_count: 0, recent: [] })
  const [live, setLive] = useState([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let t
    const fetchStats = async () => {
      try {
        const r = await fetch(`${API}/stats`)
        if (!r.ok) throw new Error(r.statusText)
        const s = await r.json()
        setStats(s)
        setError(null)
      } catch (e) {
        setError(e.message)
      }
    }
    fetchStats()
    t = setInterval(fetchStats, 3000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const es = new EventSource(`${API}/events`)
    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (ev) => {
      try {
        const e = JSON.parse(ev.data)
        setLive((prev) => [e, ...prev].slice(0, 100))
      } catch (_) {}
    }
    return () => es.close()
  }, [])

  const recent = live.length ? live : stats.recent?.slice(-50).reverse() ?? []

  return (
    <div className="app">
      <header className="header">
        <h1>Real-time Analytics</h1>
        <p className="subtitle">Orders × Payments join stream</p>
        <div className="live-badge">
          <span className={connected ? 'dot live' : 'dot'} />
          {connected ? 'Live' : 'Connecting…'}
        </div>
      </header>

      {error && (
        <div className="banner error">
          Cannot reach backend: {error}. Is it running on port 8000?
        </div>
      )}

      <section className="stats">
        <StatCard label="Orders seen" value={stats.orders_seen ?? 0} icon="📦" />
        <StatCard label="Payments seen" value={stats.payments_seen ?? 0} icon="💳" />
        <StatCard label="Joined events" value={stats.joined_count ?? 0} icon="✅" />
      </section>

      <section className="events-section">
        <h2>Joined events {live.length ? '(live)' : '(recent)'}</h2>
        <div className="table-wrap">
          <table className="events-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Status</th>
                <th>Payment type</th>
                <th>Amount</th>
                <th>Purchase time</th>
              </tr>
            </thead>
            <tbody>
              {recent.length ? (
                recent.map((e, i) => <EventRow key={`${e.order_id}-${e.payment_value ?? ''}-${i}`} e={e} />)
              ) : (
                <tr>
                  <td colSpan={5} className="muted empty">No events yet. Start the producer.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
