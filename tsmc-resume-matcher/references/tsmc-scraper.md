# TSMC 職缺爬蟲使用說明

台積電全站為 SPA + Cloudflare 保護，**`web_fetch` 無法使用**，全程透過 `scraper.py` 以 Playwright 抓取。

## Step 1：取得職缺列表

```bash
cd <repo_root>
.venv/bin/python scraper.py
```

互動式逐一選擇篩選條件，直接 Enter 跳過（不套用該 filter）。完成後輸出 `jobs.json`。

`jobs.json` 每筆欄位：`job_id`、`title`、`url`、`location`、`specialty`、`employment_type`、`posted_date`

## Step 2：抓取每筆詳細 JD

```bash
.venv/bin/python - <<'EOF'
from scraper import fetch_jd
import json

with open("jobs.json") as f:
    jobs = json.load(f)

for job in jobs:
    jd = fetch_jd(job["url"])
    print(json.dumps(jd, ensure_ascii=False, indent=2))
EOF
```

`fetch_jd()` 回傳欄位：`job_title`、`company`、`job_description`、`requirements`、`source_url`
