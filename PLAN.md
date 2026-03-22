# IMEC 세계 정세 모니터링 대시보드 — 프로젝트 계획서

> 작성일: 2026-03-21
> 목적: 인도-중동-유럽 경제 회랑(IMEC) 관련 경제 데이터 실시간 모니터링
> 운영: 개인 단독 운영 → 추후 외부 접근 가능한 클라우드 배포

---

## 1. 프로젝트 개요

### IMEC란?
**India–Middle East–Europe Economic Corridor**
인도 → UAE → 사우디아라비아(철도) → 요르단 → 이스라엘 → 지중해 → 그리스/이탈리아 → 유럽을 잇는 다층 경제 회랑.

- 컨테이너 해운 + 철도 복합 운송
- 석유 및 수소 파이프라인
- 해저 데이터 케이블
- 전력망 연결

### 전략적 의의
- 중국 일대일로(BRI)의 직접적 대항마
- 미국-인도-이스라엘-아랍 관계 재편의 핵심 축
- 2023년 G20에서 공식 발표, 다만 이스라엘-하마스 전쟁으로 일시 정체

### 대시보드 목적
IMEC 진행에 영향을 미치는 경제 지표 및 세계 정세를 모니터링하여 흐름을 예측하고 변화를 빠르게 포착.
새로고침 기반으로 최신 상태 확인.

---

## 2. 모니터링 대상 국가 및 지역

| 국가/지역 | 역할 | 코드 |
|---|---|---|
| 인도 (India) | 동쪽 기점, 수출 허브 | IN |
| UAE | 환적 허브 (두바이 제벨알리 항구) | AE |
| 사우디아라비아 | 철도 구간, 에너지 공급 | SA |
| 요르단 | 통과 국가 | JO |
| 이스라엘 | 지중해 연결 (하이파 항구) | IL |
| 그리스 | 유럽 진입점 (피레우스 항구) | GR |
| 이탈리아 | 유럽 종착점 | IT |
| EU 전체 | 수요 시장 | EU |

---

## 3. KPI — 모니터링 지표 및 데이터 소스

### 3-1. 해운 & 물류 ★ (IMEC 핵심 물리 지표)

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| 홍해·수에즈 통항량 | UNCTAD 해운 통계 | 주간 | CSV 다운로드 / 웹 스크래핑 |
| 수에즈 운하 통항 현황 | Suez Canal Authority | 주간 | 공식 발표 수집 |
| 제벨알리 TEU 처리량 | DP World 분기 실적 보고서 | 분기 | PDF 파싱 / 수동 입력 |
| 하이파 항구 물동량 | 이스라엘 항만청 | 월간 | 공식 통계 페이지 스크래핑 |
| Baltic Dry Index (BDI) | Yahoo Finance / Investing.com | 일간 | 비공식 API |
| 해운 운임 (FBX) | Freightos Baltic Index | 일간 | 웹 스크래핑 |

### 3-2. 에너지 ★ (IMEC 파이프라인·에너지 축)

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| 브렌트유 가격 | FRED API | 일간 | REST API (무료) |
| WTI 원유 가격 | FRED API | 일간 | REST API (무료) |
| 천연가스 가격 (Henry Hub / TTF) | FRED / EIA API | 일간 | REST API (무료) |
| 사우디 원유 생산량 vs OPEC 쿼터 | EIA API | 월간 | REST API (무료) |
| 인도 원유 수입량 및 수입원 | EIA API | 월간 | REST API (무료) |
| 중동발 에너지 흐름 리포트 | IEA Gas Market Report | 월간 | PDF 수동 파싱 or 요약 입력 |
| 수소 프로젝트 현황 (NEOM, UAE) | 뉴스 수집 + 수동 | 비정기 | 수동 업데이트 |

### 3-3. 무역 & 경제

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| 참여국 GDP 성장률 | World Bank API | 연간/분기 | REST API (무료) |
| 양자 교역액 (인도↔UAE 등) | UN Comtrade | 월간 | REST API (무료, 제한적) |
| 외국인 직접투자 (FDI) | World Bank API | 연간 | REST API (무료) |
| 물류 성과지수 (LPI) | World Bank API | 2년 주기 | REST API (무료) |
| 참여국 환율 (INR/AED/SAR/ILS/EUR) | FRED API / Yahoo Finance | 일간 | REST API |

