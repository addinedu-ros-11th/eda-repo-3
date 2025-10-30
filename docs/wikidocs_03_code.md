# 3. 코드 설명

## 📋 전체 구조 개요

```
1. API 초기화 및 설정
   ↓
2. 저장소 검색 (Pushed-date 샤딩)
   ↓
3. GraphQL로 최근 별점 수집
   ↓
4. 결과 저장 및 시각화
```

---

## 3-1. API 초기화

### 패키지 임포트

```python
import os, time, datetime as dt
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from tqdm import tqdm
from dotenv import load_dotenv
```

### GitHub API 설정

```python
# 환경변수 로드
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("GitHub token required! Set GITHUB_TOKEN in .env file")

# Session 생성 (헤더 자동 포함)
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "trending-robotics/1.0"
})

# API 엔드포인트
API_BASE = "https://api.github.com"
SEARCH_API = f"{API_BASE}/search/repositories"
STARS_API = f"{API_BASE}/repos/{{owner}}/{{repo}}/stargazers"
```

**핵심 포인트:**
- `Session` 사용으로 헤더 재사용
- `Authorization` Bearer 토큰 방식
- API 버전 명시로 호환성 보장

---

## 3-2. 저장소 검색

### Pushed-date 샤딩이란?

GitHub Search API는 **최대 1,000개** 결과만 반환합니다. 이를 우회하기 위해 날짜 범위를 나눕니다:

```
전체 365일 범위:
├── 2024-10-31 ~ 2024-11-29 (30일) → 최대 1,000개
├── 2024-11-30 ~ 2024-12-29 (30일) → 최대 1,000개
├── ...
└── 2025-10-01 ~ 2025-10-30 (30일) → 최대 1,000개

총 13개 샤드 = 최대 13,000개 접근 가능!
```

### 날짜 범위 생성 함수

```python
def daterange(start: dt.date, end: dt.date, step_days: int):
    """날짜 범위를 step_days 간격으로 분할"""
    cur = start
    delta = dt.timedelta(days=step_days-1)
    while cur <= end:
        window_end = min(end, cur + delta)
        yield cur, window_end
        cur = window_end + dt.timedelta(days=1)

def iso_date(d: dt.date) -> str:
    """날짜를 ISO 형식으로 변환"""
    return d.isoformat()
```

### 검색 실행

```python
# 시간 윈도우 계산
since_date = (dt.datetime.utcnow() - dt.timedelta(days=90)).isoformat()
end_date = dt.date.today()
start_date = end_date - dt.timedelta(days=364)  # 365일

# Pushed-date 윈도우 생성
windows = list(daterange(start_date, end_date, 30))  # 30일 간격

# 검색 쿼리 템플릿
query_template = (
    f'(topic:robot OR (robot in:description)) '
    f'stars:>=100 '
    f'pushed:{{start}}..{{end}}'
)

# 모든 윈도우에 대해 검색
all_repos = {}

for start, end in windows:
    query = query_template.format(
        start=iso_date(start), 
        end=iso_date(end)
    )
    page = 1
    
    while page <= 10:  # 최대 10페이지 (1,000개)
        resp = SESSION.get(
            SEARCH_API,
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 100,
                "page": page
            }
        )
        
        if resp.status_code != 200:
            break
            
        data = resp.json()
        repos = data.get("items", [])
        
        if not repos:
            break
        
        # 중복 제거를 위해 dict 사용
        for repo in repos:
            all_repos[repo["full_name"]] = repo
        
        page += 1
        time.sleep(2)  # Rate limit 방지

print(f"✅ Found {len(all_repos):,} unique repositories")
```

**결과:**
```
✅ Found 676 unique repositories
```

---

## 3-3. GraphQL 별점 수집

### REST API의 한계

```python
# REST API 방식 (❌ 작동 안 함)
# https://api.github.com/repos/owner/repo/stargazers?page=1

문제점:
1. 페이지 400까지만 접근 (40,000개)
2. 오래된 별점부터 반환 (oldest-first)
3. 최근 별점 위치: 58,657번째 → 접근 불가!
```

### GraphQL의 혁신

