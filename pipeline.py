import subprocess, sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytrends', 'pandas', 'openpyxl', '-q'])

import warnings; warnings.filterwarnings('ignore')
from pytrends.request import TrendReq
import pandas as pd
import time, os, json, argparse
from datetime import datetime, timedelta

# ════════════════════════════════════════════════════════════════════════════════
# ⚙️ CUSTOMIZATION SECTION - Edit these for your use case
# ════════════════════════════════════════════════════════════════════════════════

# 1. YOUR GITHUB REPOSITORY URL
#    Get this from: github.com/YOUR_USERNAME/YOUR_REPO
#    Example: 'https://github.com/your-username/Google-Search-Dash.git'
GITHUB_REPO = 'https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git'

# 2. LOCAL FOLDER NAME (where files are stored)
#    Should match the folder you created locally
#    Example: 'dashboard' or 'search-trends' or any name you like
REPO_DIR = os.path.expanduser('~/YOUR_DASHBOARD_NAME')

# 3. EXCEL OUTPUT FILE NAME
#    Change to something meaningful for your use case
#    Example: '~/trends_data.xlsx' or '~/campaign_trends.xlsx'
OUTPUT_EXCEL = os.path.expanduser('~/YOUR_EXCEL_FILENAME.xlsx')

# 4. GIT CONFIGURATION (for automatic commits)
GIT_EMAIL = 'your-email@example.com'
GIT_NAME = 'YOUR_NAME'

OUTPUT_HTML  = os.path.join(REPO_DIR, 'index.html')

GEO = 'US'

# ── Add / remove brands here (up to 5) ───────────────────────────────────────
BRANDS = ['brand-1', 'brand-2', 'brand-3']

METRICS = [
    ('web',      '',        'Web Search'),
    ('image',    'images',  'Image Search'),
    ('news',     'news',    'News Search'),
    ('shopping', 'froogle', 'Google Shopping'),
    ('youtube',  'youtube', 'Youtube Search'),
]

# ── Args ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--fetch',   action='store_true')
parser.add_argument('--publish', action='store_true')
parser.add_argument('--demo',    action='store_true')
args = parser.parse_args()

if not any([args.fetch, args.publish, args.demo]):
    args.fetch = True
    args.publish = True

print('GOOGLE SEARCH INTERESTS INDEX - COMPLETE PIPELINE')
print('='*80)

# ── Date range helpers ────────────────────────────────────────────────────────
def get_date_range():
    today = datetime.now()
    end_date   = today - timedelta(days=(today.weekday() - 5) % 7)   # last Saturday
    fetch_start = end_date - timedelta(weeks=52)                      # 52w for weekly granularity
    jan1   = datetime(today.year, 1, 1)
    cutoff = jan1 - timedelta(days=(jan1.weekday() + 1) % 7)         # Sunday of Jan 1's week
    return fetch_start, end_date, cutoff

# ── STEP 1: FETCH ─────────────────────────────────────────────────────────────
all_brands_trends   = {}   # brand -> {metric_key -> list of {time, value}}
all_brands_keywords = {}   # brand -> {metric_key -> list of {query, interest}}

if args.demo:
    print('\n[DEMO MODE] Generating synthetic data...\n')
    import random
    fetch_start, end_date, cutoff = get_date_range()
    weeks = pd.date_range(cutoff, end_date, freq='W-SAT')
    for brand in BRANDS:
        all_brands_trends[brand]   = {}
        all_brands_keywords[brand] = {}
        for key, gprop, display in METRICS:
            base = {'web':50,'image':70,'news':5,'shopping':30,'youtube':80}[key]
            vals = [min(100, max(0, base + random.randint(-20,20))) for _ in weeks]
            all_brands_trends[brand][key] = [
                {'time': w.strftime('%Y-%m-%d'), 'value': v}
                for w, v in zip(weeks, vals)
            ]
            queries = [f'{brand} item {i}' for i in range(1, 6)]
            all_brands_keywords[brand][key] = [
                {'query': q, 'interest': random.randint(20, 100)}
                for q in queries
            ]
    print('Demo data ready.')

