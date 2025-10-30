# 2. 환경 설정

## 📦 필수 패키지 설치

### Python 버전 요구사항
- Python 3.8 이상

### 패키지 설치

```bash
pip install requests pandas numpy matplotlib tqdm python-dotenv
```

또는 `requirements.txt` 파일 생성:

```text
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
tqdm>=4.65.0
python-dotenv>=1.0.0
```

설치:
```bash
pip install -r requirements.txt
```

---

## 🔑 GitHub Token 발급

GraphQL API를 사용하려면 GitHub Personal Access Token이 필요합니다.

### 1단계: GitHub 설정 접속

1. GitHub 로그인
2. 우측 상단 프로필 클릭
3. **Settings** 선택
4. 좌측 메뉴 최하단 **Developer settings** 클릭

### 2단계: Token 생성

1. **Personal access tokens** → **Tokens (classic)** 선택
2. **Generate new token** → **Generate new token (classic)** 클릭
3. Note: `robotics-trending-analyzer` (원하는 이름)
4. Expiration: 원하는 기간 선택 (90 days 추천)
5. **권한 선택**:
   - ✅ `public_repo` (공개 저장소 접근)
   - ✅ `read:org` (조직 정보 읽기)
6. **Generate token** 클릭
7. **토큰 복사** (한 번만 표시됨!)

### 3단계: .env 파일 생성

프로젝트 폴더에 `.env` 파일 생성:

```bash
# Linux/Mac
echo "GITHUB_TOKEN=ghp_your_token_here" > .env

# Windows (PowerShell)
Set-Content .env "GITHUB_TOKEN=ghp_your_token_here"
```

또는 텍스트 에디터로 직접 생성:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **보안 주의**: `.env` 파일을 GitHub에 커밋하지 마세요! `.gitignore`에 추가하세요.

---

## ⚙️ 설정 변수

### 기본 설정

```python
# 검색 구성
TOPIC = "robot"                    # GitHub 토픽
DESCRIPTION_KEYWORD = "robot"      # Description 검색 키워드
DAYS_WINDOW = 90                   # 최근 별점 분석 기간 (일)
PUSH_WINDOW_DAYS = 365             # 활동 저장소 기간 (일)
MIN_STARS = 100                    # 최소 총 별점
TOP_N = 100                        # 결과 개수

# 시각화
VISUALIZE_TOP_N = 30               # 차트에 표시할 개수

# API 성능
RESULTS_PER_PAGE = 100             # 페이지당 결과 수
SLEEP_TIME = 2                     # API 호출 간 대기 시간 (초)
PUSH_BUCKET_DAYS = 30              # Pushed-date 샤딩 간격
MAX_RETRIES = 3                    # 최대 재시도 횟수
```

### 설정 커스터마이징

#### 다른 분야 트렌드 분석

```python
# 머신러닝
TOPIC = "machine-learning"
DESCRIPTION_KEYWORD = "ml"

# 블록체인
TOPIC = "blockchain"
DESCRIPTION_KEYWORD = "crypto"

# 웹 개발
TOPIC = "web"
DESCRIPTION_KEYWORD = "react"
```

#### 시간 범위 조정

```python
# 최근 30일만 분석 (빠름)
DAYS_WINDOW = 30

# 최근 180일 분석 (상세함)
DAYS_WINDOW = 180
```

#### 필터링 강화

```python
# 인기 저장소만 (500+ 별점)
MIN_STARS = 500

# 모든 저장소 포함 (주의: 시간 오래 걸림)
MIN_STARS = 10
```

---

## 🧪 설치 확인

다음 코드를 실행하여 설치를 확인하세요:

```python
# test_setup.py
import os
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

if not token:
    print("❌ GITHUB_TOKEN이 설정되지 않았습니다!")
    print("   .env 파일을 확인하세요.")
else:
    print(f"✅ GITHUB_TOKEN 확인: {token[:10]}...")

# API 테스트
try:
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        user = response.json()
        print(f"✅ GitHub API 연결 성공!")
        print(f"   사용자: {user.get('login', 'Unknown')}")
    else:
        print(f"❌ API 인증 실패: {response.status_code}")
except Exception as e:
    print(f"❌ 연결 오류: {e}")

# 패키지 버전 확인
print("\n📦 패키지 버전:")
print(f"   pandas: {pd.__version__}")
print(f"   numpy: {np.__version__}")
print(f"   matplotlib: {matplotlib.__version__}")
```

**예상 출력:**
```
✅ GITHUB_TOKEN 확인: ghp_abcdef...
✅ GitHub API 연결 성공!
   사용자: your-username

📦 패키지 버전:
   pandas: 2.0.3
   numpy: 1.24.3
   matplotlib: 3.7.2
```

---

## 🚨 문제 해결

### Token이 인식되지 않을 때

```bash
# 환경변수 직접 확인
cat .env

# Python에서 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GITHUB_TOKEN'))"
```

### Rate Limit 에러

```python
# SLEEP_TIME 증가
SLEEP_TIME = 5  # 기본 2초 → 5초
```

### 패키지 설치 오류

```bash
# pip 업그레이드
pip install --upgrade pip

# 가상환경 사용 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

## ✅ 다음 단계

환경 설정이 완료되었다면 [3. 코드 설명](wikidocs_03_code.md)으로 이동하세요!

---

> 💡 **Tip**: Jupyter Notebook을 사용하면 코드를 단계별로 실행하며 결과를 확인할 수 있습니다.
> ```bash
> pip install jupyter
> jupyter notebook robotics_trending_clean.ipynb
> ```
