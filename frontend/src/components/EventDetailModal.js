import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EventDetailModal.css';

const EventDetailModal = ({ eventId, eventType, onClose }) => {
  const [eventData, setEventData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchEventDetails = async () => {
      try {
        setLoading(true);
        let endpoint = '';
        
        if (eventType === 'clipboard') {
          endpoint = `/api/clipboard/${eventId}/details`;
        } else if (eventType === 'activity') {
          endpoint = `/api/activity/${eventId}/details`;
        } else if (eventType === 'command') {
          endpoint = `/api/commands/${eventId}/details`;
        }

        const response = await axios.get(`${apiUrl}${endpoint}`);
        if (response.data.success) {
          setEventData(response.data);
        } else {
          setError('Failed to fetch event details');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchEventDetails();
  }, [eventId, eventType, apiUrl]);

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="loading">Loading event details...</div>
        </div>
      </div>
    );
  }

  if (error || !eventData) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close" onClick={onClose}>✕</button>
          <div className="error-message">Error: {error || 'Event not found'}</div>
        </div>
      </div>
    );
  }

  const data = eventData;
  const formatTime = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  const renderOverviewTab = () => {
    if (eventType === 'clipboard') {
      const contentAnalysis = data.content_analysis || {};
      const systemState = data.system_state || {};
      const activityCtx = data.activity_context || {};

      return (
        <div className="tab-content overview-tab">
          <div className="info-grid">
            <div className="info-item">
              <label>Content Type:</label>
              <div className="content-type-display">
                <span className="content-icon">{contentAnalysis.icon || '📝'}</span>
                <span>{data.basic?.content_type || 'Unknown'}</span>
              </div>
            </div>
            
            <div className="info-item">
              <label>Source App:</label>
              <span>{data.basic?.source_app || 'Unknown'}</span>
            </div>

            <div className="info-item full-width">
              <label>Length:</label>
              <span>{contentAnalysis.length || 0} characters</span>
              {contentAnalysis.word_count && <span> ({contentAnalysis.word_count} words)</span>}
              {contentAnalysis.line_count && <span>, {contentAnalysis.line_count} lines</span>}
            </div>

            <div className="info-item">
              <label>Detected as:</label>
              <div className="content-badges">
                {contentAnalysis.is_url && <span className="badge badge-url">🔗 URL</span>}
                {contentAnalysis.is_code && <span className="badge badge-code">💻 Code</span>}
                {contentAnalysis.is_json && <span className="badge badge-json">📋 JSON</span>}
                {!contentAnalysis.is_url && !contentAnalysis.is_code && !contentAnalysis.is_json && <span className="badge badge-text">📝 Text</span>}
              </div>
            </div>
          </div>

          <div className="system-metrics">
            <h4>System State at Capture</h4>
            <div className="metrics-grid">
              <div className="metric">
                <span className="metric-label">CPU</span>
                <span className="metric-value">{systemState.cpu_percent ? `${systemState.cpu_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Memory</span>
                <span className="metric-value">{systemState.memory_percent ? `${systemState.memory_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Disk</span>
                <span className="metric-value">{systemState.disk_percent ? `${systemState.disk_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Processes</span>
                <span className="metric-value">{systemState.process_count || 'N/A'}</span>
              </div>
            </div>
          </div>

          {(activityCtx.app || activityCtx.window) && (
            <div className="activity-context">
              <h4>Activity Context</h4>
              <div className="context-info">
                {activityCtx.app && <div><strong>App:</strong> {activityCtx.app}</div>}
                {activityCtx.window && <div><strong>Window:</strong> {activityCtx.window}</div>}
              </div>
            </div>
          )}
        </div>
      );
    } else if (eventType === 'activity') {
      const systemState = data.system_state || {};
      const systemInfo = data.system_info || {};

      return (
        <div className="tab-content overview-tab">
          <div className="info-grid">
            <div className="info-item">
              <label>Application:</label>
              <span>{data.basic?.application || 'Unknown'}</span>
            </div>

            <div className="info-item full-width">
              <label>Window Title:</label>
              <span>{data.basic?.window_title || 'N/A'}</span>
            </div>

            {data.basic?.url && (
              <div className="info-item full-width">
                <label>URL:</label>
                <span>{data.basic.url}</span>
              </div>
            )}
          </div>

          <div className="system-metrics">
            <h4>System State</h4>
            <div className="metrics-grid">
              <div className="metric">
                <span className="metric-label">CPU</span>
                <span className="metric-value">{systemState.cpu_percent ? `${systemState.cpu_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Memory</span>
                <span className="metric-value">{systemState.memory_percent ? `${systemState.memory_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Disk</span>
                <span className="metric-value">{systemState.disk_percent ? `${systemState.disk_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Processes</span>
                <span className="metric-value">{systemState.process_count || 'N/A'}</span>
              </div>
            </div>
          </div>

          {systemInfo.os && (
            <div className="system-info">
              <h4>System Information</h4>
              <div className="info-text">
                {systemInfo.os && <div><strong>OS:</strong> {systemInfo.os}</div>}
                {systemInfo.user && <div><strong>User:</strong> {systemInfo.user}</div>}
                {systemInfo.machine && <div><strong>Machine:</strong> {systemInfo.machine}</div>}
              </div>
            </div>
          )}
        </div>
      );
    } else if (eventType === 'command') {
      const systemState = data.system_state || {};
      const systemInfo = data.system_info || {};

      return (
        <div className="tab-content overview-tab">
          <div className="info-grid">
            <div className="info-item full-width">
              <label>Command:</label>
              <code className="command-display">{data.basic?.command || 'N/A'}</code>
            </div>

            <div className="info-item">
              <label>Status:</label>
              <span className={`status-badge ${data.basic?.success ? 'success' : 'error'}`}>
                {data.basic?.status} Exit Code: {data.basic?.exit_code}
              </span>
            </div>

            <div className="info-item">
              <label>Working Directory:</label>
              <span>{data.basic?.working_directory || 'N/A'}</span>
            </div>

            <div className="info-item">
              <label>User:</label>
              <span>{data.basic?.user || 'N/A'}</span>
            </div>

            {data.duration && (
              <div className="info-item">
                <label>Duration:</label>
                <span>{data.duration}ms</span>
              </div>
            )}
          </div>

          <div className="system-metrics">
            <h4>System State at Execution</h4>
            <div className="metrics-grid">
              <div className="metric">
                <span className="metric-label">CPU</span>
                <span className="metric-value">{systemState.cpu_percent ? `${systemState.cpu_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Memory</span>
                <span className="metric-value">{systemState.memory_percent ? `${systemState.memory_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Disk</span>
                <span className="metric-value">{systemState.disk_percent ? `${systemState.disk_percent.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Processes</span>
                <span className="metric-value">{systemState.process_count || 'N/A'}</span>
              </div>
            </div>
          </div>

          {systemInfo.os && (
            <div className="system-info">
              <h4>System Information</h4>
              <div className="info-text">
                {systemInfo.os && <div><strong>OS:</strong> {systemInfo.os}</div>}
                {systemInfo.user && <div><strong>User:</strong> {systemInfo.user}</div>}
                {systemInfo.machine && <div><strong>Machine:</strong> {systemInfo.machine}</div>}
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  const renderRawDataTab = () => {
    if (eventType === 'clipboard') {
      return (
        <div className="tab-content raw-data-tab">
          <div className="raw-content-display">
            <h4>Raw Clipboard Content</h4>
            <pre>{data.raw_data?.content || 'No content'}</pre>
            <div className="raw-meta">
              Length: {data.raw_data?.length || 0} characters
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderMetadataTab = () => {
    return (
      <div className="tab-content metadata-tab">
        <div className="metadata-display">
          <h4>Full Metadata</h4>
          <pre>{JSON.stringify(data.full_metadata || {}, null, 2)}</pre>
        </div>
      </div>
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {eventType === 'clipboard' && '📋 Clipboard Event Details'}
            {eventType === 'activity' && '👁️ Activity Event Details'}
            {eventType === 'command' && '⌘ Command Event Details'}
          </h2>
          <div className="modal-timestamp">
            {formatTime(data.timestamp || data.created_at)}
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            📊 Overview
          </button>
          {eventType === 'clipboard' && (
            <button
              className={`modal-tab ${activeTab === 'rawdata' ? 'active' : ''}`}
              onClick={() => setActiveTab('rawdata')}
            >
              📄 Raw Data
            </button>
          )}
          <button
            className={`modal-tab ${activeTab === 'metadata' ? 'active' : ''}`}
            onClick={() => setActiveTab('metadata')}
          >
            ⚙️ Metadata
          </button>
        </div>

        <div className="modal-body">
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'rawdata' && renderRawDataTab()}
          {activeTab === 'metadata' && renderMetadataTab()}
        </div>
      </div>
    </div>
  );
};

export default EventDetailModal;
