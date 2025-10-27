# 🤖 TrendBot - GitHub 오픈소스 데이터를 활용한 로봇공학 트렌드 분석

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 프로젝트 개요

로봇 기술은 자율주행, 조작, 인공지능 등 다양한 분야로 확산되고 있으며, 오픈소스 기술은 연구와 산업 혁신의 핵심 동력이 되고 있습니다. 본 프로젝트는 **GitHub의 로봇 관련 저장소를 수집/분석**하여 주요 기술 흐름, 인기 언어, 연구 트렌드를 시각적으로 파악하고, 특허 및 논문 데이터와 비교하여 로봇 관련 주요 기술의 트렌드를 확인합니다.

## 🎯 프로젝트 목표

- GitHub 로봇공학 Repository 데이터 수집 및 분석
- 주요 기술 흐름 및 인기 프로그래밍 언어 파악
- 산업계(특허), 학계(논문)와의 연계성 분석
- 오픈소스 생태계의 발전 과정 시각화

## 👥 팀 구성 (Team TrendBot)

| 이름 | 역할 |
|------|------|
| 차동현 | Kipris 특허 데이터 수집, 분석, 프로젝트 관리 |
| 최종명 | GitHub 데이터 수집, 산업계 관련 분석 |
| 박용근 | GitHub 데이터 수집, 산업계 관련 분석 |
| 강동현 | DB 관리, 논문 데이터 수집, 분석, 소스코드 관리 |

## 📊 데이터 수집

### 1. GitHub Repository Data
- **API**: GitHub REST API
- **수집 항목**: name, stars, forks, language, created_at, updated_at, topics, license, owner, description, readme, is_forked
- **데이터 규모**: 약 176개 Repository
- **선정 기준**: 
  - 키워드: reinforcement-learning, robotics, ros, slam, drone
  - Stars ≥ 1000
  - 최근 90일 이내 push 활동

### 2. 논문 데이터 (arXiv)
- **API**: arXiv API
- **수집 항목**: arxiv_id, title, abstract, published, authors, primary_category, categories
- **데이터 규모**: 약 47,000개 논문

### 3. 특허 데이터 (Kipris)
- **API**: Kipris API
- **수집 항목**: inventionTitle, astrtCont, applicationDate, registerDate, keyword
- **데이터 규모**: 약 3,300개 특허

## 🛠️ 기술 스택

- **언어**: Python
- **주요 라이브러리**:
  - 데이터 수집: requests, github API
  - 데이터 처리: pandas, numpy
  - 자연어 처리: TF-IDF, Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)
  - 시각화: matplotlib, seaborn
  - 데이터베이스: SQLite/PostgreSQL

## 🔍 데이터 전처리

1. **중복 제거** - 중복된 Repository 제거
2. **텍스트 클리닝** - 노이즈 제거 및 정규화
3. **언어 필터링** - 주요 프로그래밍 언어 중심 분석
4. **키워드 분리 및 정규화** - 토픽 기반 분류
5. **유사도 검증**:
   - **TF-IDF**: 문서 내 단어의 중요도 계산
   - **Sentence Transformer**: 다국어 문장 임베딩을 통한 의미적 유사도 계산

## 📈 주요 분석 결과

### 1. GitHub Repository 분석

#### 개발 언어 분포
- **Python**과 **C++**이 압도적으로 많이 사용됨
- 로봇공학 오픈소스 프로젝트의 핵심 언어로 확립

#### Stars와 Forks의 관계
- 강한 비례 관계 확인
- 인기 있는 프로젝트는 확산력(Fork)으로 이어짐

#### 시기별 발전 단계
- **2010년~2016년**: 도입기
- **2017년~2021년**: 성장기
- **2022년~2025년**: 성숙기

#### 토픽별 활동
- Reinforcement Learning, Robotics, ROS, SLAM이 주요 토픽
- Drone 관련 Repository는 수가 적지만 높은 Star 수 보유

### 2. 산업 연계성 분석

#### Top 10 Repository (종합 점수 기준)
종합점수 = 0.25×Activity + 0.25×Contributor + 0.20×IssueCloseRate + 0.15×PRMergeRate + 0.15×Star

| 순위 | Repository | 언어 | 점수 |
|------|------------|------|------|
| 1 | commaai/openpilot | Python | 4.22 |
| 2 | unslothai/unsloth | Python | 4.06 |
| 3 | ray-project/ray | Python | 3.99 |
| 4 | PX4/PX4-Autopilot | Python | 3.73 |
| 5 | zauberzeug/nicegui | Python | 3.57 |
| 6 | ArduPilot/ardupilot | C++ | 3.55 |
| 7 | AtsushiSakai/PythonRobotics | Python | 2.94 |
| 8 | Unity-Technologies/ml-agents | C# | 2.63 |
| 9 | labmlai/annotated_deep_learning_paper_implementations | Python | 2.40 |
| 10 | carla-simulator/carla | C++ | 2.39 |

