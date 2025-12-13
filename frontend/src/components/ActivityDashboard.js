import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './ActivityDashboard.css';
import EventDetailModal from './EventDetailModal';
import EnhancedClipboardCard from './EnhancedClipboardCard';

const ActivityDashboard = () => {
  const [activeTab, setActiveTab] = useState('clipboard');
  const [clipboardEvents, setClipboardEvents] = useState([]);
  const [activityEvents, setActivityEvents] = useState([]);
  const [commandEvents, setCommandEvents] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [semanticResults, setSemanticResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvent, setSelectedEvent] = useState(null); // {eventId, eventType}
  const [filters, setFilters] = useState({
    hours: 24,
    limit: 50
  });

  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Handle event detail click
  const handleEventDetailClick = (eventType, eventId) => {
    setSelectedEvent({ eventType, eventId });
  };

  // Close modal
  const handleCloseModal = () => {
    setSelectedEvent(null);
  };

  // Semantic search function
  const handleSemanticSearch = async (query) => {
    try {
      setLoading(true);
      const response = await axios.post(`${apiUrl}/api/search/semantic`, {
        query: query,
        limit: 20
      });
      if (response.data && response.data.results) {
        setSemanticResults(response.data.results);
        setActiveTab('search');
      }
    } catch (err) {
      setError('Semantic search failed: ' + err.message);
      console.error('Semantic search error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Keyword search function
  const handleKeywordSearch = async (keywords) => {
    try {
      setLoading(true);
      const response = await axios.post(`${apiUrl}/api/search/keywords`, {
        keywords: keywords.split(/\s+/),
        limit: 50
      });
      if (response.data && response.data.results) {
        setSearchResults(response.data.results);
        setActiveTab('search');
      }
    } catch (err) {
      setError('Keyword search failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch clipboard events
  const fetchClipboardEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiUrl}/api/clipboard`, {
        params: {
          limit: filters.limit,
          hours: filters.hours
        }
      });
      if (response.data.success) {
        setClipboardEvents(response.data.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters, apiUrl]);

  // Fetch activity events
  const fetchActivityEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiUrl}/api/activity`, {
        params: {
          limit: filters.limit,
          hours: filters.hours
        }
      });
      if (response.data.success) {
        setActivityEvents(response.data.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters, apiUrl]);

  // Fetch command events
  const fetchCommandEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiUrl}/api/commands`, {
        params: {
          limit: filters.limit,
          hours: filters.hours
        }
      });
      if (response.data.success) {
        setCommandEvents(response.data.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters, apiUrl]);

  // Fetch system stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/stats`, {
        params: { hours: filters.hours }
      });
      if (response.data.success) {
        setStats(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, [filters.hours, apiUrl]);

  // Perform semantic search
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    
    try {
      setLoading(true);
      const response = await axios.post(`${apiUrl}/api/search`, {
        query: searchQuery,
        types: ['clipboard', 'activity', 'commands'],
        limit: filters.limit,
        hours: filters.hours
      });
      if (response.data.success) {
        setSearchResults(response.data.data);
        setActiveTab('search');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filters, apiUrl]);

  // Initial load and refresh on tab change
  useEffect(() => {
    if (activeTab === 'clipboard') {
      fetchClipboardEvents();
    } else if (activeTab === 'activity') {
      fetchActivityEvents();
    } else if (activeTab === 'commands') {
      fetchCommandEvents();
    } else if (activeTab === 'stats') {
      fetchStats();
    }
  }, [activeTab, fetchClipboardEvents, fetchActivityEvents, fetchCommandEvents, fetchStats]);

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format relative time
  const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div className="activity-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Activity Dashboard</h1>
        <div className="header-controls">
          <select 
            value={filters.hours} 
            onChange={(e) => setFilters({...filters, hours: parseInt(e.target.value)})}
            className="filter-select"
          >
            <option value={1}>Last 1h</option>
            <option value={6}>Last 6h</option>
            <option value={24}>Last 24h</option>
            <option value={168}>Last 7d</option>
          </select>
          
          <div className="search-box">
            <input
              type="text"
              placeholder="Search activities semantically..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  if (e.shiftKey) {
                    handleKeywordSearch(searchQuery);
                  } else {
                    handleSemanticSearch(searchQuery);
                  }
                }
              }}
              className="search-input"
              title="Press Enter for semantic search, Shift+Enter for keyword search"
            />
            <button onClick={() => handleSemanticSearch(searchQuery)} className="search-button" title="Semantic Search">🧠</button>
            <button onClick={() => handleKeywordSearch(searchQuery)} className="search-button" title="Keyword Search">🔍</button>
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={() => setError(null)} className="close-error">✕</button>
        </div>
      )}

      {/* Tab navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'clipboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('clipboard')}
        >
          📋 Clipboard
        </button>
        <button 
          className={`tab-button ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          👁️ Activity
        </button>
        <button 
          className={`tab-button ${activeTab === 'commands' ? 'active' : ''}`}
          onClick={() => setActiveTab('commands')}
        >
          ⌘ Commands
        </button>
        <button 
          className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          📊 Stats
        </button>
        <button 
          className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          🔎 Search
        </button>
      </div>

      {/* Loading spinner */}
      {loading && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      )}

      {/* Tab content */}
      {!loading && (
        <>
          {/* Clipboard Tab */}
          {activeTab === 'clipboard' && (
            <div className="tab-content clipboard-tab">
              <h2>📋 Clipboard Events</h2>
              {clipboardEvents.length === 0 ? (
                <p className="empty-state">No clipboard events found</p>
              ) : (
                <div className="events-list">
                  {clipboardEvents.map((event, idx) => (
                    <EnhancedClipboardCard 
                      key={idx} 
                      event={event} 
                      onDetailClick={handleEventDetailClick}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div className="tab-content activity-tab">
              <h2>👁️ Activity Timeline</h2>
              {activityEvents.length === 0 ? (
                <p className="empty-state">No activity events found</p>
              ) : (
                <div className="events-timeline">
                  {activityEvents.map((event, idx) => (
                    <div 
                      key={idx} 
                      className="timeline-item"
                      onClick={() => handleEventDetailClick('activity', event.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="timeline-time">{new Date(event.timestamp).toLocaleTimeString()}</div>
                      <div className="timeline-content">
                        <div className="app-name">📲 {event.application}</div>
                        <div className="window-title">{event.window_title}</div>
                        {event.url && (
                          <div className="window-url">🌐 {event.url}</div>
                        )}
                        <div className="view-details">→ View Details</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Commands Tab */}
          {activeTab === 'commands' && (
            <div className="tab-content commands-tab">
              <h2>⌘ Command History</h2>
              {commandEvents.length === 0 ? (
                <p className="empty-state">No command events found</p>
              ) : (
                <div className="commands-list">
                  {commandEvents.map((event, idx) => (
                    <div 
                      key={idx} 
                      className="command-item"
                      onClick={() => handleEventDetailClick('command', event.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="command-header">
                        <span className="command-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
                        <span className={`exit-code ${event.exit_code === 0 ? 'success' : 'error'}`}>
                          {event.exit_code === 0 ? '✅' : '❌'} Exit {event.exit_code}
                        </span>
                      </div>
                      <div className="command-body">
                        <code className="command-text">{event.command}</code>
                        {event.working_dir && (
                          <div className="command-dir">📂 {event.working_dir}</div>
                        )}
                        {event.user && (
                          <div className="command-user">👤 {event.user}</div>
                        )}
                        <div className="view-details">→ View Details</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Stats Tab */}
          {activeTab === 'stats' && stats && (
            <div className="tab-content stats-tab">
              <h2>System Statistics ({stats.period_hours}h)</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-number">{stats.counts.clipboard}</div>
                  <div className="stat-label">Clipboard Events</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.counts.activity}</div>
                  <div className="stat-label">Activity Events</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.counts.commands}</div>
                  <div className="stat-label">Commands</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.counts.ocr}</div>
                  <div className="stat-label">OCR Results</div>
                </div>
                <div className="stat-card highlight">
                  <div className="stat-number">{stats.counts.total}</div>
                  <div className="stat-label">Total Events</div>
                </div>
              </div>

              {stats.top_applications && stats.top_applications.length > 0 && (
                <div className="stats-section">
                  <h3>Top Applications</h3>
                  <div className="stats-list">
                    {stats.top_applications.map((app, idx) => (
                      <div key={idx} className="stats-item">
                        <div className="stats-item-name">{app.app}</div>
                        <div className="stats-item-bar">
                          <div 
                            className="stats-item-fill"
                            style={{width: `${(app.count / Math.max(...stats.top_applications.map(a => a.count))) * 100}%`}}
                          ></div>
                          <span className="stats-item-count">{app.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {stats.top_clipboard_sources && stats.top_clipboard_sources.length > 0 && (
                <div className="stats-section">
                  <h3>Top Clipboard Sources</h3>
                  <div className="stats-list">
                    {stats.top_clipboard_sources.map((app, idx) => (
                      <div key={idx} className="stats-item">
                        <div className="stats-item-name">{app.app}</div>
                        <div className="stats-item-bar">
                          <div 
                            className="stats-item-fill"
                            style={{width: `${(app.count / Math.max(...stats.top_clipboard_sources.map(a => a.count))) * 100}%`}}
                          ></div>
                          <span className="stats-item-count">{app.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Search Results Tab */}
          {activeTab === 'search' && (
            <div className="tab-content search-tab">
              <h2>Search Results: "{searchQuery}"</h2>
              
              {/* Semantic Results */}
              {semanticResults.length > 0 && (
                <div className="search-results-section">
                  <h3>🧠 Semantic Results ({semanticResults.length})</h3>
                  <div className="search-results">
                    {semanticResults.map((result, idx) => (
                      <div key={`semantic-${idx}`} className="search-result-card semantic-result">
                        <div className="result-header">
                          <span className="result-relevance">
                            Similarity: {(result.similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                        {result.event && (
                          <>
                            <div className="result-title">
                              {result.event.title || result.event.app || 'Event'}
                            </div>
                            <div className="result-summary">
                              {result.event.content || result.event.summary || 'No content'}
                            </div>
                            {result.event.tags && (
                              <div className="result-tags">
                                {result.event.tags.map((tag, i) => (
                                  <span key={i} className="result-tag">{tag}</span>
                                ))}
                              </div>
                            )}
                            <div className="result-time">
                              {result.event.timestamp ? formatTime(result.event.timestamp) : 'N/A'}
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Keyword Results */}
              {searchResults.length > 0 && (
                <div className="search-results-section">
                  <h3>🔍 Keyword Results ({searchResults.length})</h3>
                  <div className="search-results">
                    {searchResults.map((result, idx) => (
                      <div key={`keyword-${idx}`} className="search-result-card">
                        <div className="result-header">
                          <span className="result-type">{result.type || 'Event'}</span>
                        </div>
                        <div className="result-title">{result.title || result.app || 'Result'}</div>
                        <div className="result-summary">{result.summary || result.content || 'No details'}</div>
                        {result.tags && result.tags.length > 0 && (
                          <div className="result-tags">
                            {result.tags.map((tag, i) => (
                              <span key={i} className="result-tag">{tag}</span>
                            ))}
                          </div>
                        )}
                        <div className="result-time">{formatTime(result.timestamp)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {searchResults.length === 0 && semanticResults.length === 0 && (
                <p className="empty-state">No results found. Try a different search query.</p>
              )}
            </div>
          )}
        </>
      )}

      {/* Detail Modal */}
      {selectedEvent && (
        <EventDetailModal
          eventId={selectedEvent.eventId}
          eventType={selectedEvent.eventType}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ActivityDashboard;
