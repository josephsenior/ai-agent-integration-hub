# Fix ChunkLoadError

## Quick Fix

Run these commands to clear cache and rebuild:

```bash
cd agent_integration_hub/frontend-nextjs
rm -rf .next
rm -rf node_modules/.cache
npm run dev
```

Or on Windows PowerShell:
```powershell
cd agent_integration_hub\frontend-nextjs
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
npm run dev
```

## If Still Failing

1. Stop the dev server (Ctrl+C)
2. Clear everything:
   ```bash
   rm -rf .next node_modules
   npm install
   npm run dev
   ```

## Root Cause

ChunkLoadError usually happens when:
- Build cache is corrupted
- Hot reload got confused
- Missing dependencies

The fix above should resolve it.