### 3-4. 금융 & 시장

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| 인도 증시 Nifty 50 | Yahoo Finance | 일간 | 비공식 API |
| 이스라엘 증시 TA-125 | Yahoo Finance | 일간 | 비공식 API |
| 사우디 Tadawul (TASI) | Yahoo Finance | 일간 | 비공식 API |
| 인프라 채권 발행 동향 | Bloomberg (유료) | 실시간 | ⚠️ Phase 후기 고려 |

### 3-5. 디지털 인프라

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| 해저 케이블 용량·트래픽 | TeleGeography | 연간 | 무료 요약 공개 데이터 활용 |
| 해저 케이블 지도 | TeleGeography SubmarineCableMap | 정적 | 이미지/데이터 임베드 |

### 3-6. 지정학적 리스크

| 지표 | 소스 | 갱신 주기 | 접근 방식 |
|---|---|---|---|
| GDELT 이벤트 지수 | GDELT Project | 일간 | CSV / BigQuery (무료) |
| 이스라엘 관련 갈등 이벤트 | GDELT Project | 일간 | 필터링 쿼리 |
| 미중 관계 / BRI vs IMEC | GDELT + 뉴스 | 일간 | 키워드 기반 |
| 정치 안정성 지수 | World Bank Governance | 연간 | REST API (무료) |

### 3-7. 뉴스 모니터링

| 키워드 그룹 | 키워드 예시 |
|---|---|
| IMEC 직접 | "IMEC", "India Middle East Europe Corridor" |
| 경쟁 구도 | "Belt and Road", "BRI", "일대일로" |
| 중동 정세 | "Israel", "Hamas", "Saudi normalization", "Abraham Accords" |
| 인프라 | "Haifa port", "Jebel Ali", "NEOM", "Suez" |
| 에너지 | "Saudi Aramco", "hydrogen pipeline", "UAE energy" |

뉴스 소스: **NewsAPI** (무료 100req/일), **GDELT News** (무료)

---

## 4. 데이터 소스 접근성 분류

### ✅ 무료 API (자동 수집 가능)
| 소스 | 제공 데이터 | 제한 |
|---|---|---|
| World Bank Open Data | GDP, FDI, LPI, 교역량 | 없음 |
| IMF Data API | 경제 전망, 거시 지표 | 없음 |
| FRED API | 유가, 환율, 가스 가격 | 없음 (키 필요) |
| EIA API | 원유/가스 생산·수입 | 없음 (키 필요) |
| GDELT Project | 지정학적 이벤트 | 없음 |
| Yahoo Finance (비공식) | 주가, 환율, BDI | 비공식, 불안정 가능 |
| UN Comtrade | 양자 무역 | 100req/시간 |
| NewsAPI | 뉴스 헤드라인 | 100req/일 (무료) |

### ⚠️ 수동/반자동 수집 필요
| 소스 | 제공 데이터 | 방식 |
|---|---|---|
| UNCTAD | 홍해·수에즈 통항량 | CSV 다운로드 → DB 입력 |
| DP World 실적 보고서 | 제벨알리 TEU | 분기 PDF 파싱 |
| 이스라엘 항만청 | 하이파 물동량 | 월간 웹 스크래핑 |
| IEA Gas Market Report | 중동 에너지 흐름 | 월간 PDF 수동 요약 |
| TeleGeography | 케이블 용량·트래픽 | 연간 공개 데이터 활용 |

### 🚫 유료 (Phase 후기 또는 제외)
| 소스 | 제공 데이터 | 비고 |
|---|---|---|
| Bloomberg Terminal | 인프라 채권 발행 | 고가 구독, 추후 고려 |
| Planet Labs / Maxar | 위성 현장 이미지 | 고가, 추후 고려 |

---

## 5. 대시보드 구조 (화면 구성)

