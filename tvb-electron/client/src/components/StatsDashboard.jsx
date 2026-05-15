import React, { useState, useEffect } from 'react';
import './StatsDashboard.css';

function StatsDashboard() {
  const [stats, setStats] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.readStats();
      if (result.error) {
        setError(result.error);
        return;
      }
      // Parse CSV content
      const lines = result.content.split('\n');
      if (lines.length < 2) return;
      const headers = lines[0].split(';');
      const data = lines.slice(1).filter(line => line.trim()).map(line => {
        const values = line.split(';');
        const obj = {};
        headers.forEach((header, idx) => {
          obj[header] = values[idx] || '';
        });
        return obj;
      });
      setStats(data);
    } else {
      // Fallback sample data for development
      const sampleStats = [
        { 'Encoded Date': '2026-05-10 14:30:00', 'Filename': 'movie1.mkv', 'Original Size': '2.5 GB', 'New Size': '1.2 GB', 'Percentage': '48%', 'Duration of Encode': '00:45:30', 'Command': 'HandBrakeCLI ...' },
        { 'Encoded Date': '2026-05-11 10:15:00', 'Filename': 'tvshow1.mkv', 'Original Size': '1.8 GB', 'New Size': '900 MB', 'Percentage': '50%', 'Duration of Encode': '00:30:20', 'Command': 'HandBrakeCLI ...' }
      ];
      setStats(sampleStats);
    }
  };

  return (
    <div className="stats-dashboard">
      <h3>Statistics Dashboard</h3>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Filename</th>
            <th>Original Size</th>
            <th>New Size</th>
            <th>Reduction</th>
            <th>Duration</th>
            <th>Command</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((row, idx) => (
            <tr key={idx}>
              <td>{row['Encoded Date'] || row.date}</td>
              <td>{row['Filename'] || row.filename}</td>
              <td>{row['Original Size'] || row.originalSize}</td>
              <td>{row['New Size'] || row.newSize}</td>
              <td>{row['Percentage'] || row.percentage}</td>
              <td>{row['Duration of Encode'] || row.duration}</td>
              <td className="command-cell">{row['Command'] || row.command}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default StatsDashboard;
