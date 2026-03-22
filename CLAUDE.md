# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** for AI-powered resume-to-job matching. It focuses on TSMC careers but supports any job postings. The skill is installed to `~/.claude/skills/tsmc-resume-matcher/` and invoked as a slash command within Claude Code sessions.

## Commands

**Install the skill:**
```bash
./install.sh
```

**Set up Python environment:**
```bash
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install chromium
```

**Run the TSMC job scraper interactively:**
```bash
.venv/bin/python scraper.py
```
Prompts for filters (location, specialty, job level, job type) and outputs `jobs.json`.

**Fetch a specific JD from a URL:**
```python
from scraper import fetch_jd
jd = fetch_jd("https://careers.tsmc.com/...")
```

## Architecture

### Skill Workflow (4 steps)
1. **Parse Resume** — Extract structured fields from PDF/text per `references/resume-parser.md`
2. **Fetch JD** — Scrape job description from URL or use TSMC scraper, per `references/jd-parser.md`
3. **Score Match** — Apply 100-point rubric across 5 dimensions per `references/scoring-rubric.md`
4. **Output Report** — Grades (S/A/B/C/D), breakdown, strengths, gaps, and recommendations

### Scoring Dimensions (100 pts total)
| Dimension | Points |
|---|---|
| Skills Match (required 25 + preferred 10) | 35 |
| Experience Level | 20 |
| Industry Background | 20 |
| Education | 10 |
| Soft Skills / Culture Fit | 15 |

### Key Files
- `tsmc-resume-matcher/SKILL.md` — Primary skill instructions (Chinese), defines the full workflow Claude follows when invoked
- `tsmc-resume-matcher/references/` — Parsing and scoring rules referenced by SKILL.md
- `scraper.py` — Playwright-based scraper for TSMC careers (SPA + Cloudflare); hardcoded filter field IDs: location=1277, specialty=558, job_level=147, job_type=542
- `.claude/settings.local.json` — Bash/WebFetch permissions required for the skill to run

### Why Playwright for TSMC
TSMC careers is a Cloudflare-protected SPA. `scraper.py` uses a full browser (Playwright + Chromium) to bypass bot detection and handle dynamic rendering. Other job sites are fetched via standard `WebFetch`.