```
┌──────────────────────────────────────────────────────────┐
│  🌐 IMEC Monitor          [마지막 갱신: 2026-03-21 14:30]  │
│                                    [🔄 새로고침]           │
├───────────┬──────────────────────────────────────────────┤
│           │  [개요] [해운] [에너지] [무역·경제] [지정학] [뉴스] │
│ IMEC 경로 ├──────────────────────────────────────────────┤
│ 인터랙티브 │                                               │
│   지도    │  선택된 탭의 차트·지표·테이블 표시              │
│           │                                               │
└───────────┴──────────────────────────────────────────────┘
```

### 탭별 구성

#### [개요] — Overview
- IMEC 경로 인터랙티브 지도 (참여국 하이라이트, 항구/노드 마커)
- 주요 KPI 카드 (8개): 유가, BDI, 수에즈 통항량, INR/USD, 이스라엘 리스크 지수 등
- 갱신 시각 표시 + 수동 새로고침 버튼

#### [해운 & 물류] — Shipping
- 홍해·수에즈 통항량 주간 추이 차트
- 제벨알리 TEU 분기 처리량 바 차트
- 하이파 항구 월간 물동량
- BDI / FBX 해운 운임 시계열

#### [에너지] — Energy
- 브렌트유 / WTI / 천연가스 가격 시계열
- 사우디 원유 생산량 vs OPEC 쿼터
- 인도 원유 수입원 파이 차트
- IEA 중동 에너지 흐름 요약 (수동 입력 패널)

#### [무역 & 경제] — Trade
- 참여국 GDP 성장률 비교 (바 차트)
- 양자 교역액 히트맵 (국가 × 국가)
- 참여국 환율 변동 테이블
- FDI 흐름 차트

#### [지정학] — Geopolitics
- GDELT 이벤트 빈도 히트맵 (국가 × 월)
- 갈등 vs 협력 이벤트 비율 추이
- 참여국 증시 비교 (Nifty50 / TA-125 / Tadawul)
- TeleGeography 해저 케이블 맵 임베드

#### [뉴스] — News Feed
- 키워드 그룹별 최신 뉴스 목록
- 감성 분석 점수 (긍정/부정/중립)
- 키워드 빈도 워드 클라우드

---

## 6. 기술 스택

### 확정: Python + Streamlit 단일 스택

```
Python
├── streamlit          # 대시보드 UI
├── pandas             # 데이터 처리
├── plotly             # 인터랙티브 차트
├── folium             # 지도 (IMEC 경로)
├── requests           # API 호출
├── apscheduler        # 백그라운드 갱신 스케줄러
├── sqlite3 (내장)     # 로컬 데이터 캐시
├── beautifulsoup4     # 웹 스크래핑 (항만 데이터 등)
└── vaderSentiment     # 뉴스 감성 분석
```

**선택 이유:**
- `streamlit run app.py` 한 줄로 실행
- 차트, 지도, 테이블 모두 Python에서 처리
- SQLite 캐시로 API 무료 한도 보존

### 배포 전략
| 단계 | 환경 | 방법 |
|---|---|---|
| 개발/테스트 | 로컬 PC | `streamlit run app.py` |
| 외부 공개 배포 | 클라우드 | Streamlit Community Cloud (무료) 또는 Railway/Render |
| 데이터 갱신 | 클라우드 | APScheduler + SQLite 또는 GitHub Actions |

---

## 7. 구현 단계

### Phase 1 — 기반 구축
- [ ] 프로젝트 폴더 구조 생성
- [ ] API 키 발급: FRED, EIA, NewsAPI
- [ ] SQLite 캐시 스키마 설계 (지표별 테이블)
- [ ] 무료 API 수집 모듈 작성 (World Bank, FRED, EIA)
- [ ] 기본 Streamlit 앱 골격 + 새로고침 버튼

### Phase 2 — 해운 & 에너지 탭 (핵심)
- [ ] UNCTAD / 수에즈 통항량 수집 (CSV 파싱)
- [ ] DP World / 하이파 항만 데이터 수집 모듈
- [ ] BDI 시계열 차트
- [ ] 유가 / 가스 가격 차트
- [ ] EIA 원유 생산·수입 데이터 시각화
- [ ] IMEC 경로 지도 (Folium)

### Phase 3 — 무역 & 경제 탭
- [ ] GDP 비교 차트 (World Bank)
- [ ] 양자 교역액 히트맵 (UN Comtrade)
- [ ] 환율 테이블 (FRED)
- [ ] 참여국 증시 차트 (Yahoo Finance)

