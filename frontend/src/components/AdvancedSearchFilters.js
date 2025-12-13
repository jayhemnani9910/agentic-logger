import React, { useState, useEffect } from 'react';
import './AdvancedSearchFilters.css';

const AdvancedSearchFilters = ({ onFilterChange, loading }) => {
  const [filters, setFilters] = useState({
    contentType: '', // 'url', 'code', 'json', 'text'
    app: '',
    timeRange: '24h', // '1h', '6h', '24h', '7d'
    minSize: '',
    maxSize: '',
    isCommand: false,
    exitCode: '', // 0 for success, -1 for error
    commandSearch: '',
    searchText: ''
  });

  const handleFilterChange = (field, value) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const defaultFilters = {
      contentType: '',
      app: '',
      timeRange: '24h',
      minSize: '',
      maxSize: '',
      isCommand: false,
      exitCode: '',
      commandSearch: '',
      searchText: ''
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  return (
    <div className="advanced-search-filters">
      <div className="filters-header">
        <h3>🔍 Advanced Filters</h3>
        <button 
          className="reset-button"
          onClick={handleReset}
          title="Clear all filters"
        >
          ↺ Reset
        </button>
      </div>

      <div className="filters-grid">
        {/* Content Type Filters */}
        <div className="filter-group content-type-group">
          <label>Content Type</label>
          <div className="filter-options">
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.contentType === 'url'}
                onChange={(e) => handleFilterChange('contentType', e.target.checked ? 'url' : '')}
                disabled={loading}
              />
              <span>🔗 URLs</span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.contentType === 'code'}
                onChange={(e) => handleFilterChange('contentType', e.target.checked ? 'code' : '')}
                disabled={loading}
              />
              <span>💻 Code</span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.contentType === 'json'}
                onChange={(e) => handleFilterChange('contentType', e.target.checked ? 'json' : '')}
                disabled={loading}
              />
              <span>📋 JSON</span>
            </label>
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.contentType === 'text'}
                onChange={(e) => handleFilterChange('contentType', e.target.checked ? 'text' : '')}
                disabled={loading}
              />
              <span>📝 Text</span>
            </label>
          </div>
        </div>

        {/* Time Range */}
        <div className="filter-group">
          <label htmlFor="timeRange">Time Range</label>
          <select
            id="timeRange"
            value={filters.timeRange}
            onChange={(e) => handleFilterChange('timeRange', e.target.value)}
            disabled={loading}
            className="filter-select"
          >
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>

        {/* Application Filter */}
        <div className="filter-group">
          <label htmlFor="app">Application</label>
          <input
            id="app"
            type="text"
            placeholder="e.g., VS Code, Chrome"
            value={filters.app}
            onChange={(e) => handleFilterChange('app', e.target.value)}
            disabled={loading}
            className="filter-input"
          />
        </div>

        {/* Size Range */}
        <div className="filter-group size-group">
          <label>Content Size</label>
          <div className="size-inputs">
            <input
              type="number"
              placeholder="Min (bytes)"
              value={filters.minSize}
              onChange={(e) => handleFilterChange('minSize', e.target.value)}
              disabled={loading}
              className="filter-input-small"
            />
            <span>—</span>
            <input
              type="number"
              placeholder="Max (bytes)"
              value={filters.maxSize}
              onChange={(e) => handleFilterChange('maxSize', e.target.value)}
              disabled={loading}
              className="filter-input-small"
            />
          </div>
        </div>

        {/* Search Text */}
        <div className="filter-group full-width">
          <label htmlFor="searchText">Search Content</label>
          <input
            id="searchText"
            type="text"
            placeholder="Search in clipboard content..."
            value={filters.searchText}
            onChange={(e) => handleFilterChange('searchText', e.target.value)}
            disabled={loading}
            className="filter-input"
          />
        </div>

        {/* Command Filters */}
        <div className="filter-group">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={filters.isCommand}
              onChange={(e) => handleFilterChange('isCommand', e.target.checked)}
              disabled={loading}
            />
            <span>⌘ Commands Only</span>
          </label>
        </div>

        {/* Exit Code Filter */}
        {filters.isCommand && (
          <div className="filter-group">
            <label htmlFor="exitCode">Exit Code</label>
            <select
              id="exitCode"
              value={filters.exitCode}
              onChange={(e) => handleFilterChange('exitCode', e.target.value)}
              disabled={loading}
              className="filter-select"
            >
              <option value="">Any exit code</option>
              <option value="0">✅ Success (0)</option>
              <option value="-1">❌ Errors (non-zero)</option>
            </select>
          </div>
        )}

        {/* Command Search */}
        {filters.isCommand && (
          <div className="filter-group full-width">
            <label htmlFor="commandSearch">Command</label>
            <input
              id="commandSearch"
              type="text"
              placeholder="Search in commands..."
              value={filters.commandSearch}
              onChange={(e) => handleFilterChange('commandSearch', e.target.value)}
              disabled={loading}
              className="filter-input"
            />
          </div>
        )}
      </div>

      {/* Active Filters Summary */}
      {(filters.contentType || filters.app || filters.timeRange !== '24h' || 
        filters.minSize || filters.maxSize || filters.searchText || 
        filters.isCommand || filters.exitCode) && (
        <div className="active-filters">
          <span className="filters-label">Active filters:</span>
          {filters.contentType && (
            <span className="filter-badge">
              {filters.contentType === 'url' && '🔗 URLs'}
              {filters.contentType === 'code' && '💻 Code'}
              {filters.contentType === 'json' && '📋 JSON'}
              {filters.contentType === 'text' && '📝 Text'}
            </span>
          )}
          {filters.app && <span className="filter-badge">App: {filters.app}</span>}
          {filters.timeRange !== '24h' && <span className="filter-badge">Time: {filters.timeRange}</span>}
          {filters.minSize && <span className="filter-badge">Min: {filters.minSize}B</span>}
          {filters.maxSize && <span className="filter-badge">Max: {filters.maxSize}B</span>}
          {filters.searchText && <span className="filter-badge">Search: {filters.searchText}</span>}
          {filters.isCommand && <span className="filter-badge">⌘ Commands</span>}
          {filters.exitCode === '0' && <span className="filter-badge">✅ Success</span>}
          {filters.exitCode === '-1' && <span className="filter-badge">❌ Errors</span>}
          {filters.commandSearch && <span className="filter-badge">Cmd: {filters.commandSearch}</span>}
        </div>
      )}
    </div>
  );
};

export default AdvancedSearchFilters;
