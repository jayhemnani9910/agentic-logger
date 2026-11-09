import React from 'react';

const EnhancedClipboardCard = ({ event, onDetailClick }) => {
  // Parse metadata if it exists
  let metadata = {};
  if (event.event_metadata) {
    try {
      metadata = typeof event.event_metadata === 'string' 
        ? JSON.parse(event.event_metadata) 
        : event.event_metadata;
    } catch (e) {
      // Silently handle parse errors
    }
  }

  // The list API sends these as flat fields
  const contentAnalysis = metadata;
  const systemState = metadata;

  // Determine content icon
  const getContentIcon = () => {
    if (contentAnalysis.is_url) return '🔗';
    if (contentAnalysis.is_code) return '💻';
    if (contentAnalysis.is_json) return '📋';
    return '📝';
  };

  const contentIcon = getContentIcon();
  const contentLength = contentAnalysis.content_length || event.raw_content?.length || 0;

  return (
    <div className="event-card clipboard-event" onClick={() => onDetailClick('clipboard', event.id)}>
      <div className="event-header">
        <div className="event-header-left">
          <span className="content-icon-badge">{contentIcon}</span>
          <div className="event-meta">
            <span className="event-type-badge">{event.content_type}</span>
            <span className="event-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
        <div className="event-header-right">
          {contentLength > 0 && (
            <span className="content-length" title={`${contentLength} characters`}>
              📏 {contentLength > 1000 ? `${(contentLength / 1024).toFixed(1)}KB` : `${contentLength}B`}
            </span>
          )}
          {systemState.cpu_percent && (
            <span className="system-indicator" title={`CPU: ${systemState.cpu_percent.toFixed(1)}% | Memory: ${systemState.memory_percent?.toFixed(1)}%`}>
              💻 {systemState.cpu_percent.toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      <div className="event-body">
        <p className="event-app">🎯 {event.source_app || 'Unknown App'}</p>
        
        {/* Content Analysis Badges */}
        {(contentAnalysis.is_url || contentAnalysis.is_code || contentAnalysis.is_json) && (
          <div className="content-type-badges">
            {contentAnalysis.is_url && <span className="type-badge url">🔗 URL</span>}
            {contentAnalysis.is_code && <span className="type-badge code">💻 Code</span>}
            {contentAnalysis.is_json && <span className="type-badge json">📋 JSON</span>}
          </div>
        )}

        {/* Preview */}
        {event.raw_content && (
          <p className="event-content-preview">
            {event.raw_content.length > 150 
              ? event.raw_content.substring(0, 150) + '...' 
              : event.raw_content}
          </p>
        )}

        {/* Summary */}
        {event.summary && (
          <div className="event-summary">
            <strong>💡 Summary:</strong> {event.summary}
          </div>
        )}

        {/* Tags */}
        {event.tags && event.tags.length > 0 && (
          <div className="event-tags">
            {event.tags.map((tag, i) => (
              <span key={i} className="tag">{tag}</span>
            ))}
          </div>
        )}
      </div>

      {event.has_image && (
        <div className="event-footer">
          🖼️ Image attached ({event.ocr_count || 0} OCR results)
        </div>
      )}

      <div className="event-footer-interaction">
        <button className="view-details-btn">View Details →</button>
      </div>
    </div>
  );
};

export default EnhancedClipboardCard;
