"""
TSMC Careers Scraper
Scrapes job listings from https://careers.tsmc.com/zh_TW/careers/SearchJobs

Filter options (pass values to scrape()):
  location   : 台灣, 加拿大, 中國, 德國-德勒斯登, 德國-慕尼黑, 日本-橫濱市,
                日本-大阪市, 日本-筑波市, 日本-熊本市, 韓國, 荷蘭,
                美國-亞利桑那州, 美國-加利福尼亞州, 美國-麻薩諸塞州,
                美國-德克薩斯州, 美國-華盛頓州, 美國-華盛頓哥倫比亞特區
  specialty  : 研究發展, 特殊技術, IC 設計技術, 製造, 廠務與工安環保, 產品發展,
                連線與封裝技術, 測試開發與技術, 品質暨可靠性, 資訊技術, 內部稽核,
                業務開發, 客戶服務, 企業規劃, 財務會計暨風險管理, 人力資源, 法務,
                資材管理, 永續發展 (ESG), 一般行政, 身心障礙應徵者專區
  job_level  : 技術員, 副工程師/副管理師, 工程師/管理師, 主管職, 其它
  job_type   : 正職, 約聘, 實習, 學徒
"""
import json
import math
import os
import re
import tempfile
import time
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, Page


# ── Filter definitions (field_id → {label: value}) ──────────────────────────

FILTERS = {
    "location": {
        "field_id": "1277",
        "format": "1380",
        "options": {
            "台灣": "13209",
            "加拿大": "13210",
            "中國": "13211",
            "德國-德勒斯登": "2326764",
            "德國-慕尼黑": "4762540",
            "日本-橫濱市": "13214",
            "日本-大阪市": "13215",
            "日本-筑波市": "13216",
            "日本-熊本市": "13217",
            "韓國": "13212",
            "荷蘭": "13213",
            "美國-亞利桑那州": "13221",
            "美國-加利福尼亞州": "13218",
            "美國-麻薩諸塞州": "13219",
            "美國-德克薩斯州": "13220",
            "美國-華盛頓州": "13222",
            "美國-華盛頓哥倫比亞特區": "13223",
        },
    },
    "specialty": {
        "field_id": "558",
        "format": "493",
        "options": {
            "研究發展": "38617",
            "特殊技術": "38618",
            "IC 設計技術": "38619",
            "製造": "38620",
            "廠務與工安環保": "38621",
            "產品發展": "38622",
            "連線與封裝技術": "38623",
            "測試開發與技術": "38635",
            "品質暨可靠性": "38624",
            "資訊技術": "38625",
            "內部稽核": "38626",
            "業務開發": "38627",
            "客戶服務": "38628",
            "企業規劃": "38629",
            "財務會計暨風險管理": "38630",
            "人力資源": "38631",
            "法務": "38632",
            "資材管理": "38633",
            "永續發展 (ESG)": "7898835",
            "一般行政": "38634",
            "身心障礙應徵者專區": "38636",
        },
    },
    "job_level": {
        "field_id": "147",
        "format": "70",
        "options": {
            "技術員": "5710",
            "副工程師/副管理師": "39075",
            "工程師/管理師": "5709",
            "主管職": "5708",
            "其它": "39076",
        },
    },
    "job_type": {
        "field_id": "542",
        "format": "486",
        "options": {
            "正職": "5701",
            "約聘": "5702",
            "實習": "13100",
            "學徒": "4348108",
        },
    },
}


# ── URL builder ──────────────────────────────────────────────────────────────

def build_url(
    offset: int = 0,
    location: Optional[str] = None,
    specialty: Optional[str] = None,
    job_level: Optional[str] = None,
    job_type: Optional[str] = None,
) -> str:
    base = "https://careers.tsmc.com/zh_TW/careers/SearchJobs/"
    params: dict[str, str] = {}

    filter_args = {
        "location": location,
        "specialty": specialty,
        "job_level": job_level,
        "job_type": job_type,
    }

    for key, label in filter_args.items():
        if label is None:
            continue
        cfg = FILTERS[key]
        value = cfg["options"].get(label)
        if value is None:
            raise ValueError(f"Unknown {key!r}: {label!r}. Valid: {list(cfg['options'])}")
        params[cfg["field_id"]] = value
        params[f"{cfg['field_id']}_format"] = cfg["format"]

    params["listFilterMode"] = "1"
    params["jobRecordsPerPage"] = "10"
    if offset:
        params["jobOffset"] = str(offset)

    return base + "?" + urlencode(params)


# ── Parsing ──────────────────────────────────────────────────────────────────

@dataclass
class Job:
    job_id: str
    title: str
    url: str
    location: str
    specialty: Optional[str]
    employment_type: Optional[str]
    posted_date: Optional[str]


