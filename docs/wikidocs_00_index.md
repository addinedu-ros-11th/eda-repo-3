# 로보틱스 트렌딩 저장소 분석기

> GitHub API를 활용한 로보틱스 트렌드 분석 완벽 가이드

## 📖 목차

### [1. 프로젝트 소개](wikidocs_01_intro.md)
- 프로젝트 개요
- 주요 기능
- 핵심 성과

### [2. 환경 설정](wikidocs_02_setup.md)
- 필수 패키지 설치
- GitHub Token 발급
- 설정 변수

### [3. 코드 설명](wikidocs_03_code.md)
#### 3-1. API 초기화
- GitHub API 설정
- Session 구성

#### 3-2. 저장소 검색
- 검색 쿼리 구성
- Pushed-date 샤딩

#### 3-3. GraphQL 별점 수집
- 역방향 페이지네이션
- REST API vs GraphQL

#### 3-4. 결과 저장 및 시각화
- CSV 저장
- 차트 생성

### [4. 실행 결과](wikidocs_04_results.md)
- Top 10 트렌딩 저장소
- 통계 요약
- 언어 분포

### [5. 전체 소스코드](wikidocs_05_fullcode.md)
- 복사 가능한 완전한 코드
- Jupyter Notebook 다운로드

### [6. 트러블슈팅](wikidocs_06_troubleshooting.md)
- 자주 묻는 질문
- 문제 해결 방법

---

## 🚀 빠른 시작

```python
# 1. 패키지 설치
pip install requests pandas numpy matplotlib tqdm python-dotenv

# 2. GitHub Token 설정
echo "GITHUB_TOKEN=your_token_here" > .env

# 3. 코드 실행
# [전체 소스코드] 페이지에서 복사하여 실행
```

## 📊 주요 결과 미리보기

| 순위 | 저장소 | 최근 90일 별점 |
|------|--------|---------------|
| 1 | commaai/openpilot | 3,222⭐ |
| 2 | huggingface/lerobot | 2,691⭐ |
| 3 | Vector-Wangel/XLeRobot | 2,200⭐ |

**분석 데이터**: 676개 저장소 → Top 100 추출  
**실행 시간**: 약 37분  
**데이터 품질**: GraphQL 무제한 수집으로 100% 정확도

---

## 💡 이 프로젝트에서 배울 수 있는 것

✅ GitHub REST API와 GraphQL API의 차이점  
✅ API Rate Limit 극복 전략  
✅ 대규모 데이터 수집 최적화  
✅ 데이터 시각화 및 분석  

---

## 📚 참고 자료

- [GitHub REST API 공식 문서](https://docs.github.com/en/rest)
- [GitHub GraphQL API 공식 문서](https://docs.github.com/en/graphql)
- [전체 프로젝트 GitHub 저장소](https://github.com/addinedu-ros-11th/eda-repo-3)

---

**작성일**: 2025-10-30  
**버전**: 1.0  
**라이선스**: MIT
