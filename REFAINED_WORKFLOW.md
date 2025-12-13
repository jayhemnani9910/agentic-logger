# 🎯 Refined Agentic Logger Workflow

## Current Issue
- ✅ Local agents working and saving raw data
- ❌ No LLM processing happening (Summary: None, Tags: None)
- ❌ UI shows only raw data, not processed insights

## Refined Workflow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Local        │    │   Docker        │    │   Frontend     │
│   Agents       │───▶│   Database      │───▶│   UI           │
│               │    │                 │    │                 │
│ 📋 Clipboard  │    │ 📄 Raw Data    │    │ 🎯 Summary    │
│ 🪟 Activity   │    │ 💾 Processed   │    │   View         │
│ 💻 Commands   │    │   Data          │    │ 🔍 Details     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Step-by-Step Process

### 1. Local Agent Monitoring
```python
# local_agent_runner.py captures:
- Clipboard content (text/images)
- Active window/application
- Shell commands
- Timestamps and metadata
```

### 2. Database Trigger
```sql
-- Trigger on INSERT to clipboard_events
CREATE OR REPLACE FUNCTION process_clipboard_event()
RETURNS TRIGGER AS $$
BEGIN
    -- Queue for LLM processing
    INSERT INTO processing_queue (event_id, type, status) 
    VALUES (NEW.id, 'clipboard', 'pending');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 3. LLM Processing Pipeline
```python
# Background worker processes queue:
def process_clipboard_queue():
    for item in queue:
        if item.type == 'clipboard':
            # Call Ollama for processing
            result = ollama.process(
                model="llama3.2",
                prompt=f"Analyze this content: {item.content}",
                system="You are an activity analysis AI..."
            )
            
            # Update with processed data
            update_clipboard_event(
                event_id=item.id,
                summary=result.summary,
                tags=result.tags,
                categories=result.categories,
                importance=result.importance
            )
```

### 4. UI Data Display Strategy

#### Main Dashboard View (Processed Data Only)
```javascript
// Show only processed entries
const fetchSummaryData = async () => {
    const response = await fetch('/api/clipboard/processed');
    return response.data.filter(item => 
        item.summary !== null && item.tags.length > 0
    );
};
```

#### Detail View (Full Data on Click)
```javascript
// When user clicks entry, show full details
const fetchFullDetails = async (eventId) => {
    const response = await fetch(`/api/clipboard/${eventId}`);
    return {
        raw: response.raw_content,
        processed: response.processed_summary,
        metadata: response.event_metadata,
        tags: response.tags,
        timeline: response.processing_timeline
    };
};
```

## Implementation Plan

### Phase 1: Database Schema Updates
```sql
-- Add processing status fields
ALTER TABLE clipboard_events 
ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN processed_at TIMESTAMP,
ADD COLUMN llm_model VARCHAR(50),
ADD COLUMN processing_error TEXT;

-- Create processing queue table
CREATE TABLE processing_queue (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES clipboard_events(id),
    type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);
```

### Phase 2: Background Processing Service
```python
# processing_worker.py
class LLMProcessor:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.db = get_database_connection()
    
    def process_queue(self):
        while True:
            items = self.get_pending_items()
            for item in items:
                try:
                    result = self.process_with_llm(item)
                    self.update_processed_data(item.id, result)
                except Exception as e:
                    self.mark_failed(item.id, str(e))
            time.sleep(5)
```

### Phase 3: API Updates
```python
# New endpoints
@app.route('/api/clipboard/processed')
def get_processed_clipboard():
    """Return only processed entries for main view"""
    events = ClipboardEvent.query.filter(
        ClipboardEvent.processed_summary.isnot(None)
    ).order_by(ClipboardEvent.created_at.desc()).limit(50)
    
    return jsonify({
        'data': [format_for_ui(event) for event in events],
        'success': True
    })

@app.route('/api/clipboard/<int:event_id>')
def get_event_details(event_id):
    """Return full details for detail view"""
    event = ClipboardEvent.query.get_or_404(event_id)
    return jsonify({
        'data': format_full_details(event),
        'success': True
    })
```

### Phase 4: Frontend Updates
```javascript
// Dashboard shows processed data only
const Dashboard = () => {
    const [summaryData, setSummaryData] = useState([]);
    
    useEffect(() => {
        fetchSummaryData().then(setSummaryData);
    }, []);
    
    return (
        <div>
            {summaryData.map(item => (
                <ClipboardCard 
                    key={item.id}
                    summary={item.processed_summary}
                    tags={item.tags}
                    onClick={() => showDetails(item.id)}
                />
            ))}
        </div>
    );
};

// Detail modal shows full information
const DetailModal = ({ eventId }) => {
    const [details, setDetails] = useState(null);
    
    useEffect(() => {
        fetchFullDetails(eventId).then(setDetails);
    }, [eventId]);
    
    return (
        <Modal>
            {details && (
                <div>
                    <h3>Summary</h3>
                    <p>{details.processed}</p>
                    
                    <h3>Raw Content</h3>
                    <pre>{details.raw}</pre>
                    
                    <h3>AI Analysis</h3>
                    <TagsList tags={details.tags} />
                </div>
            )}
        </Modal>
    );
};
```

## User Experience Flow

1. **User copies something** → Local agent captures instantly
2. **Background processing** → Ollama analyzes and categorizes  
3. **Dashboard updates** → Shows meaningful summaries
4. **Click for details** → Full raw + processed data
5. **Search & filter** → Through processed metadata

## Benefits

- ✅ **Instant capture** - No waiting for processing
- ✅ **Smart summaries** - AI-powered insights
- ✅ **Clean UI** - Shows processed data only
- ✅ **Deep details** - Full data available on click
- ✅ **Scalable** - Background processing queue

## Next Steps

1. **Update database schema** with processing fields
2. **Create background worker** for LLM processing  
3. **Modify local_agent_runner.py** to save raw + trigger processing
4. **Update API** with processed/raw endpoints
5. **Refactor frontend** for summary/detail views

This separates capture from processing, giving users instant feedback while providing deep AI insights.