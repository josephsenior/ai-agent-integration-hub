# Backend Import Fix

## Issue
The backend was failing to start with error:
```
ModuleNotFoundError: No module named 'langchain'
```

## Root Cause
The code was importing `init_chat_model` from `langchain.chat_models` at the top level, but:
1. The langchain package structure has changed in newer versions
2. The import was failing even though it's only used as a fallback

## Solution
Made the import **lazy** (only import when needed) instead of at module load time. This allows the code to:
1. Try `google.genai` first (preferred)
2. Fall back to `langchain_google_genai` 
3. Only try `langchain.chat_models.init_chat_model` as last resort
4. Handle import errors gracefully

## Files Changed
- `backend/utils/gemini_client.py` - Made `init_chat_model` import lazy

## Testing
✅ Import test passed: `python -c "from backend.utils.gemini_client import create_llm; print('Import successful')"`

## Next Steps
The backend should now start successfully:
```bash
uvicorn backend.api.main:app --reload --port 8000
```
