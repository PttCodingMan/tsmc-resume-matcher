# 職缺 JD 解析規則

## 從網頁萃取 JD 的重點

網頁 HTML 通常包含導覽列、頁尾、廣告等雜訊，請只萃取以下核心區塊：
- 職缺標題（`<h1>` 或 `<title>` 中的職位名稱）
- 職責說明（Responsibilities / 工作內容）
- 必要條件（Requirements / 資格條件）
- 加分條件（Nice to have / Preferred）
- 公司介紹（取前 2-3 句即可）

## 必要 vs. 加分條件的判斷

**必要條件**：
- 出現「必須」、「需要」、「required」、「must have」
- 列在 Requirements / 基本資格區塊下
- 年資要求（如「3 年以上經驗」）

**加分條件**：
- 出現「加分」、「優先」、「preferred」、「nice to have」、「plus」
- 列在 Preferred / 其他條件區塊下

**模糊情況**：若無法判斷，一律視為必要條件（從嚴認定）

## 年資標準化

| 原始文字 | 標準化輸出 |
|---------|-----------|
| 「3 年以上」 | `{ "min": 3, "max": null }` |
| 「3-5 年」 | `{ "min": 3, "max": 5 }` |
| 「應屆歡迎」| `{ "min": 0, "max": 1 }` |
| 未提及 | `null` |

## 輸出範例

```json
{
  "job_title": "Senior Backend Engineer",
  "company": "某某科技股份有限公司",
  "required_skills": ["Python", "RESTful API", "SQL", "Docker"],
  "preferred_skills": ["Kubernetes", "Redis", "系統設計經驗"],
  "years_required": { "min": 3, "max": null },
  "education_required": "大學以上，資工/資管相關科系",
  "job_description": "負責核心交易平台後端服務開發與維護，參與系統架構設計討論，與前端及產品團隊協作",
  "source_url": "https://example.com/jobs/123"
}
```

## TSMC 詳細頁解析

TSMC 職缺詳細頁（`JobDetail?jobId=...`）可直接 `web_fetch`，內容結構：

- 職缺標題：`<h1>` 或頁面頂部大標
- 工作職責（Job Responsibilities）：條列式，通常在「工作職責」或「Job Responsibilities」段落
- 資格要求（Qualifications）：必要條件，通常在「資格條件」或「Qualifications」段落
- 公司固定填入：`"company": "TSMC"`

列表頁已取得的欄位（`location`、`specialty`、`employment_type`、`posted_date`）
可直接從 `jobs.json` 帶入，不必重複從詳細頁萃取。

## 常見障礙處理

| 問題 | 解法 |
|------|------|
| 需要登入才能看職缺 | 告知使用者請手動貼上 JD |
| 104/LinkedIn 等需登入 | 同上 |
| 頁面為單頁應用（SPA），抓到空內容 | 請使用者直接貼上 JD 文字 |
| TSMC 列表頁（SearchJobs）SPA 無法抓取 | 改用 `scraper.py`（參考 tsmc-scraper.md） |
| JD 全英文 | 正常處理，評分時以技能名稱對比 |
