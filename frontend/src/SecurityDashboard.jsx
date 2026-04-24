import { useState, useEffect, useRef, useCallback } from 'react';
import './SecurityDashboard.css';

// const API_BASE = 'http://localhost:8086';
const API_BASE = 'https://marks-pi.com';

const WEB_SOCKET_BASE = 'wss://marks-pi.com/security/ws/stream'
// const WEB_SOCKET_BASE = 'ws://localhost:8086/security/ws/stream'

const STREAM_URL = 'http://localhost:8086/security/stream'


export default function SecurityDashboard() {
  const [tracking, setTracking] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [feedOnline, setFeedOnline] = useState(true);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [absX, setAbsX] = useState('');
  const [absY, setAbsY] = useState('');
  const [logs, setLogs] = useState([]);
  const [time, setTime] = useState(new Date());
  const logRef = useRef(null);
  const wsRef = useRef(null);
  const [frameSrc, setFrameSrc] = useState('');

  // Clock
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Scroll log to bottom
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  useEffect(() => {
    const ws = new WebSocket(WEB_SOCKET_BASE);
    ws.onmessage = (e) => setFrameSrc(`data:image/jpeg;base64,${e.data}`);
    ws.onerror = () => setFeedOnline(false);
    ws.onclose = () => setFeedOnline(false);
    ws.onopen = () => setFeedOnline(true);
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const addLog = useCallback((msg, type = 'info') => {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: true });
    setLogs(prev => [...prev.slice(-19), { msg, type, ts }]);
  }, []);

  const request = useCallback(async (method, path, body = null) => {
    try {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(`${API_BASE}${path}`, opts);
      return res;
    } catch (err) {
      addLog(`NETWORK ERROR: ${err.message}`, 'error');
      return null;
    }
  }, [addLog]);

  // ─── HANDLERS ───

  const handleTrackToggle = async () => {
    const next = !tracking;
    const res = await request('GET', `/security/track?track=${next}`);
    if (res) {
      setTracking(next);
      addLog(`AUTO TRACK ${next ? 'ENABLED' : 'DISABLED'}`, next ? 'success' : 'info');
    } else {
      addLog('FAILED TO TOGGLE TRACKING', 'error');
    }
  };

  const handleMove = async (direction) => {
    const res = await request('POST', '/security/move', { direction });
    if (res?.ok) {
      addLog(`MOVE → ${direction.toUpperCase()}`, 'success');
    } else {
      addLog(`MOVE FAILED: ${direction}`, 'error');
    }
  };

  const handleScan = async (start) => {
    if (scanning) return;

    if(start){
      setScanning(true);
      addLog('SCAN SEQUENCE INITIATED', 'info');
      const res = await request('GET', '/security/scan');

      if (res?.ok) {
        addLog('SCAN RUNNING IN BACKGROUND', 'success');
      } else {
        addLog('SCAN FAILED TO START', 'error');
      }
      setTimeout(() => setScanning(false), 2000);

    } else{
      setScanning(false);
      addLog('SCAN SEQUENCE STOPPED', 'info');
      const res = await request('GET', '/security/scanStop');

      if (res?.ok) {
        addLog('SCAN STOPPED IN BACKGROUND', 'success');
      } else {
        addLog('SCAN FAILED TO STOP', 'error');
      }
      setTimeout(() => setScanning(false), 2000);
    }
    
  };

  const handleGoToPreset = async () => {
    const res = await request('GET', '/security/goToPreset');
    if (res?.ok) {
      addLog('RETURNING TO PRESET HOME', 'success');
    } else {
      addLog('FAILED TO GO TO PRESET', 'error');
    }
  };

  const handleSetPreset = async () => {
    const res = await request('GET', '/security/setPreset');
    if (res?.ok) {
      addLog('PRESET POSITION SAVED', 'success');
    } else {
      addLog('FAILED TO SAVE PRESET', 'error');
    }
  };

  const handleAbsPosition = async () => {
    const x = parseFloat(absX);
    const y = parseFloat(absY);
    if (isNaN(x) || isNaN(y)) {
      addLog('INVALID COORDINATES', 'error');
      return;
    }
    if (x < 0 || x > 360) { addLog('X MUST BE 0–360', 'error'); return; }
    if (y < 0 || y > 90) { addLog('Y MUST BE 0–90', 'error'); return; }

    const res = await request('POST', '/security/goToPostion', { x, y });
    if (res?.ok) {
      setPosition({ x, y });
      addLog(`POSITION SET → X:${x} Y:${y}`, 'success');
    } else {
      addLog(`POSITION FAILED → X:${x} Y:${y}`, 'error');
    }
  };

  const ptzButtons = [
    { label: '↖', dir: 'LeftUp',   pos: [0,0] },
    { label: '↑', dir: 'Up',       pos: [0,1] },
    { label: '↗', dir: 'RightUp',  pos: [0,2] },
    { label: '←', dir: 'Left',     pos: [1,0] },
    { label: null, dir: null,      pos: [1,1] },
    { label: '→', dir: 'Right',    pos: [1,2] },
    { label: '↙', dir: 'LeftDown', pos: [2,0] },
    { label: '↓', dir: 'Down',     pos: [2,1] },
    { label: '↘', dir: 'RightDown',pos: [2,2] },
  ];

  return (
    <div className="dashboard">

      {/* ─── HEADER ─── */}
      <header className="header">
        <div className="header-left">
          <span className="logo">Lights Security</span>
          <div className="header-divider" />
          <span className="header-title">Security Control System</span>
        </div>
        <div className="header-right">
          <div className="status-indicator">
            <span className={`status-dot ${feedOnline ? '' : 'offline'}`} />
            {feedOnline ? 'ONLINE' : 'OFFLINE'}
          </div>
          <div className="header-divider" />
          <span className="timestamp">
            {time.toLocaleTimeString('en-US', { hour12: true })}
          </span>
        </div>
      </header>

      {/* ─── FEED AREA ─── */}
      <main className="feed-area">
        <div className="feed-container">
          <div className="feed-corner tl" />
          <div className="feed-corner tr" />
          <div className="feed-corner bl" />
          <div className="feed-corner br" />
          <div className="feed-rec">
            <span className="rec-dot" />
            REC
          </div>
          {feedOnline ? (
            <img className="feed-img" src={frameSrc} alt="Camera Feed" />
          ) : (
            <div className="feed-offline">
              <span className="feed-offline-icon">⬡</span>
              <span className="feed-offline-text">Signal Lost</span>
            </div>
          )}
        </div>

        {/* Position bar */}
        <div className="position-bar">
          <span className="pos-label">PAN</span>
          <span className="pos-value">{position.x.toFixed(1)}°</span>
          <div className="pos-divider" />
          <span className="pos-label">TILT</span>
          <span className="pos-value">{position.y.toFixed(1)}°</span>
          <div className="pos-divider" />
          <span className="pos-label">CAM</span>
          <span className="pos-value">IP2M-841</span>
          <span className="pos-mode">{tracking ? 'AUTO TRACK' : scanning ? 'SCANNING' : 'MANUAL'}</span>
        </div>

        {/* Activity Log */}
        <div
          ref={logRef}
          style={{ minHeight: '100px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}
        >
          {logs.length === 0 && (
            <div className="log-entry">SYSTEM READY // AWAITING INPUT</div>
          )}
          {logs.map((l, i) => (
            <div key={i} className={`log-entry ${l.type}`}>
              [{l.ts}] {l.msg}
            </div>
          ))}
        </div>
      </main>

      {/* ─── SIDEBAR ─── */}
      <aside className="sidebar">

        {/* Auto Track */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">AI Tracking</span>
            <span className="panel-badge">{tracking ? 'ACTIVE' : 'IDLE'}</span>
          </div>
          <div
            className={`toggle-row ${tracking ? 'active' : ''}`}
            onClick={handleTrackToggle}
          >
            <div className="toggle-label">
              Auto Track
              <small>Follow detected motion</small>
            </div>
            <label className="toggle-switch" onClick={e => e.stopPropagation()}>
              <input type="checkbox" checked={tracking} onChange={handleTrackToggle} />
              <span className="toggle-slider" />
            </label>
          </div>
        </div>

        {/* PTZ Controls */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">PTZ Control</span>
            <span className="panel-badge">MANUAL</span>
          </div>
          <div className="ptz-grid">
            {ptzButtons.map((btn, i) =>
              btn.dir === null ? (
                <div key={i} className="ptz-btn center">PTZ</div>
              ) : (
                <button
                  key={i}
                  className="ptz-btn"
                  onClick={() => handleMove(btn.dir)}
                  title={btn.dir}
                >
                  {btn.label}
                </button>
              )
            )}
          </div>
        </div>

        {/* Preset */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Preset Position</span>
            <span className="panel-badge">SLOT 1</span>
          </div>
          <button className="action-btn" onClick={handleGoToPreset}>
            ⌖ Return to Home
          </button>
          <button className="action-btn danger" onClick={handleSetPreset}>
            ◎ Save Current as Home
          </button>
        </div>

        {/* Absolute Position */}
        <div className="panel" style={{pointerEvents: 'none', opacity: .5}}>
          <div className="panel-header">
            <span className="panel-title">Absolute Position</span>
            <span className="panel-badge">ABS</span>
          </div>
          <div className="position-inputs">
            <div className="input-group">
              <span className="input-label">PAN (X)</span>
              <input
                className="input-field"
                type="number"
                min="0"
                max="360"
                placeholder="0"
                value={absX}
                onChange={e => setAbsX(e.target.value)}
              />
              <span className="input-hint">0 – 360°</span>
            </div>
            <div className="input-group">
              <span className="input-label">TILT (Y)</span>
              <input
                className="input-field"
                type="number"
                min="0"
                max="90"
                placeholder="0"
                value={absY}
                onChange={e => setAbsY(e.target.value)}
              />
              <span className="input-hint">0 – 90°</span>
            </div>
          </div>
          <button className="action-btn" onClick={handleAbsPosition}>
            ⊕ Go to Position
          </button>
        </div>

        {/* Scan */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Auto Scan</span>
            <span className="panel-badge">{scanning ? 'RUNNING' : 'READY'}</span>
          </div>
          <button
            className={`action-btn ${scanning ? 'active-state' : ''}`}
            onClick={() => handleScan(true)}
            disabled={scanning}
          >
            {scanning ? '◈ Scanning...' : '◈ Start Scan Sequence'}
          </button>
          <button
            className={`action-btn ${scanning ? 'active-state' : ''}`}
            onClick={() => handleScan(false)}
            disabled={scanning}
          >
            {scanning ? '◈ Scanning...' : '◈ Stop Scan Sequence'}
          </button>
        </div>

      </aside>
    </div>
  );
}
