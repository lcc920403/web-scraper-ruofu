# 自動抓補器（Python + SQLite）

這個專案是一個可直接執行的 Python 自動抓補器範例。它會：

- 抓取指定網站的列表頁 / 內容頁
- 解析標題、連結、內容
- 去除重複資料
- 儲存到 SQLite 資料庫
- 可自訂目標網址與 CSS 選擇器

## 專案結構

- `scraper.py`：抓取與儲存主程式
- `requirements.txt`：Python 依賴套件
- `.gitignore`：忽略檔案

## 安裝

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 執行

```bash
python scraper.py
```

## 設定來源

在 `scraper.py` 中可調整：

- `BASE_URL`
- `START_URLS`
- `item_selector`
- `title_selector`
- `link_selector`
- `content_selector`
- `allowed_domains`

範例：

```python
START_URLS = [
    "https://example.com/news",
]

ITEM_SELECTOR = "article, .post, .news-item, .card"
TITLE_SELECTOR = "h2, h3, .title, .headline"
LINK_SELECTOR = "a[href]"
CONTENT_SELECTOR = "p"
ALLOWED_DOMAINS = ["example.com"]
```

## 資料庫

資料會存放在：

```text
scraped_data.db
```

表格名稱：

```sql
CREATE TABLE scraped_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT UNIQUE,
    content TEXT,
    source TEXT,
    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 查詢資料範例

```bash
sqlite3 scraped_data.db
SELECT * FROM scraped_items LIMIT 10;
```

## 注意事項

- 請確認目標網站允許抓取
- 若網站有反爬蟲機制，可能需要設定 `User-Agent` 或代理伺服器
- 若要抓取動態網站（JavaScript 渲染），建議改用 Playwright 或 Selenium

## 進階建議

- 增加排程任務（cron / APScheduler）
- 儲存到 MySQL / PostgreSQL
- 加上錯誤記錄與重試邏輯
- 擴充 JSON / CSV 輸出
