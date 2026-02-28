# GitHub Launch Checklist

## Pre-Push Verification

### Files to Verify
- [ ] README.md (professional landing page)
- [ ] LICENSE (MIT)
- [ ] .gitignore (excludes secrets, data)
- [ ] requirements.txt (all dependencies)
- [ ] setup.py (package installer)
- [ ] CHANGELOG.md (v1.0.0 notes)
- [ ] CONTRIBUTING.md (contribution guide)
- [ ] TEMPLATE_CATALOG.md (11 domains)
- [ ] docs/ folder (installation, templates, API)
- [ ] examples/ folder (4 working demos)
- [ ] research_scanner/ (core code)
- [ ] research_scanner/templates/ (11 YAML files)

### Critical Files to NOT Push
- [ ] .env files (API keys, secrets)
- [ ] chroma_db/ (vector database - too large)
- [ ] __pycache__/ (Python cache)
- [ ] *.pyc files (compiled Python)
- [ ] Personal data files
- [ ] scan_history.json (personal usage data)

### Pre-Commit Tasks
- [ ] Remove any personal information
- [ ] Remove API keys from code
- [ ] Check for hardcoded paths (D:\Claude\Projects\...)
- [ ] Verify all file paths are relative
- [ ] Remove any TODO comments with names
- [ ] Check for email addresses (replace with placeholder)

## GitHub Setup Steps

### Step 1: Create Repository on GitHub
1. Go to https://github.com/new
2. Repository name: `research-scanner`
3. Description: "Universal research paper discovery system - works for ANY research domain"
4. Public repository
5. Do NOT initialize with README (we have one)
6. Do NOT add .gitignore (we have one)
7. Do NOT add license (we have one)
8. Click "Create repository"

### Step 2: Initialize Local Git Repository
```bash
cd D:\Claude\Projects\scholars-terminal
git init
git branch -M main
```

### Step 3: Add Remote Origin
```bash
# Replace 'yourusername' with your actual GitHub username
git remote add origin https://github.com/yourusername/research-scanner.git
```

### Step 4: Stage All Files
```bash
# Add all files
git add .

# Verify what will be committed
git status
```

### Step 5: Create Initial Commit
```bash
git commit -m "Initial release: Research Scanner v1.0.0

- Universal research paper discovery system
- 11 pre-built domain templates
- 6 data sources (arXiv, PubMed, HF, IEEE, medRxiv, bioRxiv)
- Tested across 8 research domains
- Complete documentation and examples
- MIT License - fully open source"
```

### Step 6: Push to GitHub
```bash
git push -u origin main
```

## Post-Push Setup

### Step 1: Verify Repository
- [ ] Go to https://github.com/yourusername/research-scanner
- [ ] Check README displays correctly
- [ ] Verify all folders visible
- [ ] Click through documentation links
- [ ] Test example code snippets

### Step 2: Add Topics/Tags
On GitHub repository page:
- [ ] Click "Add topics"
- [ ] Add: `research`, `papers`, `arxiv`, `pubmed`, `machine-learning`, `academic`, `literature-review`, `python`

### Step 3: Set Repository Settings
- [ ] Go to Settings
- [ ] Enable Issues
- [ ] Enable Discussions (recommended)
- [ ] Set default branch: main
- [ ] Enable "Allow merge commits"

### Step 4: Create Release
- [ ] Go to Releases
- [ ] Click "Create a new release"
- [ ] Tag: v1.0.0
- [ ] Title: "Research Scanner v1.0.0 - Initial Release"
- [ ] Description: Copy from CHANGELOG.md
- [ ] Click "Publish release"

### Step 5: Add Badges to README
Update README.md with:
```markdown
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-stable-green.svg)
```

## Social Media Announcement

### Twitter/X Template
```
🚀 Just open-sourced Research Scanner!

Universal paper discovery for ANY research field:
✅ 11 pre-built domains
✅ 6 data sources  
✅ 97.7% relevance (AI)
✅ Template-driven

Stop missing important papers!

https://github.com/yourusername/research-scanner

#OpenSource #Research #Academia
```

### Reddit r/machinelearning
```
[P] Research Scanner - Universal paper discovery system (tested across 8 domains)

I built a research paper scanner that actually adapts to your field...

[Full post with test results and template examples]

GitHub: https://github.com/yourusername/research-scanner
```

### Hacker News
```
Research Scanner – Universal research paper discovery (tested across 8 domains)
https://github.com/yourusername/research-scanner
```

## Medium Article Publication

### Post-Push Updates to Article
1. Replace all "yourusername" with actual GitHub username
2. Add real GitHub repository URL
3. Update any placeholder links
4. Add screenshot of README
5. Add screenshot of example output

### Medium Publication Checklist
- [ ] Copy content from MEDIUM_ARTICLE.md
- [ ] Add cover image (screenshot of README)
- [ ] Add inline images (example output, template)
- [ ] Update all GitHub links to real URL
- [ ] Add tags: Research, Open Source, AI, Academia, Python
- [ ] Set canonical URL to GitHub
- [ ] Publish!

## Community Engagement Plan

### Week 1
- [ ] Monitor GitHub issues
- [ ] Respond to questions
- [ ] Accept first PRs
- [ ] Thank contributors

### Week 2
- [ ] Share on academic subreddits
- [ ] Post to relevant Discord servers
- [ ] Engage with users
- [ ] Document common questions

### Week 3
- [ ] Start planning v1.1
- [ ] Collect feature requests
- [ ] Review template contributions
- [ ] Build roadmap

## Success Metrics

### Week 1 Goals
- [ ] 50+ GitHub stars
- [ ] 5+ forks
- [ ] 10+ issues/discussions
- [ ] 1+ PR

### Month 1 Goals
- [ ] 200+ GitHub stars
- [ ] 20+ forks
- [ ] 50+ issues/discussions
- [ ] 5+ merged PRs
- [ ] 2+ community templates

### Month 3 Goals
- [ ] 500+ GitHub stars
- [ ] 50+ forks
- [ ] User testimonials
- [ ] Active community
- [ ] v1.1 released

## Backup Plan

### Before Pushing
```bash
# Create backup of current state
cp -r D:\Claude\Projects\scholars-terminal D:\Claude\Projects\scholars-terminal.backup
```

### If Something Goes Wrong
```bash
# Delete .git folder and start over
rm -rf .git
# Then follow steps again
```

## Ready to Push?

When you're ready, execute these commands:

```bash
cd D:\Claude\Projects\scholars-terminal

# 1. Initialize
git init
git branch -M main

# 2. Add remote (replace with your actual repo)
git remote add origin https://github.com/yourusername/research-scanner.git

# 3. Stage files
git add .

# 4. Commit
git commit -m "Initial release: Research Scanner v1.0.0"

# 5. Push
git push -u origin main
```

## Post-Push Celebration 🎉

After successful push:
1. Share on social media
2. Publish Medium article
3. Tell colleagues
4. Watch the stars roll in!

**You built something amazing. Time to share it with the world!**