#### 산업 적용 사례
- **ArduPilot**: 해양 로봇(ROV/AUV), 농업, 수색구조 등에 활용
- **CARLA**: NVIDIA, Intel, Toyota와 협력한 자율주행 시뮬레이션
- **PX4**: Dronecode Foundation 주도의 오픈소스 드론 OS

### 3. 특허 데이터 연계성

#### 의미 유사도 분석
- 특정 GitHub 프로젝트가 실제 특허와 높은 유사도를 보임
- 평균 유사도는 낮지만, 최대 유사도는 높음 → 개념적 확산 발생

#### 기술 전이 시간
- **GitHub → 특허**: 약 3~5년의 시차
- **SLAM, Robotics**: GitHub-특허 간 직접적 연동 확인
- **ROS**: 산업 적용까지 약 4년 소요
- **Reinforcement Learning**: 산업 적용까지 약 3~4년 소요
- **Drone**: 직접적 전이는 약함

#### 트렌드 분석
- GitHub: 2010년 이후 증가, 2015~2020년 집중
- 특허: GitHub보다 3~5년 뒤늦게 증가세
- 오픈소스에서 실험/연구된 기술이 이후 산업적 응용으로 확산

### 4. 논문 데이터 연계성

#### 시간적 상관관계
- **논문 → GitHub**: 약 3년의 시차
- 논문 수 증가 후 약 3년 뒤 Repository 수 증가
- 연구 결과가 오픈소스 생태계 활성화를 촉진

#### 주제 일치도
- "robot", "learning", "control" 등 핵심 개념 공유
- **arXiv**: 이론적/방법론적 표현 중심
- **GitHub**: 구현/적용 표현 중심

#### 상호 참조 현황
- 약 5%만이 서로를 직접 연결
- 대칭적 구조로 나타남
- 연구와 실무가 연결되기 시작했지만 초기 단계

#### 인기도 관계
- 논문 내용과 유사한 오픈소스일수록 Star 수가 높은 경향
- 연구 내용이 실무에 영향을 미침

## 🎓 주요 발견 및 시사점

### 산업 연계성
1. **Python/C++** 중심으로 발전 중
2. **ROS2 확산**으로 관련 프로젝트 급성장
3. **자율주행, SLAM, 딥러닝**이 최근 3년간 핵심 키워드
4. GitHub 오픈소스가 산업 특허의 **선행 지표** 역할 수행

### 특허 연계성
1. **Reinforcement Learning, Robotics, SLAM**은 오픈소스 혁신이 산업 특허화의 주요 경로
2. GitHub 기술 트렌드가 특허보다 **3~5년 선행**
3. **ROS/SLAM**처럼 인프라/핵심 기술은 특허화 속도가 빠름

### 논문 연계성
1. 논문 발표 후 약 **3년 뒤** Repository 수 증가
2. 연구와 개발은 **같은 주제를 공유하지만 초점은 다름**
3. 연구와 실무의 직접적 연결은 **초기 단계**
4. 논문과 유사한 오픈소스일수록 **인기도가 높음**

## ⚠️ 제한사항

- API 수집 제한으로 일부 데이터 누락 가능성
- README 품질 편차로 키워드 분석 정확도 제한
- 논문, 특허 자료의 전체 내용을 분석하지 못함
- GitHub API 분석 경험 부족으로 인한 시행착오

## 📂 프로젝트 구조

```
eda-repo-3/
├── data/
│   ├── github/          # GitHub Repository 데이터
│   ├── arxiv/           # 논문 데이터
│   └── kipris/          # 특허 데이터
├── notebooks/           # 분석 Jupyter Notebooks
├── src/
│   ├── collectors/      # 데이터 수집 스크립트
│   ├── preprocessing/   # 전처리 스크립트
│   └── analysis/        # 분석 스크립트
├── visualizations/      # 시각화 결과물
└── README.md
```

## 📝 향후 개선 방향

1. 논문 및 특허 자료의 전체 내용(Full-text) 분석
2. 더 체계적인 프로젝트 기획 및 데이터 수집 전략 수립
3. GitHub API의 심층 분석을 통한 데이터 품질 향상
4. 실시간 트렌드 모니터링 시스템 구축
5. 더 다양한 데이터 소스 통합 (GitLab, Bitbucket 등)

## 📧 문의

프로젝트에 대한 문의사항이나 제안은 이슈를 통해 남겨주세요.

## 📜 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Team TrendBot** | 2025 EDA Project | Addinedu ROS 11th