```python
def get_recent_stars(owner: str, repo: str, since_date: str, 
                     max_pages: int = None) -> int:
    """
    GraphQL API로 최근 별점만 역순 페이지네이션으로 조회
    
    Args:
        owner: 저장소 소유자
        repo: 저장소 이름
        since_date: 기준 날짜 (ISO 8601)
        max_pages: 최대 페이지 수 (None=무제한)
    
    Returns:
        최근 90일 이내 별점 수
    """
    
    # GraphQL 쿼리: 역순 페이지네이션 (최신부터)
    query = """
    query($owner: String!, $repo: String!, $last: Int!, $before: String) {
      repository(owner: $owner, name: $repo) {
        stargazers(last: $last, before: $before) {
          edges {
            starredAt
            cursor
          }
          pageInfo {
            hasPreviousPage
            startCursor
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    graphql_url = "https://api.github.com/graphql"
    
    recent_count = 0
    before_cursor = None
    found_old_star = False
    page = 0
    
    while True:
        page += 1
        
        # max_pages 제한 체크
        if max_pages and page > max_pages:
            break
        
        # 안전장치: 최대 200페이지
        if page > 200:
            break
        
        # GraphQL 변수
        variables = {
            "owner": owner,
            "repo": repo,
            "last": 100,  # GraphQL 한계
            "before": before_cursor
        }
        
        try:
            response = SESSION.post(
                graphql_url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data:
                    return 0
                
                stargazers = data.get("data", {}).get("repository", {}).get("stargazers", {})
                edges = stargazers.get("edges", [])
                page_info = stargazers.get("pageInfo", {})
                
                if not edges:
                    break
                
                # 현재 페이지의 최근 별점 카운트
                for edge in edges:
                    starred_at = edge.get("starredAt", "")
                    if starred_at >= since_date:
                        recent_count += 1
                    else:
                        found_old_star = True
                
                # 90일 이전 별점 발견 시 중단
                if found_old_star:
                    break
                
                # 이전 페이지가 없으면 종료
                if not page_info.get("hasPreviousPage"):
                    break
                
                # 다음 페이지 커서
                before_cursor = page_info.get("startCursor")
                time.sleep(1)  # Rate limit 방지
                
            elif response.status_code == 429:
                time.sleep(60)
            else:
                break
                
        except Exception as e:
            break
    
    return recent_count
```

### 작동 원리 시각화

```
commaai/openpilot (총 58,657개 별점)

GraphQL 역순 페이지네이션:
┌─────────────────────────────────┐
│ Page 1: 58,657 → 58,558 (최신)  │ ✅ 2025-10-30 ~ 2025-10-25
├─────────────────────────────────┤
│ Page 2: 58,557 → 58,458         │ ✅ 2025-10-24 ~ 2025-10-18
├─────────────────────────────────┤
│ Page 3: 58,457 → 58,358         │ ✅ 2025-10-17 ~ 2025-10-10
├─────────────────────────────────┤
│ ...                             │
├─────────────────────────────────┤
│ Page 33: 55,457 → 55,358        │ ✅ 2025-08-05 ~ 2025-08-02
├─────────────────────────────────┤
│ Page 34: 55,357 → 55,258        │ ❌ 2025-07-31 (90일 이전!)
└─────────────────────────────────┘
                ↓
         자동 중단 및 반환
         결과: 3,222개
```

---

## 3-4. 결과 저장 및 시각화

### 데이터 수집 및 정렬

```python
trending = []

for repo in tqdm(all_repos.values(), desc="Processing repos"):
    owner, name = repo["full_name"].split("/")
    
    # GraphQL로 최근 별점 수집
    recent_stars = get_recent_stars(owner, name, since_date, max_pages=None)
    
    if recent_stars > 0:
        trending.append({
            "full_name": repo["full_name"],
            "description": repo["description"],
            "language": repo["language"],
            "total_stars": max(repo["stargazers_count"], recent_stars),
            "recent_stars": recent_stars,
            "url": repo["html_url"],
            "topics": ",".join(repo.get("topics", []))
        })
        
    time.sleep(2)

# DataFrame 생성 및 정렬
result_df = pd.DataFrame(trending)
result_df = result_df.sort_values("recent_stars", ascending=False).head(100)
```

### CSV 저장

```python
timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
out_csv = f"robotics_trending_top100_{timestamp}.csv"
result_df.to_csv(out_csv, index=False, encoding="utf-8")

print(f"✅ Saved to: {out_csv}")
```

### 시각화

