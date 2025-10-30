# 6. 문제 해결 가이드

이 페이지는 로보틱스 트렌딩 분석을 실행하면서 자주 발생할 수 있는 문제와 해결 방법을 정리한 것입니다.

---

## 6-1. GitHub 토큰 관련 오류

### ❌ 오류: `ValueError: GitHub token required!`

**증상:**
```
ValueError: GitHub token required! Set GITHUB_TOKEN in .env file
```

**원인:**
- `.env` 파일이 없거나 `GITHUB_TOKEN` 변수가 설정되지 않음

**해결 방법:**
1. 프로젝트 루트 디렉토리에 `.env` 파일 생성
2. GitHub Personal Access Token 추가:
```bash
GITHUB_TOKEN=ghp_your_token_here
```
3. 토큰 생성 방법은 [2. 환경 설정](wikidocs_02_setup.md) 참조

---

### ❌ 오류: `401 Unauthorized`

**증상:**
```
requests.exceptions.HTTPError: 401 Client Error: Unauthorized
```

**원인:**
- 잘못된 토큰 또는 만료된 토큰 사용

**해결 방법:**
1. GitHub에서 토큰 상태 확인:
   - [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. 토큰 재발급 후 `.env` 파일 업데이트
3. **주의**: 토큰 권한 확인 (최소 `public_repo` 필요)

---

### ❌ 오류: `403 Forbidden - Rate limit exceeded`

**증상:**
```
⏳ Rate limit hit. Waiting 3600s...
```
또는
```
403 Client Error: rate limit exceeded
```

**원인:**
- GitHub API 호출 한도 초과
  - **인증된 요청**: 5,000 requests/hour
  - **GraphQL API**: 별도 계산 (포인트 시스템)

**해결 방법:**

**방법 1: 대기**
- 코드가 자동으로 대기 후 재시도
- Rate limit 리셋 시간까지 자동 대기 (최대 1시간)

**방법 2: Sleep 시간 증가**
```python
SLEEP_TIME = 3  # 기본 2초 → 3초로 증가
```

**방법 3: 토큰 확인**
```bash
# 현재 남은 API 호출 횟수 확인
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

출력 예시:
```json
{
  "resources": {
    "core": {
      "limit": 5000,
      "remaining": 4999,
      "reset": 1234567890
    },
    "graphql": {
      "limit": 5000,
      "remaining": 4950,
      "reset": 1234567890
    }
  }
}
```

---

## 6-2. 네트워크 및 타임아웃 오류

### ❌ 오류: `requests.exceptions.Timeout`

**증상:**
```
requests.exceptions.ReadTimeout: HTTPSConnectionPool
```

**원인:**
- 네트워크 연결 불안정
- GitHub API 응답 지연

**해결 방법:**

**방법 1: 재실행**
- 코드는 자동으로 3번까지 재시도 (MAX_RETRIES=3)
- 실패 시 해당 저장소는 건너뜀

**방법 2: 타임아웃 시간 증가**
`github_api_call()` 함수 수정:
```python
resp = SESSION.get(url, params=params, headers=headers, timeout=60)  # 30 → 60초
```

**방법 3: 인터넷 연결 확인**
```bash
ping github.com
curl -I https://api.github.com
```

---

### ❌ 오류: `Connection reset by peer`

**증상:**
```
ConnectionResetError: [Errno 104] Connection reset by peer
```

**원인:**
- GitHub API 서버 일시적 문제
- 너무 빠른 연속 요청

**해결 방법:**
1. `SLEEP_TIME` 증가:
```python
SLEEP_TIME = 3  # 또는 5초
```

2. 재실행 (자동 재시도 로직이 처리)

---

## 6-3. 데이터 및 결과 관련 문제

### ❌ 문제: "검색된 저장소가 너무 적어요"

**증상:**
```
✅ Found 50 unique repositories (stars >= 100)
```
예상보다 적은 저장소 발견

**원인:**
- `MIN_STARS` 값이 너무 높음
- `TOPIC` 또는 `DESCRIPTION_KEYWORD`가 너무 구체적

**해결 방법:**

**방법 1: MIN_STARS 낮추기**
```python
MIN_STARS = 50  # 100 → 50으로 변경
```

**방법 2: DESCRIPTION_KEYWORD 제거**
```python
DESCRIPTION_KEYWORD = None  # 토픽만 검색
```

**방법 3: TOPIC 변경**
```python
# 더 포괄적인 토픽 사용
TOPIC = "robotics"  # "robot" 대신
```

---

### ❌ 문제: "최근 별점이 0인 저장소가 많아요"

**증상:**
```
Total with recent stars: 50
```
676개 저장소 중 50개만 최근 별점 보유

**원인:**
- `DAYS_WINDOW`가 너무 짧음 (예: 7일)
- 많은 저장소가 최근에 별점을 받지 못함

**해결 방법:**

**방법 1: 기간 확대**
```python
DAYS_WINDOW = 180  # 90일 → 180일 (6개월)
```

**방법 2: 전체 별점 순위로 변경**
```python
# 최근 별점 대신 전체 별점으로 정렬
result_df = result_df.sort_values("total_stars", ascending=False).head(TOP_N)
```

---

### ❌ 문제: "commaai/openpilot의 별점이 0이에요"

**증상:**
Top 저장소의 `recent_stars`가 0으로 표시

**원인:**
- REST API 사용 중 (GraphQL 미사용)
- 400페이지 한계로 최근 데이터 미도달

**해결 방법:**
✅ **현재 코드는 GraphQL을 사용하므로 이 문제 없음**

만약 REST API를 사용 중이라면:
```python
# get_recent_stars() 함수가 GraphQL을 사용하는지 확인
# GraphQL 쿼리가 포함되어 있어야 함:
query = """
query($owner: String!, $repo: String!, $last: Int!, $before: String) {
  repository(owner: $owner, name: $repo) {
    stargazers(last: $last, before: $before) { ... }
  }
}
"""
```

---

## 6-4. 성능 및 실행 시간 문제

### ❌ 문제: "실행 시간이 너무 오래 걸려요"

**증상:**
- 예상 시간: 30-60분
- 실제 시간: 2시간 이상

**원인:**
- 너무 많은 저장소 분석
- `max_pages=None` (무제한 수집)

**해결 방법:**

**방법 1: 제한 모드 사용 (빠른 테스트)**
```python
# max_pages 추가 (최근 별점 카운팅 섹션)
recent_stars = get_recent_stars(owner, name, since_date, max_pages=5)
```
- 실행 시간: 5-10분
- 정확도: 감소 (최근 별점이 많은 저장소는 과소 측정)

**방법 2: MIN_STARS 올리기**
```python
MIN_STARS = 500  # 100 → 500 (분석 대상 축소)
```

**방법 3: SLEEP_TIME 줄이기** (주의: Rate limit 위험)
```python
SLEEP_TIME = 1  # 2 → 1초 (권장하지 않음)
```

---

### ❌ 문제: "중간에 멈춘 것 같아요"

**증상:**
- Progress bar가 오래 멈춤
- 응답 없음

**원인:**
- 특정 저장소의 별점이 매우 많음 (예: 50,000+)
- GraphQL 페이지 수집 중

**해결 방법:**
1. **대기**: 정상 동작입니다
   - 큰 저장소는 최대 5-10분 소요 가능
   - Progress bar는 저장소 단위로 업데이트

2. **확인 방법**:
```python
# tqdm progress bar에서 현재 처리 중인 저장소 확인
# "Processing repos: 50%|█████     | 338/676 [18:23<18:23, 3.26s/it]"
# → 338번째 저장소 처리 중
```

3. **타임아웃 추가** (선택):
```python
# get_recent_stars() 함수에 안전장치 추가
if page > 200:  # 최대 20,000개 별점만 수집
    break
```

---

## 6-5. 시각화 오류

### ❌ 오류: `ValueError: x and y must have same first dimension`

**증상:**
```
ValueError: x and y must have same first dimension, but have shapes (10,) and (5,)
```

**원인:**
- Top 30 미만의 결과 (예: 15개만 발견)
- 시각화 코드는 30개 가정

**해결 방법:**

**방법 1: VISUALIZE_TOP_N 조정**
```python
# 결과 개수에 맞춰 자동 조정
VISUALIZE_TOP_N = min(len(result_df), 30)
```

**방법 2: 시각화 섹션 수정**
```python
# 데이터 개수 확인 후 시각화
if len(result_df) >= 30:
    # 3패널 차트 생성
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
elif len(result_df) >= 10:
    # 1패널 차트만 생성
    fig, ax1 = plt.subplots(1, 1)
    bars1 = ax1.bar(range(len(result_df)), result_df['recent_stars'])
else:
    print("⚠️  시각화하기엔 데이터가 부족합니다 (최소 10개 필요)")
```

---

### ❌ 오류: `RuntimeError: Failed to process string with tex`

**증상:**
Matplotlib LaTeX 렌더링 오류

**원인:**
- LaTeX 설치 안 됨 (일반적으로 문제 없음)

**해결 방법:**
```python
# matplotlib 설정에서 LaTeX 비활성화
plt.rcParams['text.usetex'] = False
```

---

## 6-6. CSV 파일 오류

### ❌ 오류: `UnicodeDecodeError` (CSV 읽기 시)

**증상:**
```python
pd.read_csv("robotics_trending_top100_20251030_1806.csv")
# UnicodeDecodeError: 'utf-8' codec can't decode...
```

**원인:**
- 저장소 description에 특수 문자 포함

**해결 방법:**
✅ **현재 코드는 UTF-8로 저장하므로 문제 없음**

만약 오류 발생 시:
```python
# 인코딩 명시
df = pd.read_csv("robotics_trending_top100.csv", encoding="utf-8")

# 또는 오류 무시
df = pd.read_csv("robotics_trending_top100.csv", encoding="utf-8", errors="ignore")
```

---

### ❌ 문제: "CSV 파일이 생성되지 않았어요"

**증상:**
- 코드 실행 완료
- CSV 파일 없음

**원인:**
- 최근 별점을 가진 저장소가 0개
- 파일 저장 권한 문제

**해결 방법:**

**방법 1: 결과 확인**
```python
# 저장 전 데이터 확인
print(f"Trending repos count: {len(trending)}")
print(result_df.head())
```

**방법 2: 절대 경로 사용**
```python
import os
out_csv = os.path.join(os.getcwd(), f"robotics_trending_top{TOP_N}_{timestamp}.csv")
print(f"Saving to: {out_csv}")
result_df.to_csv(out_csv, index=False, encoding="utf-8")
```

**방법 3: 권한 확인**
```bash
# Linux/Mac
ls -la
# 현재 디렉토리 쓰기 권한 확인
```

---

## 6-7. Jupyter Notebook 관련 문제

### ❌ 문제: "ImportError: No module named 'dotenv'"

**증상:**
```
ImportError: No module named 'dotenv'
```

**원인:**
- `python-dotenv` 패키지 미설치

**해결 방법:**
```bash
# Notebook 내에서 실행
!pip install python-dotenv
```

또는 터미널에서:
```bash
pip install python-dotenv
```

---

### ❌ 문제: "Kernel died with exit code 137"

**증상:**
Jupyter Notebook 커널 종료

**원인:**
- 메모리 부족 (OOM)
- 너무 많은 데이터 처리

**해결 방법:**

**방법 1: 저장소 수 제한**
```python
MIN_STARS = 500  # 분석 대상 축소
```

**방법 2: 데이터 정리**
```python
# 각 섹션 후 메모리 정리
import gc
gc.collect()
```

**방법 3: 시각화 간소화**
```python
VISUALIZE_TOP_N = 10  # 30 → 10개만 시각화
```

---

## 6-8. 자주 묻는 질문 (FAQ)

### Q1: GraphQL과 REST API의 차이는?

**A:** 
- **REST API**: 
  - 순방향 페이지네이션 (오래된 별점부터)
  - 400페이지 한계 (40,000개 별점)
  - 최근 별점이 많으면 도달 불가
  
- **GraphQL API**:
  - 역방향 페이지네이션 (최신 별점부터) ✅
  - 무제한 페이지 수집 가능
  - 최근 데이터에 직접 접근

→ **현재 코드는 GraphQL 사용** (정확도 100%)

---

### Q2: `max_pages=None`과 `max_pages=5`의 차이는?

**A:**
| 설정 | 실행 시간 | 정확도 | 권장 용도 |
|------|----------|--------|----------|
| `max_pages=None` | 30-60분 | 100% | **프로덕션 (최종 분석)** |
| `max_pages=5` | 5-10분 | 70-90% | 빠른 테스트 |
| `max_pages=1` | 2-3분 | 50-70% | 개발/디버깅 |

---

### Q3: `PUSH_WINDOW_DAYS`는 왜 365일인가요?

**A:** 
- 최근 1년 동안 **한 번이라도 푸시된 저장소** 검색
- 레거시 프로젝트도 포함 (ROS2 공식 저장소 등)
- 값을 줄이면 (예: 90일) 최근 활동 저장소만 검색

```python
PUSH_WINDOW_DAYS = 90   # 최근 3개월 활동 저장소만
PUSH_WINDOW_DAYS = 365  # 최근 1년 활동 저장소 (기본값)
```

---

### Q4: 여러 토픽을 동시에 검색할 수 있나요?

**A:** 
가능합니다. 검색 쿼리 수정:

```python
# 복수 토픽 검색
TOPIC = "robot"
query_template = f'(topic:robot OR topic:robotics OR topic:ros2) stars:>={MIN_STARS} pushed:{{start}}..{{end}}'
```

또는 description 활용:
```python
DESCRIPTION_KEYWORD = "robot OR robotics OR autonomous"
```

---

### Q5: API 호출 횟수를 줄이려면?

**A:**
1. **MIN_STARS 올리기**: 분석 대상 축소
```python
MIN_STARS = 500  # 500개 이상만 분석
```

2. **SLEEP_TIME 증가**: Rate limit 여유 확보
```python
SLEEP_TIME = 3  # 안전 마진 확보
```

3. **결과 캐싱**: 이전 결과 재사용
```python
# 이전 CSV 파일 로드
cached_df = pd.read_csv("robotics_trending_top100_20251030_1806.csv")
```

---

## 6-9. 에러 로그 확인 방법

### 전체 에러 추적
```python
import traceback

try:
    # 코드 실행
    recent_stars = get_recent_stars(owner, name, since_date)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    traceback.print_exc()  # 전체 스택 트레이스 출력
```

### API 응답 상태 확인
```python
# github_api_call() 함수 수정 (디버깅용)
resp = SESSION.get(url, params=params, headers=headers, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Headers: {resp.headers}")
print(f"Response: {resp.text[:500]}")  # 처음 500자만
```

---

## 6-10. 추가 도움말

### 공식 문서
- [GitHub REST API 문서](https://docs.github.com/en/rest)
- [GitHub GraphQL API 문서](https://docs.github.com/en/graphql)
- [GitHub Rate Limit](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)

### 커뮤니티 지원
- GitHub Issues: 오류 보고
- Stack Overflow: `github-api` 태그 검색

---

**다른 문제가 있나요?**
- 에러 메시지와 함께 GitHub Issues에 문의하세요
- 실행 환경 정보 포함 (Python 버전, OS 등)

---

**목차로 돌아가기:** [0. 시작하기](wikidocs_00_index.md)
