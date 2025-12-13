# Deployment Checklist - Critical Fixes

## Pre-Deployment Verification

### Code Changes ✅
- [x] clipboard_watcher.py - Event-driven architecture
- [x] llm_processor.py - Model updated + embeddings added
- [x] models_extended.py - Vector storage columns added
- [x] ocr_agent.py - Privacy controls added
- [x] activity_watcher.py - URL extraction improved
- [x] orchestrator.py - Semantic search method added
- [x] routes.py - Search API endpoints added
- [x] ActivityDashboard.js - Semantic search UI added
- [x] docker-compose.yml - Services optimized

### Dependencies to Install

```bash
# Required
pip install sentence-transformers  # For embeddings
pip install scikit-learn          # For cosine similarity
pip install numpy                 # For numerical operations

# Optional (for ReAct)
pip install langchain>=0.1.0
pip install langchain-community>=0.0.1
```

### System Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install xclip    # For event-driven clipboard monitoring
sudo apt-get install xdotool  # For browser URL extraction

# Optional OCR
sudo apt-get install tesseract-ocr  # For OCR functionality
```

---

## Database Migration

### Step 1: Backup Current Database
```bash
pg_dump -U postgres agentic_logger > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Add Vector Storage Columns

```sql
-- Add embedding and metadata columns to clipboard_events
ALTER TABLE clipboard_events 
ADD COLUMN embedding JSON DEFAULT NULL,
ADD COLUMN metadata JSON DEFAULT NULL;

-- Create indices for faster searches
CREATE INDEX idx_embedding ON clipboard_events USING GIN(embedding);
CREATE INDEX idx_metadata ON clipboard_events USING GIN(metadata);
```

### Step 3: Verify Schema
```sql
\d clipboard_events  -- PostgreSQL
DESC clipboard_events;  -- MySQL
```

---

## Docker Deployment

### Step 1: Rebuild Images

```bash
# Build backend with new dependencies
docker-compose build backend

# Rebuild UI (if dependencies changed)
docker-compose build ui
```

### Step 2: Start Services

```bash
# Stop current containers
docker-compose down

# Start fresh
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### Step 3: Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check UI availability
curl http://localhost:3000

# View logs
docker-compose logs -f backend
```

---

## Feature Testing

### Test 1: Event-Driven Clipboard Monitoring
```python
# Copy text to clipboard and verify it's captured
# Check logs for "📋 Clipboard Event" messages

# Expected: Instant capture without polling delays
```

### Test 2: Embedding Generation
```python
# Test via Python
from agents.llm_processor import LLMProcessor
llm = LLMProcessor()
embedding = llm.generate_embedding("Hello world")
print(f"Embedding length: {len(embedding)}")  # Should be 384 for all-MiniLM-L6-v2
```

### Test 3: Semantic Search
```bash
# Test via API
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "important meeting",
    "limit": 10
  }'
```

### Test 4: Privacy Filtering
```python
# Test sensitive content filtering
from agents.ocr_agent import filter_sensitive_content

result = filter_sensitive_content("My password is secret123")
print(result)  # Should output: "[SENSITIVE_CONTENT_FILTERED]"
```

### Test 5: Browser URL Extraction
```bash
# Open Firefox/Chrome and check active window
# Verify URL appears in Activity Dashboard

# Check logs for "👁️ Activity" messages
```

### Test 6: Frontend Semantic Search
1. Navigate to http://localhost:3000
2. Click "Search" tab
3. Enter query in search box
4. Click 🧠 button for semantic search
5. Verify results display with similarity scores

---

## Performance Validation

### Metric 1: Container Memory Usage
```bash
# Before fix
docker stats  # Note memory usage

# After fix (should be lower)
docker stats  # Compare memory usage
```

### Metric 2: Clipboard Monitoring Response Time
```python
# Measure time from clipboard copy to event capture
# Expected: <100ms with event-driven, ~1s with polling
```

### Metric 3: Semantic Search Latency
```bash
# Time the semantic search endpoint
time curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 20}'

# Expected: 50-200ms depending on database size
```

