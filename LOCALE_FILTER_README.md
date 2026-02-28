# Locale File Filtering - Scholar's Terminal

## What This Does

Automatically excludes **335,492+ locale/translation files** from GitHub indexing, saving you ~186 hours of processing time!

## Files Modified

1. **`locale_filter.py`** (NEW) - Core filtering logic
2. **`reindex_with_metadata.py`** (UPDATED) - Integrated locale filtering

## How It Works

The filter automatically excludes:

### ✅ Folder-based Patterns
```
/locales/
/i18n/
/l10n/
/translations/
/lang/
/languages/
```

### ✅ Filename Patterns
```
Package.locale.en-US.yaml
messages.en.js
strings.fr.json
app.de.properties
```

### ✅ Language Code Files
```
eu.js
fr.json
de.ts
zh-CN.yaml
pt-BR.xml
```

## What's Excluded vs. Kept

**EXCLUDED** (examples):
- `winget-pkgs/manifests/.../Package.locale.en-US.yaml` ❌
- `project/src/locales/eu.js` ❌
- `app/i18n/fr.json` ❌
- `translations/zh-CN.yaml` ❌

**KEPT** (examples):
- `project/src/index.js` ✅
- `app/main.py` ✅
- `README.md` ✅
- `european.js` ✅ (eu in middle of word)

## Your Estimated Savings

Based on your GitHub scan:

**Files:**
- Total scanned: 1,463,617
- Valid files: 1,128,125
- **Excluded: 335,492 (22.9%)**

**Time:**
- **186.4 hours saved** (~7.8 days of processing!)
- At 2 seconds per file for embedding generation

**Space:**
- **~328 MB** less in your vector database
- Faster, cleaner searches

## Usage

### Just Run Your Normal Indexing!

The filter is **already integrated** into `reindex_with_metadata.py`.

```bash
python reindex_with_metadata.py
```

You'll see in the logs:
```
[SCAN] Scanning D:\GitHub...
[FILTER] Excluded 335,492 locale files
[FOUND] Found 1,128,125 files to process
```

## How to Copy to Other PC

To copy the updated files to your indexing PC at 192.168.160.1:

```powershell
# Copy the locale filter
Copy-Item "D:\Claude\Projects\scholars-terminal\locale_filter.py" `
          "\\192.168.160.1\<share>\scholars-terminal\locale_filter.py"

# Copy the updated reindex script
Copy-Item "D:\Claude\Projects\scholars-terminal\reindex_with_metadata.py" `
          "\\192.168.160.1\<share>\scholars-terminal\reindex_with_metadata.py"
```

Or just copy these two files:
1. `locale_filter.py` (NEW)
2. `reindex_with_metadata.py` (UPDATED)

## Features

- **Books are NOT filtered** - Only applies to GitHub files
- **Conservative filtering** - Won't exclude unless confident it's a locale file
- **Logging** - Shows exactly how many files were excluded
- **Zero performance impact** - Filtering is instant

## Notes

- The filter only applies to GitHub directory, not your Books directory
- All filtering is logged so you can review what was excluded
- If you find valid files being excluded, you can adjust patterns in `locale_filter.py`

---

**Result:** From 1.46M files down to 1.13M files - focused, clean knowledge base! 🎯
