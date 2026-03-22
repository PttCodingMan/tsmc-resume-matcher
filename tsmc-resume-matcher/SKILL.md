---
name: tsmc-resume-matcher
description: >
  自動將使用者的履歷與指定職缺進行 AI 配對分析，輸出詳細的配對分數與理由。
  當使用者提到「幫我看這份履歷適不適合這個職缺」、「篩選職缺」、「履歷配對」、
  「我的履歷跟這個 JD 符合嗎」、「幫我分析這個工作適不適合我」、
  「我想投這家公司，幫我看看」，或上傳履歷並附上任何職缺連結時，請務必使用此 skill。
  即使使用者只說「幫我看一下」並同時上傳履歷，也應優先考慮使用此 skill。
---

# Resume Job Matcher Skill

使用者提供履歷（PDF 或純文字）及一個或多個職缺來源，
此 skill 會自動解析、比對並輸出每個職缺的配對分數與詳細理由。

## 環境需求（首次使用前確認）

需要 Python 3.11+ 與 Playwright，請在 skill 目錄執行：

```bash
cd ~/.claude/skills/tsmc-resume-matcher
python3 -m venv .venv
.venv/bin/pip install playwright
.venv/bin/playwright install chromium
```

確認方式：
```bash
.venv/bin/python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

> 若 `.venv` 已存在且上述確認指令輸出 `OK`，可跳過安裝步驟。

## 整體流程

```
1. 解析履歷  →  2. 抓取職缺 JD  →  3. AI 配對分析  →  4. 輸出結果
```

---

## Step 1：解析履歷

### 1a. PDF 上傳

使用 `pdftotext` 或 `pdfplumber` 萃取文字：

```bash
pdftotext -layout /mnt/user-data/uploads/<filename>.pdf /tmp/resume.txt
cat /tmp/resume.txt
```

若萃取結果空白或亂碼，改用視覺化方式：
```bash
pdftoppm -jpeg -r 150 -f 1 -l 1 /mnt/user-data/uploads/<filename>.pdf /tmp/resume_page
# 然後用 view tool 檢視圖片
```

### 1b. 純文字貼上

使用者直接貼入文字，不需要額外處理，直接進入 Step 2。

### 萃取目標欄位

從履歷中萃取以下結構化資訊（存入變數備用）：

```
- 職稱/職能方向 (current_title, target_role)
- 總年資 (years_of_experience)
- 技能清單 (skills[])
- 工作經歷摘要 (work_summary[])
- 學歷 (education)
- 語言能力 (languages[])
- 其他亮點 (highlights[])
```

詳細解析規則請參考：`references/resume-parser.md`

---

## Step 2：抓取職缺 JD

### 2. 目標為台積電（TSMC）職缺

台積電全站（列表頁與詳細頁）皆為 SPA + Cloudflare 保護，**`web_fetch` 無法使用**，全程改用 Playwright：

**Step 1：取得職缺列表**

```bash
cd ~/.claude/skills/tsmc-resume-matcher
.venv/bin/python scraper.py
```

互動式選擇篩選條件（可跳過任一項）：
- 工作地點（台灣、美國-亞利桑那州…）
- 專業領域（資訊技術、製造、研究發展…）
- 職別（工程師/管理師、技術員…）
- 職務類型（正職、約聘、實習…）

**Step 2：用 Playwright 抓取所有詳細 JD**

```bash
.venv/bin/python - <<'EOF'
from scraper import fetch_jd
import json

import tempfile, os
with open(os.path.join(tempfile.gettempdir(), "tsmc_jobs.json")) as f:
    jobs = json.load(f)

for job in jobs:
    jd = fetch_jd(job["url"])
    print(json.dumps(jd, ensure_ascii=False, indent=2))
EOF
```

詳細爬蟲說明請參考：`references/tsmc-scraper.md`

### JD 萃取目標欄位

```
- job_title: 職缺名稱
- company: 公司名稱
- required_skills[]: 必要技能/條件
- preferred_skills[]: 加分條件
- years_required: 要求年資
- education_required: 學歷要求
- job_description: 職責摘要
- source_url: 原始連結
```

詳細解析規則請參考：`references/jd-parser.md`

---

## Step 3：AI 配對分析

直接根據履歷資訊與 JD 內容進行分析，評分維度：

| 維度 | 滿分 |
|------|------|
| 技能符合度 (skills_match) | 35 |
| 年資/職層 (experience_level) | 20 |
| 產業背景 (industry_background) | 20 |
| 學歷要求 (education) | 10 |
| 軟實力/文化 (soft_skills_culture) | 15 |

等級：S(90+) / A(75-89) / B(60-74) / C(45-59) / D(<45)

詳細評分規則請參考：`references/scoring-rubric.md`

---

## Step 4：輸出結果

### 格式規範

在對話中直接輸出，不需要生成檔案。每個職缺用一個區塊呈現：

```
---
📌 [職缺標題] @ [公司名稱]
🔗 [連結]

總分：XX / 100　　等級：[S/A/B/C/D]　　一句話總結：[verdict]

📊 分項分數
  ├ 技能符合度      XX / 35
  ├ 年資/職層       XX / 20
  ├ 產業背景        XX / 20
  ├ 學歷要求        XX / 10
  └ 軟實力/文化     XX / 15

✅ 你的優勢
  • [優勢1]
  • [優勢2]

⚠️ 潛在缺口
  • [缺口1]

💡 建議
  [recommendation]
---
```

若有多個職缺，最後加上**Top 5 排名總表**，並附上 JD 連結：

```
## 📋 職缺排名總覽

| # | 職缺 | 公司 | 分數 | 等級 |
|---|------|------|------|------|
| 1 | ...  | ...  |  87  |  A   |
| 2 | ...  | ...  |  71  |  B   |
```

---

## 錯誤處理

| 情況 | 處理方式 |
|------|---------|
| PDF 無法萃取文字 | 改用視覺化（rasterize）方式讀取 |
| 職缺頁面需要登入 | 請使用者手動貼上 JD 文字 |
| API 回傳非 JSON | 清除 markdown fences 後重新 parse，失敗則重試一次 |
| 職缺頁面找不到 JD | 告知使用者，跳過此職缺並繼續分析其他職缺 |