### Phase 4 — 지정학 & 뉴스 탭
- [ ] GDELT 이벤트 파이프라인
- [ ] NewsAPI 뉴스 피드 + 감성 분석
- [ ] TeleGeography 케이블 맵 임베드
- [ ] 리스크 스코어 계산 로직

### Phase 5 — 자동화 & 클라우드 배포
- [ ] APScheduler 갱신 주기 설정 (지표별 상이)
- [ ] API 오류 처리 및 폴백 (캐시 사용)
- [ ] Streamlit Community Cloud 배포
- [ ] 수동 입력 패널 (IEA 리포트, DP World 등)

---

## 8. 폴더 구조

```
imec-dashboard/
├── PLAN.md
├── app.py                     ← Streamlit 메인 앱
├── config.py                  ← API 키, 설정값 (.env 연동)
├── .env                       ← API 키 보관 (git 제외)
├── requirements.txt
├── data/
│   ├── cache.db               ← SQLite 캐시
│   └── static/                ← 수동 입력 데이터 (IEA, DP World 등)
├── collectors/
│   ├── worldbank.py           ← World Bank API
│   ├── fred.py                ← FRED API (유가, 환율)
│   ├── eia.py                 ← EIA API (에너지)
│   ├── comtrade.py            ← UN Comtrade
│   ├── gdelt.py               ← GDELT 이벤트
│   ├── finance.py             ← Yahoo Finance (주가, BDI)
│   ├── news.py                ← NewsAPI
│   └── scraper.py             ← UNCTAD, 하이파 항만청 스크래핑
├── pages/
│   ├── overview.py            ← 개요 탭
│   ├── shipping.py            ← 해운·물류 탭
│   ├── energy.py              ← 에너지 탭
│   ├── trade.py               ← 무역·경제 탭
│   ├── geopolitics.py         ← 지정학 탭
│   └── news_feed.py           ← 뉴스 탭
└── scheduler.py               ← 자동 갱신 스케줄러
```

---

## 9. API 키 발급 체크리스트

구현 시작 전 아래 키를 발급해야 합니다:

- [ ] **FRED API Key** — https://fred.stlouisfed.org/docs/api/api_key.html (무료)
- [ ] **EIA API Key** — https://www.eia.gov/opendata/ (무료)
- [ ] **NewsAPI Key** — https://newsapi.org/ (무료, 100req/일)
- [ ] **UN Comtrade** — https://comtradeplus.un.org/ (무료 계정)

---

## 10. 제한사항 및 리스크

| 항목 | 내용 | 대응 방안 |
|---|---|---|
| API 무료 한도 | NewsAPI 100req/일 | SQLite 캐싱으로 재요청 최소화 |
| DP World / 항만 데이터 | 공식 API 없음, 분기 보고서 | PDF 파싱 + 수동 입력 패널 |
| IEA 리포트 | PDF 형식, 구조화 어려움 | 수동 요약 입력 UI 제공 |
| GDELT 노이즈 | 데이터 방대, 관련성 낮은 이벤트 포함 | 국가코드 + 키워드 이중 필터 |
| Yahoo Finance 비공식 | 라이브러리 불안정 가능 | yfinance 라이브러리 + 폴백 처리 |
| 이스라엘-하마스 전쟁 | IMEC 이스라엘 구간 현실적 정체 | 상황 모니터링 자체가 목적 |
| TeleGeography 유료 | 상세 케이블 데이터 유료 | 공개 케이블 맵 이미지/요약만 활용 |
| Bloomberg 유료 | 채권 발행 실시간 데이터 | 초기 제외, 후기에 고려 |

---

## 11. 다음 단계 (계획 확정 후)

1. **API 키 발급** (FRED, EIA, NewsAPI, UN Comtrade)
2. **Phase 1 시작**: 폴더 구조 + SQLite 캐시 + 기본 수집 모듈
3. **Phase 2 우선**: 해운·물류 탭 (IMEC 핵심 물리 지표)

---

*기술 스택: Python + Streamlit | 배포: Streamlit Community Cloud*
*알림: 대시보드 내 수동 새로고침 기반*
*이 문서는 구현 시작 전 계획 단계입니다.*