```python
# Top 30 추출
top_n_df = result_df.head(30).copy()
top_n_df['repo_name'] = top_n_df['full_name'].apply(lambda x: x.split('/')[-1])

# 차트 설정
plt.rcParams['figure.figsize'] = (18, 16)
plt.rcParams['font.size'] = 10

# 3개 서브플롯 생성
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, height_ratios=[3, 2.5, 2])

# 컬러 팔레트
colors = plt.cm.tab20(np.linspace(0, 1, 20))
colors = np.vstack((colors, plt.cm.Set3(np.linspace(0, 1, 10))))

# 바 차트 그리기
bars1 = ax1.bar(range(10), top_n_df['recent_stars'].head(10), color=colors[:10])
bars2 = ax2.bar(range(10), top_n_df['recent_stars'].iloc[10:20], color=colors[10:20])
bars3 = ax3.bar(range(10), top_n_df['recent_stars'].iloc[20:30], color=colors[20:30])

# 제목
ax1.set_title('Top 10 Trending Robotics Repositories', fontsize=14, pad=20)
ax2.set_title('11-20th Trending Repositories', fontsize=14, pad=20)
ax3.set_title('21-30th Trending Repositories', fontsize=14, pad=20)

# 값 라벨 추가
def add_value_labels(ax, bars):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height,
                f'{int(height):,}', ha='center', va='bottom', fontsize=9)

add_value_labels(ax1, bars1)
add_value_labels(ax2, bars2)
add_value_labels(ax3, bars3)

# 축 설정
def setup_axes(ax, repos):
    ax.set_xticks(range(len(repos)))
    ax.set_xticklabels(repos, rotation=45, ha='right')
    ax.set_ylabel('Recent Stars', fontsize=12, labelpad=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))

setup_axes(ax1, top_n_df['repo_name'].head(10).tolist())
setup_axes(ax2, top_n_df['repo_name'].iloc[10:20].tolist())
setup_axes(ax3, top_n_df['repo_name'].iloc[20:30].tolist())

plt.tight_layout()
plt.show()
```

### 통계 출력

```python
print(f"Total recent stars (top 30): {top_n_df['recent_stars'].sum():,}")
print(f"Average: {top_n_df['recent_stars'].mean():.1f}")
print(f"Median: {top_n_df['recent_stars'].median():.1f}")

# 언어 분포
lang_stats = top_n_df['language'].value_counts()
print(f"\nLanguage Distribution (top 30):")
for lang, count in lang_stats.head(5).items():
    percentage = (count / len(top_n_df)) * 100
    lang_name = lang if pd.notna(lang) else 'Not specified'
    print(f"  {lang_name}: {count} repos ({percentage:.1f}%)")
```

---

## 📊 실행 결과 예시

```
Processing repos: 100%|██████████| 676/676 [36:11<00:00,  3.21s/it]

✅ Completed! Top 100 repositories identified
   Total with recent stars: 669
   Average recent stars (top 100): 352.5

✅ Saved to: robotics_trending_top100_20251030_1806.csv

================================================================================
STATISTICS
================================================================================
Total recent stars (top 30): 24,381
Average: 812.7
Median: 517.5

Language Distribution (top 30):
  Python: 16 repos (53.3%)
  C++: 2 repos (6.7%)
  Jupyter Notebook: 2 repos (6.7%)
  Go: 1 repos (3.3%)
  JavaScript: 1 repos (3.3%)
```

---

## 🔍 핵심 코드 분석

### 1. Rate Limit 처리

```python
if response.status_code == 429:
    # Rate limit 초과 시 60초 대기
    time.sleep(60)
```

### 2. 조기 종료 최적화

```python
# 90일 이전 별점 발견 시 즉시 중단
if starred_at < since_date:
    found_old_star = True
    break
```

### 3. 에러 핸들링

```python
try:
    response = SESSION.post(graphql_url, ...)
    if "errors" in data:
        return 0  # 에러 발생 시 0 반환
except Exception as e:
    break  # 예외 발생 시 루프 종료
```

---

## 다음 단계

[4. 실행 결과](wikidocs_04_results.md)에서 상세한 분석 결과를 확인하세요!

---

> 💡 **Tip**: GraphQL Playground에서 쿼리를 테스트해보세요:
> https://docs.github.com/en/graphql/overview/explorer
