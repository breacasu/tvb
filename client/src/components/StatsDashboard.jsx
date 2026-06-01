import React, { useState, useEffect } from 'react';
import './StatsDashboard.css';

const ITEMS_PER_PAGE = 4;

function StatsDashboard() {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadStats();
  }, []);

  const parseCSVLine = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (const ch of line) {
      if (ch === '"') { inQuotes = !inQuotes; continue; }
      if (ch === ';' && !inQuotes) { result.push(current); current = ''; continue; }
      current += ch;
    }
    result.push(current);
    return result;
  };

  const loadStats = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.readStats();
      if (result.error) {
        setError(result.error);
        return;
      }
      const lines = result.content.split('\n');
      if (lines.length < 2) return;
      const clean = lines.map(l => l.replace(/\r$/, '')).filter(l => l.trim());
      const headers = parseCSVLine(clean[0]);
      const data = clean.slice(1).filter(line => line.trim()).map(line => {
        const values = parseCSVLine(line);
        const obj = {};
        headers.forEach((header, idx) => {
          obj[header] = values[idx] || '';
        });
        return obj;
      }).reverse();
      setStats(data);
      setPage(1);
    }
  };

  const totalPages = Math.max(1, Math.ceil(stats.length / ITEMS_PER_PAGE));
  const startIdx = (page - 1) * ITEMS_PER_PAGE;
  const pageItems = stats.slice(startIdx, startIdx + ITEMS_PER_PAGE);
  const maxVisiblePages = 5;

  const getPageNumbers = () => {
    const pages = [];
    let start = Math.max(1, page - Math.floor(maxVisiblePages / 2));
    let end = Math.min(totalPages, start + maxVisiblePages - 1);
    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  };

  const [tooltip, setTooltip] = useState({ show: false, text: '', x: 0, y: 0 });

  const handleMouseEnter = (e, text) => {
    const rect = e.target.getBoundingClientRect();
    setTooltip({ show: true, text, x: rect.left, y: rect.bottom + 4 });
  };

  const handleMouseLeave = () => {
    setTooltip({ show: false, text: '', x: 0, y: 0 });
  };

  return (
    <div className="stats-dashboard">
      <h3>Stats</h3>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Filename</th>
            <th>Original</th>
            <th>New</th>
            <th>Reduction</th>
            <th>Duration</th>
            <th>Command</th>
          </tr>
        </thead>
        <tbody>
          {pageItems.map((row, idx) => (
            <tr key={idx}>
              <td>{row['Encoded Date'] || row.date}</td>
              <td className="filename-cell">{row['Filename'] || row.filename}</td>
              <td>{row['Original Size'] || row.originalSize}</td>
              <td>{row['New Size'] || row.newSize}</td>
              <td>{row['Percentage'] || row.percentage}</td>
              <td>{row['Duration of Encode'] || row.duration}</td>
              <td className="command-cell"
                onMouseEnter={(e) => handleMouseEnter(e, row['Command'] || row.command)}
                onMouseLeave={handleMouseLeave}>
                {row['Command'] || row.command}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {stats.length > ITEMS_PER_PAGE && (
        <div className="pagination">
          <button onClick={() => setPage(1)} disabled={page === 1} title="First page">&lt;&lt;</button>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} title="Previous page">&lt;</button>
          {getPageNumbers().map(p => (
            <button key={p} className={p === page ? 'active' : ''} onClick={() => setPage(p)}>{p}</button>
          ))}
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} title="Next page">&gt;</button>
          <button onClick={() => setPage(totalPages)} disabled={page === totalPages} title="Last page">&gt;&gt;</button>
          <span className="page-info">Page {page} of {totalPages} ({stats.length} entries)</span>
        </div>
      )}

      {tooltip.show && (
        <div className="command-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          {tooltip.text}
        </div>
      )}
    </div>
  );
}

export default StatsDashboard;