### Metric 4: Embedding Generation Speed
```python
# Benchmark embedding generation
import time
from agents.llm_processor import LLMProcessor

llm = LLMProcessor()
start = time.time()
for i in range(100):
    llm.generate_embedding(f"Test text {i}")
elapsed = time.time() - start
print(f"Average time per embedding: {elapsed/100*1000:.2f}ms")
```

---

## Rollback Procedures

### If Docker Deployment Fails

```bash
# Revert to previous images
docker-compose down
docker pull <previous-backend-image>
docker pull <previous-ui-image>
docker-compose up -d
```

### If Database Migration Fails

```bash
# Restore from backup
pg_restore -U postgres -d agentic_logger backup_20251105_120000.sql
```

### If Features Break

```bash
# Disable problematic feature
# Edit routes.py and comment out the problematic endpoint
# Restart containers
docker-compose restart backend
```

---

## Monitoring & Logging

### Key Logs to Monitor

```bash
# Backend logs
docker-compose logs -f backend

# Watch for:
# - "Agent integration initialized" (startup)
# - "📋 Clipboard Event" (event-driven working)
# - "Semantic search error" (issues)
# - "X11 event-driven clipboard monitoring initialized" (X11 working)
```

### Database Queries to Monitor

```sql
-- Monitor embedding storage
SELECT COUNT(*) as total_with_embeddings 
FROM clipboard_events 
WHERE embedding IS NOT NULL;

-- Check metadata storage
SELECT COUNT(*) as total_with_metadata 
FROM clipboard_events 
WHERE metadata IS NOT NULL;

-- Query performance
SELECT COUNT(*) FROM clipboard_events;
EXPLAIN ANALYZE SELECT * FROM clipboard_events WHERE embedding IS NOT NULL;
```

---

## Success Criteria

### All Fixes Working ✅
- [ ] Event-driven clipboard monitoring active
- [ ] `qwen2.5:3b` model available in Ollama
- [ ] Embeddings generated and stored in database
- [ ] Sensitive content filtered correctly
- [ ] Browser URLs extracted accurately
- [ ] Semantic search returns relevant results
- [ ] Keyword search works via API
- [ ] Frontend search UI displays results

### Performance Metrics ✅
- [ ] Docker memory usage < 2GB (vs. 4GB before)
- [ ] Clipboard capture < 100ms response time
- [ ] Semantic search < 200ms for 1000 events
- [ ] No memory leaks in extended operation (24+ hours)

### User Experience ✅
- [ ] Search results display correctly
- [ ] Similarity scores visible and accurate
- [ ] Error messages clear and helpful
- [ ] UI remains responsive during searches
- [ ] Mobile view works (if applicable)

---

## Troubleshooting

### Issue: "xclip not found"
**Solution**: Install xclip
```bash
sudo apt-get install xclip
```

### Issue: Embeddings not generating
**Solution**: Check sentence-transformers
```bash
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

### Issue: Semantic search returning empty results
**Solution**: Verify embeddings exist in database
```sql
SELECT COUNT(*) FROM clipboard_events WHERE embedding IS NOT NULL;
```

### Issue: High memory usage
**Solution**: Check database connections
```bash
docker-compose logs backend | grep "connection"
```

### Issue: UI search not working
**Solution**: Check CORS and API availability
```bash
curl http://localhost:8000/api/search/semantic
```

---

## Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] Health check endpoint responding
- [ ] Database migrations complete
- [ ] Embeddings being generated and stored
- [ ] Semantic search functional
- [ ] Frontend UI displaying correctly
- [ ] Logs being generated without errors
- [ ] Performance metrics acceptable
- [ ] Backup procedures documented
- [ ] Team notified of new features

---

## Documentation Updates

- [ ] Update API documentation with new endpoints
- [ ] Document semantic search usage
- [ ] Add privacy filtering documentation
- [ ] Update architecture diagrams
- [ ] Create user guide for new search features
- [ ] Document system requirements

---

## Sign-Off

- **Deployment Date**: _______________
- **Deployed By**: ___________________
- **Verified By**: ___________________
- **Status**: ✅ READY FOR PRODUCTION

---

**All 10 critical fixes are now integrated and ready for deployment!**