def parse_articles(page: Page) -> list[Job]:
    jobs = []
    for article in page.locator("article.article--result").all():
        link = article.locator("h3 a.link")
        title = link.inner_text().strip()
        url = link.get_attribute("href") or ""

        match = re.search(r"jobId=(\d+)", url)
        job_id = match.group(1) if match else ""

        subtitles = article.locator(".article__header__text__subtitle").all()
        location = specialty = employment_type = posted_date = None

        if len(subtitles) >= 1:
            texts = [s.inner_text().strip() for s in subtitles[0].locator("span:not(.separator)").all()]
            if len(texts) == 1:
                location = texts[0]
            elif len(texts) == 2:
                location, employment_type = texts
            elif len(texts) >= 3:
                location, specialty, employment_type = texts[0], texts[1], texts[2]

        if len(subtitles) >= 2:
            raw = subtitles[1].locator(".list-item-posted").inner_text().strip()
            posted_date = raw.replace("職務張貼日:", "").strip()

        jobs.append(Job(
            job_id=job_id, title=title, url=url,
            location=location or "", specialty=specialty,
            employment_type=employment_type, posted_date=posted_date,
        ))
    return jobs


def fetch_jd(url: str) -> dict:
    """Fetch full JD content from a TSMC JobDetail page using Playwright."""
    with sync_playwright() as p:
        page = p.chromium.launch(headless=True).new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-TW",
        ).new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)

        title = page.title().strip()
        text = page.inner_text("[class*='jobDetail']") if page.locator("[class*='jobDetail']").count() else page.inner_text("body")

    # Split into description / requirements by Chinese section headers
    description = ""
    requirements = ""

    desc_match = re.search(r"職務說明\s*\n(.*?)(?=職務要求|\Z)", text, re.S)
    req_match  = re.search(r"職務要求\s*\n(.*?)$", text, re.S)

    if desc_match:
        description = desc_match.group(1).strip()
    if req_match:
        requirements = req_match.group(1).strip()

    # Fallback: split on English headers if Chinese ones are absent
    if not description:
        m = re.search(r"(?:Job Description|Responsibilities)[:\s]*\n(.*?)(?=(?:Required|Preferred|Qualifications)|\Z)", text, re.S | re.I)
        if m:
            description = m.group(1).strip()

    return {
        "job_title": title,
        "company": "TSMC",
        "job_description": description,
        "requirements": requirements,
        "source_url": url,
    }


def get_total_count(page: Page) -> int:
    text = page.locator(".list-controls__text__legend").inner_text()
    m = re.search(r"of\s+([\d,]+)", text) or re.search(r"([\d,]+)\s*筆", text)
    return int(m.group(1).replace(",", "")) if m else 0


# ── Main scrape ──────────────────────────────────────────────────────────────

def scrape(
    location: Optional[str] = None,
    specialty: Optional[str] = None,
    job_level: Optional[str] = None,
    job_type: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> list[Job]:
    all_jobs: list[Job] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-TW",
        ).new_page()

        filter_kwargs = dict(location=location, specialty=specialty,
                             job_level=job_level, job_type=job_type)

        first_url = build_url(offset=0, **filter_kwargs)
        print(f"Loading page 1 → {first_url}")
        page.goto(first_url, wait_until="networkidle", timeout=60000)

        total = get_total_count(page)
        total_pages = math.ceil(total / 10) if total else 1
        if max_pages:
            total_pages = min(total_pages, max_pages)
        print(f"Total jobs: {total}, pages to scrape: {total_pages}")

        jobs = parse_articles(page)
        all_jobs.extend(jobs)
        print(f"  Page 1: {len(jobs)} jobs")

        for offset in range(10, total_pages * 10, 10):
            time.sleep(1.5)
            url = build_url(offset=offset, **filter_kwargs)
            page_num = offset // 10 + 1
            print(f"  Page {page_num}...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            jobs = parse_articles(page)
            all_jobs.extend(jobs)
            print(f"    → {len(jobs)} jobs")

        browser.close()

    return all_jobs


def prompt_filter(name: str, key: str) -> Optional[str]:
    options = list(FILTERS[key]["options"].keys())
    print(f"\n{name}（直接 Enter 跳過）:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("選擇號碼: ").strip()
        if raw == "":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  請輸入 1–{len(options)} 或直接 Enter 跳過")


if __name__ == "__main__":
    print("=== TSMC 職缺篩選 ===")
    location  = prompt_filter("工作地點", "location")
    specialty = prompt_filter("專業領域", "specialty")
    job_level = prompt_filter("職別",     "job_level")
    job_type  = prompt_filter("職務類型", "job_type")

    print("\n開始爬取...")
    jobs = scrape(location=location, specialty=specialty,
                  job_level=job_level, job_type=job_type)

    print(f"\n共爬取 {len(jobs)} 筆職缺")
    out_path = os.path.join(tempfile.gettempdir(), "tsmc_jobs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(j) for j in jobs], f, ensure_ascii=False, indent=2)
    print(f"已儲存至 {out_path}")
