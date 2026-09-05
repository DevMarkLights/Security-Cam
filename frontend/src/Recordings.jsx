import { useState, useEffect } from 'react';
import './SecurityDashboard.css';

const local = false;
const API_BASE = local ? 'http://localhost:8086' : 'https://marks-pi.com';

export default function Recordings({ onNavigate }) {
  const [recordings, setRecordings] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    console.log(API_BASE)
    fetch(`${API_BASE}/security/recordings`)
      .then(r => r.json())
      .then(data => {
        setRecordings(data.recordings || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="recordings-page">
      <header className="header">
        <div className="header-left">
          <span className="logo">Lights Security</span>
          <div className="header-divider" />
          <span className="header-title">Recordings</span>
        </div>
        <div className="header-right">
          <button className="nav-btn" onClick={() => onNavigate('live')}>Live Feed</button>
          <div className="header-divider" />
          <span className="timestamp">
            {time.toLocaleTimeString('en-US', { hour12: true })}
          </span>
        </div>
      </header>

      <div className="recordings-body">
        <div className="recordings-player">
          {selected ? (
            <>
              <video
                key={selected}
                controls
                autoPlay
                className="recordings-video"
              >
                <source src={`${API_BASE}/security/recordings/${selected}`} type="video/mp4" />
              </video>
              <div className="recordings-filename">{selected.replace('.mp4', '')}</div>
            </>
          ) : (
            <div className="recordings-placeholder">
              <span className="feed-offline-icon">⬡</span>
              <span className="feed-offline-text">Select a recording</span>
            </div>
          )}
        </div>

        <div className="recordings-list">
          <div className="recordings-list-header">
            <span className="panel-title">Available Recordings</span>
            <span className="panel-badge">{recordings.length} FILES</span>
          </div>
          {loading && (
            <div className="recordings-empty">Loading...</div>
          )}
          {!loading && recordings.length === 0 && (
            <div className="recordings-empty">No recordings found</div>
          )}
          {recordings.map(f => (
            <div
              key={f}
              className={`recordings-list-item ${selected === f ? 'active' : ''}`}
              onClick={() => setSelected(f)}
            >
              <span className="recordings-date">{f.replace('.mp4', '')}</span>
              <span className="recordings-arrow">▶</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
