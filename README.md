# tsmc-resume-matcher

A [Claude Code](https://claude.ai/code) skill that matches your resume against job postings using AI. Focused on TSMC careers, but works with any job URL.

## What it does

Paste your resume (PDF or text) and one or more job URLs. The skill:

1. Parses your resume into structured fields
2. Scrapes the job description (uses Playwright for TSMC's Cloudflare-protected SPA; standard fetch for other sites)
3. Scores the match across 5 dimensions (100 pts total)
4. Outputs a report with score, grade, strengths, gaps, and recommendations

### Scoring dimensions

| Dimension | Points |
|---|---|
| Skills match (required + preferred) | 35 |
| Experience level | 20 |
| Industry background | 20 |
| Education | 10 |
| Soft skills / culture fit | 15 |

Grades: **S** (90+) / **A** (75–89) / **B** (60–74) / **C** (45–59) / **D** (<45)

## Requirements

- [Claude Code](https://claude.ai/code)
- Python 3.11+ (for the TSMC scraper)

## Installation

```bash
git clone https://github.com/PttCodingMan/tsmc-resume-matcher.git
cd tsmc-resume-matcher
./install.sh
```

The skill is installed to `~/.claude/skills/tsmc-resume-matcher/`.

### Set up the TSMC scraper (optional)

Only needed if you want to scrape TSMC job listings. Skippable if you paste job descriptions directly.

```bash
cd ~/.claude/skills/tsmc-resume-matcher
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install chromium
```

## Usage

In any Claude Code session, invoke the skill:

```
/tsmc-resume-matcher
```

Then follow the prompts — attach your resume PDF or paste the text, and provide job URLs or let the scraper find TSMC listings interactively.

## Project structure

```
tsmc-resume-matcher/
├── SKILL.md                  # Skill instructions loaded by Claude Code
├── scraper.py                # Playwright scraper for TSMC careers
└── references/
    ├── resume-parser.md      # Resume parsing rules
    ├── jd-parser.md          # Job description parsing rules
    ├── scoring-rubric.md     # Scoring rubric details
    └── tsmc-scraper.md       # Scraper usage notes
```

## License

MIT