elif args.fetch:
    print('\n[FETCH] Scraping Google Trends...\n')
    pytrends = TrendReq(hl='en-US', tz=360)
    fetch_start, end_date, cutoff = get_date_range()
    tf_long = f'{fetch_start.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'
    tf_ytd  = f'{cutoff.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'

    def safe_fetch(fn, delay=25, retries=3):
        for attempt in range(retries):
            try:
                result = fn()
                time.sleep(delay)
                return result
            except Exception as e:
                if '429' in str(e) and attempt < retries - 1:
                    wait = 60 * (attempt + 1)
                    print(f'429 - waiting {wait}s...', end=' ', flush=True)
                    time.sleep(wait)
                else:
                    raise

    for brand in BRANDS:
        print(f'\n  Brand: {brand.upper()}')
        all_brands_trends[brand]   = {}
        all_brands_keywords[brand] = {}
        for key, gprop, display in METRICS:
            print(f'    {key}...', end=' ', flush=True)
            try:
                # Interest over time: 52-week fetch → weekly data → filter to YTD
                pytrends.build_payload([brand], timeframe=tf_long, geo=GEO, gprop=gprop)
                trend_data = safe_fetch(pytrends.interest_over_time)
                if brand not in trend_data.columns or trend_data.empty:
                    raise ValueError(f'No trend data returned for {brand}')
                trend_w = trend_data[[brand]][trend_data.index >= pd.Timestamp(cutoff)]
                max_val = int(trend_w.max())
                if max_val > 0:
                    trend_w = (trend_w / max_val * 100).round(0).astype(int)
                all_brands_trends[brand][key] = [
                    {'time': idx.strftime('%Y-%m-%d'), 'value': int(row[brand])}
                    for idx, row in trend_w.iterrows()
                ]

                # Keywords: YTD timeframe
                pytrends.build_payload([brand], timeframe=tf_ytd, geo=GEO, gprop=gprop)
                related = safe_fetch(pytrends.related_queries)
                top = related[brand]['top']
                if top is not None and not top.empty:
                    all_brands_keywords[brand][key] = [
                        {'query': r['query'], 'interest': int(r['value'])}
                        for _, r in top.iterrows()
                    ]
                else:
                    all_brands_keywords[brand][key] = []
                print(f'done ({len(all_brands_keywords[brand][key])} kw, {len(all_brands_trends[brand][key])} wks)')
            except Exception as e:
                print(f'Error: {e}')
                all_brands_trends[brand][key]   = []
                all_brands_keywords[brand][key] = []

    # Save to Excel (one sheet per brand for trends, one sheet per brand for keywords)
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        for brand in BRANDS:
            # Trends sheet
            times = [r['time'] for r in all_brands_trends[brand].get('web', [])]
            df_t = pd.DataFrame({'Time': times})
            for key, gprop, display in METRICS:
                vals = [r['value'] for r in all_brands_trends[brand].get(key, [])]
                if len(vals) == len(times):
                    df_t[display] = vals
            df_t.to_excel(writer, sheet_name=f'{brand.title()} Trends', index=False)

            # Keywords sheet
            max_rows = max((len(v) for v in all_brands_keywords[brand].values()), default=0)
            df_k = pd.DataFrame()
            for key, gprop, display in METRICS:
                rows = all_brands_keywords[brand].get(key, [])
                queries   = [r['query']    for r in rows] + [None]*(max_rows - len(rows))
                interests = [r['interest'] for r in rows] + [None]*(max_rows - len(rows))
                df_k[display]         = queries
                df_k[f'{display}.1']  = interests
            df_k.to_excel(writer, sheet_name=f'{brand.title()} Keywords', index=False)

    print(f'\nExcel saved: {OUTPUT_EXCEL}')

