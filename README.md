# Google Search Trends Dashboard

Monitor your brand's search trends **during a campaign**. Track multiple brands across 5 search metrics in one dashboard. Auto-updates daily so you can see real-time search patterns without manual clicks.

**Live Example:** [selinaxxiao-dot.github.io/Google-Search-Dash](https://selinaxxiao-dot.github.io/Google-Search-Dash/)

---

## The Problem

You're running a marketing campaign. You want to know: **How are people searching for my brand right now?**

But Google Trends requires:
- ❌ Clicking between your brand and competitors
- ❌ Toggling through 5 metrics one-at-a-time
- ❌ Manual checking every time you want an update
- ❌ No historical comparison across metrics

**This dashboard solves that.**

---

## The Solution

One dashboard showing:
- ✅ **3 brands side-by-side** (yours + competitors)
- ✅ **All 5 metrics together** (Web, Image, News, Shopping, YouTube)
- ✅ **Auto-updates daily** (no manual checking)
- ✅ **Interactive controls** (toggle brands, toggle metrics)
- ✅ **Historical trends** (see patterns over time)

Pull up the dashboard. See everything at once. That's it.

---

## Who Should Use This?

- **During a campaign** - Monitor search interest in real-time
- **E-commerce** - Track your product vs competitor keywords
- **Brand launches** - See if people are searching for you
- **Content creators** - Monitor topic trends while promoting
- **Marketing teams** - Track brand awareness across channels

---

## How It Works

1. **You customize** brands and time window
2. **Script runs daily** (via Claude Code or your scheduler)
3. **Fetches Google Trends data** for your brands
4. **Generates interactive dashboard** with all metrics visible
5. **Auto-pushes to GitHub Pages** (live URL updates)
6. **You check dashboard** anytime during campaign

---

## Quick Start

### 1. Clone This Repo

```bash
git clone https://github.com/selinaxxiao-dot/Google-Search-Dash.git
cd Google-Search-Dash
```

### 2. Customize Your Brands

**Edit `pipeline.py` at line 19:**

```python
# Change these to YOUR brands
BRANDS = ['brand-1', 'brand-2', 'brand-3']

# Example for e-commerce:
# BRANDS = ['your-product', 'competitor-a', 'competitor-b']

# Example for campaign:
# BRANDS = ['your-brand', 'hashtag-campaign', 'competitor-brand']
```

### 3. (Optional) Customize Time Window

**Edit `pipeline.py` at line 16:**

```python
# Change GEO if needed (default: US)
GEO = 'US'  # 'CA' for Canada, 'GB' for UK, etc.
```

The dashboard automatically tracks the last 52 weeks with YTD filtering.

### 4. Enable GitHub Pages

1. Go to repo **Settings** → **Pages**
2. Select `main` branch, root folder
3. Your dashboard goes live at: `https://YOUR_USERNAME.github.io/Google-Search-Dash/`

### 5. Run the Script

**Option A: One-time run**
```bash
python pipeline.py
```

**Option B: Schedule daily (Claude Code)**
Just click "Run" daily or set up a schedule in Claude Code.

---

## Dashboard Guide

### Brand Switcher
- Click buttons at top to switch between brands
- Each brand shows its own trends + keywords
- See how your brand compares in real-time

### Metric Toggles
- **All Metrics** - Show/hide all 5 at once
- **Individual buttons** - Toggle Web, Image, News, Shopping, YouTube
- Chart updates instantly

### Trend Chart
- **Y-axis:** Search interest (0-100 scale)
- **X-axis:** Weeks over time
- **Line per metric:** See which channel is trending

### Keywords Table
- **10 columns** - All 5 metrics side-by-side
- **Top 25 queries** - Most searched terms per brand per metric
- **Interest bars** - Visual popularity

---

## Customization Guide

### Change Brands

**File:** `pipeline.py` **Line:** 19

```python
BRANDS = ['brand-1', 'brand-2', 'brand-3']  # ← Edit here
```

**Examples:**
```python
# E-commerce (product vs competitors)
BRANDS = ['nike-shoe', 'adidas-shoe', 'puma-shoe']

# Campaign (brand + related searches)
BRANDS = ['your-brand', 'campaign-hashtag', 'competitor']

# Content (topic vs alternatives)
BRANDS = ['your-product', 'product-review', 'alternative']
```

### Change Metrics

**File:** `pipeline.py` **Lines:** 21-27

Default (all 5):
```python
METRICS = [
    ('web',      '',        'Web Search'),
    ('image',    'images',  'Image Search'),
    ('news',     'news',    'News Search'),
    ('shopping', 'froogle', 'Google Shopping'),
    ('youtube',  'youtube', 'Youtube Search'),
]
```

**To remove a metric** - comment it out:
```python
METRICS = [
    ('web',      '',        'Web Search'),
    ('image',    'images',  'Image Search'),
    # ('news',     'news',    'News Search'),      # ← Commented out
    ('shopping', 'froogle', 'Google Shopping'),
    ('youtube',  'youtube', 'Youtube Search'),
]
```

### Change Geographic Region

**File:** `pipeline.py` **Line:** 16

```python
GEO = 'US'  # ← Change here

# Common codes:
# 'US'    - United States
# 'CA'    - Canada
# 'GB'    - United Kingdom
# 'AU'    - Australia
# 'DE'    - Germany
# 'FR'    - France
# 'JP'    - Japan
# ''      - Worldwide
```

### Change Time Window

**File:** `pipeline.py` **Lines:** 44-50 (advanced)**

Default: Last 52 weeks with YTD filtering. To change:

```python
def get_date_range():
    today = datetime.now()
    end_date   = today - timedelta(days=(today.weekday() - 5) % 7)
    fetch_start = today - timedelta(weeks=52)  # ← Change 52 to any number
    ...
```

---

## Running Modes

### Full Run (Recommended)
```bash
python pipeline.py
```
✅ Fetches fresh data from Google Trends  
✅ Generates HTML dashboard  
✅ Pushes to GitHub Pages  
⏱️ Takes ~2 minutes

### Demo Mode (Testing)
```bash
python pipeline.py --demo
```
✅ No API calls to Google  
✅ Generates synthetic data  
✅ Good for testing dashboard design  

### Fetch Only (No Push)
```bash
python pipeline.py --fetch
```
✅ Only downloads data  
✅ Saves Excel locally  
❌ Doesn't push to GitHub

### Publish Only
```bash
python pipeline.py --publish
```
❌ Uses existing data  
✅ Regenerates HTML  
✅ Pushes to GitHub

---

## File Structure

```
YOUR_REPO_NAME/
├── pipeline.py                  # Main script (edit brands/metrics here)
├── index.html                   # Generated dashboard (auto-created)
├── YOUR_EXCEL_FILENAME.xlsx     # Generated Excel data (auto-created)
├── README.md                    # This file
├── .gitignore                   # Git config
├── LICENSE                      # MIT License
└── .git/                        # Git history
```

---

## Output Files

### Excel File: `YOUR_EXCEL_FILENAME.xlsx`

**Sheet 1: `Brand-1 Trends`**
- Time | Web Search | Image Search | News Search | Google Shopping | Youtube Search
- Historical weekly data for your first brand

**Sheet 2: `Brand-1 Keywords`**
- Web Search | Web Search.1 | Image Search | Image Search.1 | ...
- Top 25 keywords per metric

(Repeated for Brand-2, Brand-3)

---

## Limitations & Notes

⚠️ **25 keywords max** - Google Trends returns top 25 queries per metric  
⚠️ **Weekly granularity** - Data is weekly, not daily  
⚠️ **Rate limiting** - Space runs 24+ hours apart to avoid blocks  
⚠️ **Unofficial API** - pytrends is not official; Google could change it  

✅ **Caching** - First run takes 2 minutes, subsequent runs are faster  
✅ **Retry logic** - Auto-retries on 429 errors with exponential backoff  

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `429 Too Many Requests` | Space runs 24+ hours apart. Script retries automatically. |
| No data for a brand | Brand might be too niche or have no search volume. Check Google Trends directly. |
| GitHub push fails | Verify personal access token has `repo` scope. |
| Dashboard not updating | Check GitHub Pages enabled (Settings → Pages). Clear cache. |
| Want more keywords | Google Trends API caps at 25. Would need direct API access. |

---

## FAQ

**Q: How often should I run this?**  
A: Once daily is safe. More frequent = risk of rate limiting.

**Q: Can I track more/fewer brands?**  
A: Yes. Edit BRANDS list to any number. More brands = longer runtime.

**Q: Can I change brands mid-campaign?**  
A: Yes. Just edit line 19 in pipeline.py and re-run.

**Q: Will Google ban me?**  
A: Unlikely. pytrends respects rate limits. Daily runs are fine.

**Q: Can I use without GitHub Pages?**  
A: Yes. Skip GitHub Pages setup. You get local HTML/Excel files.

**Q: How do I schedule daily updates?**  
A: In Claude Code, set up a recurring task. Or use cron/Task Scheduler.

**Q: Can I change dashboard colors?**  
A: Yes. Edit the `colors` object in the HTML section of pipeline.py.

**Q: What if a brand name has a space?**  
A: Works fine. `'your brand'` is treated as one search term.

---

## Contributing

Found a bug? Have ideas? Open an issue or PR!

---

## License

MIT License - Free to use and modify

---

## Author

Built to solve the problem of monitoring campaign search trends without manual clicks.

**GitHub:** [@selinaxxiao-dot](https://github.com/selinaxxiao-dot)  
**Example Dashboard:** [selinaxxiao-dot.github.io/Google-Search-Dash](https://selinaxxiao-dot.github.io/Google-Search-Dash/)

---

## Example Use Cases

### E-Commerce Campaign
```python
BRANDS = ['nike-running-shoes', 'adidas-running-shoes', 'asics-running-shoes']
GEO = 'US'
```
Monitor which brand people search during your shoe launch.

### Product Launch
```python
BRANDS = ['your-new-product', 'previous-product', 'competitor-product']
GEO = 'CA'
```
See real-time search interest as you launch in Canada.

### Content Promotion
```python
BRANDS = ['your-blog-topic', 'related-hashtag', 'competitor-blog']
GEO = ''  # Worldwide
```
Track which version of your topic is trending.

### Brand Campaign
```python
BRANDS = ['your-brand', 'campaign-slogan', 'competitor-brand']
GEO = 'US'
```
Monitor search interest during your marketing campaign.

---

## Getting Help

1. Check **Troubleshooting** section above
2. Look at **Customization Guide** for common edits
3. Check **Running Modes** to understand different ways to run
4. Open an issue on GitHub with details