# ── STEP 2: PUBLISH ───────────────────────────────────────────────────────────
if args.publish or args.demo:
    print('\n[PUBLISH] Generating HTML and pushing to GitHub Pages...\n')

    if not args.demo:
        # Re-load from Excel
        xls = pd.ExcelFile(OUTPUT_EXCEL)
        for brand in BRANDS:
            all_brands_trends[brand]   = {}
            all_brands_keywords[brand] = {}
            df_t = xls.parse(f'{brand.title()} Trends')
            df_k = xls.parse(f'{brand.title()} Keywords')
            for key, gprop, display in METRICS:
                if display in df_t.columns:
                    all_brands_trends[brand][key] = [
                        {'time': str(row['Time'])[:10], 'value': int(row[display]) if pd.notna(row[display]) else 0}
                        for _, row in df_t.iterrows()
                    ]
                else:
                    all_brands_trends[brand][key] = []
                if display in df_k.columns:
                    all_brands_keywords[brand][key] = [
                        {'query': str(row[display]), 'interest': int(row[f'{display}.1']) if pd.notna(row.get(f'{display}.1')) else 0}
                        for _, row in df_k.iterrows() if pd.notna(row[display])
                    ]
                else:
                    all_brands_keywords[brand][key] = []

    brands_js      = json.dumps(BRANDS)
    brands_data_js = json.dumps({
        b: {
            'trends':   all_brands_trends[b],
            'keywords': all_brands_keywords[b],
        } for b in BRANDS
    })
    updated_str    = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    num_weeks      = len(all_brands_trends[BRANDS[0]].get('web', []))
    print(f'  Brands: {BRANDS}')
    print(f'  Trend weeks: {num_weeks}')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Search Interests Index</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f9fafb; color: #111827; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; padding: 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 24px; font-weight: 600; margin: 0 0 4px 0; }}
        .meta-row {{ display:flex; align-items:center; gap:10px; margin:4px 0 1.5rem 0; flex-wrap:wrap; }}
        .updated {{ font-size: 12px; color: #6b7280; }}
        .brand-switcher {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:1.5rem; padding-bottom:1.5rem; border-bottom:0.5px solid #e5e7eb; }}
        .brand-btn {{ padding:7px 18px; border:1.5px solid #d1d5db; border-radius:20px; cursor:pointer; font-size:13px; font-weight:600; background:white; color:#6b7280; transition:all 0.2s; }}
        .brand-btn.active {{ background:#111827; color:white; border-color:#111827; }}
        .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 0.5px solid #e5e7eb; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 2px; }}
        .legend-text {{ font-size: 12px; color: #111827; }}
        h2 {{ font-size: 16px; font-weight: 600; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px dotted #d1d5db; display:flex; align-items:center; gap:6px; }}
        .info-icon {{ display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; border:1.5px solid #9ca3af; color:#9ca3af; font-size:10px; font-weight:700; cursor:default; flex-shrink:0; position:relative; }}
        .info-icon:hover .tooltip {{ display:block; }}
        .tooltip {{ display:none; position:absolute; top:22px; left:0; width:280px; background:#1f2937; color:white; font-size:11px; font-weight:400; padding:8px 10px; border-radius:6px; line-height:1.5; z-index:10; }}
        .buttons {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
        button {{ padding: 8px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s; }}
        .section {{ margin-bottom: 3rem; }}
        .chart-svg {{ width: 100%; height: 280px; border: 0.5px solid #d1d5db; border-radius: 6px; background: white; display: block; margin-bottom: 20px; }}
        .table-wrapper {{ overflow-x: auto; max-height: 500px; overflow-y: auto; border: 0.5px solid #d1d5db; border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        thead {{ position: sticky; top: 0; background: #f3f4f6; }}
        th {{ padding: 8px 6px; text-align: left; font-weight: 600; color: #6b7280; font-size: 10px; border-bottom: 0.5px solid #d1d5db; border-left: 3px solid #999; white-space: nowrap; }}
        td {{ padding: 8px 6px; border-bottom: 0.5px solid #e5e7eb; font-weight: 500; color: #111827; }}
        .bar-container {{ display: flex; align-items: center; gap: 4px; justify-content: flex-end; }}
        .bar {{ width: 40px; height: 12px; background: #e5e7eb; border-radius: 2px; overflow: hidden; flex-shrink: 0; }}
        .bar-fill {{ height: 100%; }}
        .interest-val {{ font-weight: 600; font-size: 10px; min-width: 20px; text-align: right; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Google Search Interests Index</h1>
    <div class="meta-row">
        <span class="updated">Last updated: {updated_str}</span>
    </div>

    <div class="brand-switcher" id="brand-switcher"></div>

    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background:#2563EB"></div><span class="legend-text">Web Search</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#DC2626"></div><span class="legend-text">Image Search</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#16A34A"></div><span class="legend-text">News Search</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#F59E0B"></div><span class="legend-text">Google Shopping</span></div>
        <div class="legend-item"><div class="legend-color" style="background:#9333EA"></div><span class="legend-text">Youtube Search</span></div>
    </div>

    <div class="section">
        <h2>Interest over time <span class="info-icon">i<span class="tooltip">Search interest over a specific time period, displayed on a relative scale from 0 to 100, where 100 signifies the peak interest for the time period of the chart. A value of 50 indicates half the popularity of the peak, and 0 suggests insufficient data.</span></span></h2>
        <div class="buttons">
            <button id="btn-all" style="background:#111827;color:white">All metrics</button>
            <button id="btn-web"      style="background:#2563EB;color:white">Web</button>
            <button id="btn-image"    style="background:#DC2626;color:white">Image</button>
            <button id="btn-news"     style="background:#16A34A;color:white">News</button>
            <button id="btn-shopping" style="background:#F59E0B;color:white">Shopping</button>
            <button id="btn-youtube"  style="background:#9333EA;color:white">YouTube</button>
        </div>
        <svg id="chart" class="chart-svg"></svg>
    </div>

    <div class="section">
        <h2>Top queries interest <span class="info-icon">i<span class="tooltip">Top queries are the most popular queries in the specified location and time period. They are scored on a relative scale, where 100 is the most searched.</span></span></h2>
        <div class="table-wrapper">
            <table><thead id="table-head"></thead><tbody id="table-body"></tbody></table>
        </div>
    </div>
</div>
<script>
const brands     = {brands_js};
const brandsData = {brands_data_js};
const colors     = {{web:'#2563EB',image:'#DC2626',news:'#16A34A',shopping:'#F59E0B',youtube:'#9333EA'}};
const metricLabels = {{web:'Web Search',image:'Image Search',news:'News Search',shopping:'Google Shopping',youtube:'Youtube Search'}};
const metrics    = ['web','image','news','shopping','youtube'];

let activeBrand   = brands[0];
let activeMetrics = new Set(metrics);

// ── Brand switcher ──────────────────────────────────────────────────────────
const switcher = document.getElementById('brand-switcher');
brands.forEach(b => {{
    const btn = document.createElement('button');
    btn.className = 'brand-btn' + (b === activeBrand ? ' active' : '');
    btn.textContent = b.charAt(0).toUpperCase() + b.slice(1);
    btn.onclick = () => {{
        activeBrand = b;
        document.querySelectorAll('.brand-btn').forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
        rebuildTable();
        drawChart();
    }};
    switcher.appendChild(btn);
}});

// ── Chart ───────────────────────────────────────────────────────────────────
function drawChart() {{
    const trendData = metrics.reduce((acc, m) => {{
        const rows = brandsData[activeBrand].trends[m] || [];
        rows.forEach((r, i) => {{
            if (!acc[i]) acc[i] = {{time: r.time}};
            acc[i][m] = r.value;
        }});
        return acc;
    }}, []);

    const svg = document.getElementById('chart');
    svg.innerHTML = '';
    const width = svg.getBoundingClientRect().width || svg.clientWidth;
    if (!width || trendData.length < 2) return;
    const height = svg.clientHeight;
    const pad = {{top:20, right:20, bottom:40, left:50}};
    const gw = width - pad.left - pad.right;
    const gh = height - pad.top - pad.bottom;
    const xStep = gw / (trendData.length - 1);

    for (let i = 0; i <= 4; i++) {{
        const y = pad.top + (gh/4)*i;
        const line = document.createElementNS('http://www.w3.org/2000/svg','line');
        line.setAttribute('x1',pad.left); line.setAttribute('y1',y);
        line.setAttribute('x2',width-pad.right); line.setAttribute('y2',y);
        line.setAttribute('stroke','#e5e7eb'); line.setAttribute('stroke-width','0.5');
        svg.appendChild(line);
        const t = document.createElementNS('http://www.w3.org/2000/svg','text');
        t.setAttribute('x',pad.left-10); t.setAttribute('y',y+4);
        t.setAttribute('text-anchor','end'); t.setAttribute('font-size','11'); t.setAttribute('fill','#9ca3af');
        t.textContent = 100-(i*25); svg.appendChild(t);
    }}

    metrics.forEach(m => {{
        if (!activeMetrics.has(m)) return;
        const pts = trendData.map((d,i) => `${{pad.left+i*xStep}},${{pad.top+gh-((d[m]||0)/100)*gh}}`).join(' ');
        const pl = document.createElementNS('http://www.w3.org/2000/svg','polyline');
        pl.setAttribute('points',pts); pl.setAttribute('fill','none');
        pl.setAttribute('stroke',colors[m]); pl.setAttribute('stroke-width','2');
        svg.appendChild(pl);
    }});

    trendData.forEach((d,i) => {{
        if (i % 4 !== 0) return;
        const x = pad.left + i*xStep;
        const t = document.createElementNS('http://www.w3.org/2000/svg','text');
        t.setAttribute('x',x); t.setAttribute('y',height-25);
        t.setAttribute('text-anchor','middle'); t.setAttribute('font-size','10'); t.setAttribute('fill','#9ca3af');
        const [yr,mo,dy] = d.time.split('-');
        const s1 = document.createElementNS('http://www.w3.org/2000/svg','tspan');
        s1.setAttribute('x',x); s1.setAttribute('dy','0'); s1.textContent = `${{mo}}/${{dy}}`;
        const s2 = document.createElementNS('http://www.w3.org/2000/svg','tspan');
        s2.setAttribute('x',x); s2.setAttribute('dy','12'); s2.textContent = `'${{yr.slice(-2)}}`;
        t.appendChild(s1); t.appendChild(s2); svg.appendChild(t);
    }});
}}

// ── Table ───────────────────────────────────────────────────────────────────
function rebuildTable() {{
    const keywordData = brandsData[activeBrand].keywords;
    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    thead.innerHTML = ''; tbody.innerHTML = '';

    const hr = document.createElement('tr');
    metrics.forEach(m => {{
        const th1 = document.createElement('th');
        th1.textContent = metricLabels[m]; th1.style.borderLeftColor = colors[m];
        hr.appendChild(th1);
        const th2 = document.createElement('th');
        th2.textContent = 'Interest'; th2.style.color = colors[m]; th2.style.borderLeft = 'none';
        hr.appendChild(th2);
    }});
    thead.appendChild(hr);

    const maxRows = Math.max(...metrics.map(m => (keywordData[m]||[]).length));
    for (let i = 0; i < maxRows; i++) {{
        const row = document.createElement('tr');
        metrics.forEach(m => {{
            const item = (keywordData[m]||[])[i];
            const td1 = document.createElement('td'); td1.textContent = item ? item.query : ''; row.appendChild(td1);
            const td2 = document.createElement('td');
            if (item) {{
                const c = document.createElement('div'); c.className = 'bar-container';
                const bar = document.createElement('div'); bar.className = 'bar';
                const fill = document.createElement('div'); fill.className = 'bar-fill';
                fill.style.width = item.interest+'%'; fill.style.backgroundColor = colors[m];
                bar.appendChild(fill);
                const val = document.createElement('span'); val.className = 'interest-val'; val.textContent = item.interest;
                c.appendChild(bar); c.appendChild(val); td2.appendChild(c);
            }}
            row.appendChild(td2);
        }});
        tbody.appendChild(row);
    }}
}}

// ── Metric toggle buttons ───────────────────────────────────────────────────
document.getElementById('btn-all').onclick = () => {{
    if (activeMetrics.size === 5) activeMetrics.clear(); else activeMetrics = new Set(metrics);
    updateMetricButtons(); drawChart();
}};
metrics.forEach(m => {{
    document.getElementById('btn-'+m).onclick = () => {{
        activeMetrics.has(m) ? activeMetrics.delete(m) : activeMetrics.add(m);
        updateMetricButtons(); drawChart();
    }};
}});
function updateMetricButtons() {{
    metrics.forEach(m => {{
        const btn = document.getElementById('btn-'+m);
        if (activeMetrics.has(m)) {{ btn.style.backgroundColor=colors[m]; btn.style.color='white'; btn.style.border='none'; }}
        else {{ btn.style.backgroundColor='white'; btn.style.color='#111827'; btn.style.border='0.5px solid #d1d5db'; }}
    }});
    const ba = document.getElementById('btn-all');
    if (activeMetrics.size===5) {{ ba.style.backgroundColor='#111827'; ba.style.color='white'; ba.style.border='none'; }}
    else {{ ba.style.backgroundColor='white'; ba.style.color='#111827'; ba.style.border='0.5px solid #d1d5db'; }}
}}

rebuildTable();
requestAnimationFrame(drawChart);
window.addEventListener('resize', drawChart);
</script>
</body>
</html>"""

    if not os.path.exists(REPO_DIR):
        print(f'  Cloning repo to {REPO_DIR}...')
        result = subprocess.run(['git', 'clone', GITHUB_REPO, REPO_DIR], capture_output=True, text=True)
        if result.returncode != 0:
            print(f'  ERROR cloning: {result.stderr}')
            sys.exit(1)
    else:
        print('  Pulling latest...')
        subprocess.run(['git', '-C', REPO_DIR, 'pull'], capture_output=True)

    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)
    print(f'  HTML written to {OUTPUT_HTML}')

    subprocess.run(['git', '-C', REPO_DIR, 'config', 'user.email', GIT_EMAIL], capture_output=True)
    subprocess.run(['git', '-C', REPO_DIR, 'config', 'user.name',  GIT_NAME], capture_output=True)
    subprocess.run(['git', '-C', REPO_DIR, 'add', 'index.html'], capture_output=True)

    commit_msg = f'Update dashboard {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    commit = subprocess.run(['git', '-C', REPO_DIR, 'commit', '-m', commit_msg], capture_output=True, text=True)
    if 'nothing to commit' in commit.stdout:
        print('  No changes to commit.')
    else:
        push = subprocess.run(['git', '-C', REPO_DIR, 'push'], capture_output=True, text=True)
        if push.returncode == 0:
            print(f'  Pushed successfully!')
            print(f'\n  Live at: https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/')
        else:
            print(f'  ERROR pushing: {push.stderr}')

print('\n' + '='*80)
print('DONE')
print('='*80)
