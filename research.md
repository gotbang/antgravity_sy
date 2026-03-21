# AntGravity - 개미 생존기 분석 보고서

## 1. 프로젝트 개요

**프로젝트명**: AntGravity - 스마트한 개미들의 나침반
**컨셉**: 주식 투자를 개미의 시선에서 게임화한 모바일 웹 앱

---

## 2. 앱 구조

### 2.1 진입 화면 (Lobby)
3가지 투자 모드 선택:
| 모드 | 아이콘 | 상태 | 설명 |
|------|--------|------|------|
| 튼튼한 개미굴 청약 | 🏰 | 공사중 | 부동산 투자 |
| 아슬아슬 나뭇가지 타기 | 🍃 | 활성(HOT) | 주식 투자 (메인) |
| 벼락 맞은 각설탕 줍기 | 🧊 | 겨울잠 | 코인 투자 |

### 2.2 주식 앱 화면 (메인)
하단 네비게이션으로 3개 탭 전환:
1. **여왕의 지시** (`tab-today`): 오늘의 시장 판단
2. **먹이 탐색** (`tab-analysis`): 종목 분석
3. **생존 일지** (`tab-diary`): 감정 일기

---

## 3. 캐릭터 시스템

| 캐릭터 | 아이콘 | 역할 |
|--------|--------|------|
| 병정개미 | 💂 | 시장 리스크 경보 발령 |
| 여왕개미 | 👑 | AI 페로몬 분석 결과 전달 |
| 정찰개미 | 🧐 | 종목 분석 정보 제공 |

---

## 4. UI/UX 디자인 시스템

### 4.1 색상 팔레트
```css
:root {
  /* 배경색 */
  --bg-cream: #FFF8E7;      /* 배경색 (크림색) */
  --card-bg: #FFFFFF;       /* 카드 배경 */

  /* 텍스트 색상 */
  --text-primary: #333333;   /* 주요 텍스트 */
  --text-secondary: #666666; /* 보조 텍스트 */
  --text-auxiliary: #999999; /* 부가 텍스트 */

  /* 기능색 */
  --color-primary: #FF9900;  /* 주황 강조 */
  --color-success: #4CAF50;  /* 녹색 긍정 */
  --color-negative: #FF5252; /* 빨강 부정 */
}
```

### 4.2 폰트
- **Jua**: 귀여운 타이틀용 (`.font-cute`)
- **Nanum Pen Script**: 일기장 손글씨 (`.font-diary`)
- **Noto Sans KR**: 본문 텍스트

### 4.3 주요 애니메이션
```css
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

@keyframes bounce-subtle {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-3px) scale(1.02); }
}
```

### 4.4 카드 스타일
```css
.character-card {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0px 4px rgba(0,0,0,0.1);
}
```

### 4.5 버튼 스타일
```css
/* 주요 버튼 */
.btn-primary {
  background-color: #FF9900;
  color: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0px 2px rgba(0,0,0,0.05);
}

/* 보조 버튼 */
.btn-secondary {
  background-color: #FFFFFF;
  color: #FF9900;
  border: 2px solid #FF9900;
  border-radius: 8px;
}
```

---

## 5. 화면 전환 로직

### 5.1 홈 ↔ 앱 전환
```javascript
// 앱 진입
function enterStockApp() {
  container.classList.add('app-active');
}

// 홈 복귀
function goBackToHome() {
  container.classList.remove('app-active');
}
```

### 5.2 CSS 트랜지션
```css
#screen-home { transform: translateX(0); opacity: 1; }
#screen-stock { transform: translateX(100%); opacity: 0; }

.app-active #screen-home {
  transform: translateX(-30%) scale(0.95);
  opacity: 0;
}
.app-active #screen-stock {
  transform: translateX(0);
  opacity: 1;
}
```

---

## 6. 탭 전환 시스템

```javascript
function switchTab(tabId, index) {
  // 1. 모든 탭 비활성화
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });

  // 2. 선택 탭 활성화
  document.getElementById('tab-' + tabId).classList.add('active');

  // 3. 인디케이터 이동
  indicator.style.transform = `translateX(${index * 106}%)`;

  // 4. 아이콘/텍스트 스타일 변경
  // grayscale, opacity 조절
}
```

---

## 7. 토스트 알림

```javascript
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.innerText = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}
```

---

## 8. 탭별 상세 분석

### 8.1 Tab 1: 오늘 판단
- **병정개미 말풍선**: 시장 리스크 점수 (68/100)
- **여왕개미 말풍선**: AI 페로몬 분석
  - 먹이 발견 (상승): 25%
  - 대열 유지 (보합): 60%
  - 천적 출현 (하락): 15%

### 8.2 Tab 2: 종목 분석
- 검색 입력창
- 종목 카드 (예: 사과나무/AAPL)
  - 현재 가격 표시
  - 안전 활동 반경 슬라이더
  - 거인의 발자국 (상승풍)
  - 맞바람 강도 (하락풍)

### 8.3 Tab 3: 감정 일기
- 기분 선택 (🍯달달해, 🕸️거미줄, 💧물방울, 💤동면)
- 일기 작성 영역 (diary-bg 줄무늬)
- 과거 일기 목록

---

## 9. 외부 의존성

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Jua&family=Nanum+Pen+Script&family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
```

---

## 10. 재현 체크리스트

- [ ] HTML 구조 (mobile-container > screen-home, screen-stock)
- [ ] CSS 변수 및 애니메이션 정의
- [ ] 진입 화면 3개 모드 카드
- [ ] 주식 앱 Header 컴포넌트
- [ ] Tab 1: 오늘 판단 (말풍선 2개)
- [ ] Tab 2: 종목 분석 (검색, 카드, 슬라이더)
- [ ] Tab 3: 감정 일기 (기분 선택, textarea, 목록)
- [ ] Bottom Navigation (인디케이터 포함)
- [ ] JavaScript: enterStockApp, goBackToHome
- [ ] JavaScript: switchTab, showToast

---

## 11. 실데이터 연동 운영 메모

### 최신 기준 용어
- `시장 데이터만 실데이터`
- `Supabase 원본`
- `파일 캐시 비추적 산출물`
- `미국장 마감 후 하루 1회`

### 현재 구현/계획 반영 사항
- 시장 심리, AI 분석 카드, 트렌딩 종목, 종목 검색/상세는 실데이터 연결 대상으로 본다.
- 개미 광장은 1차에 실데이터 범위에 포함하지 않는다.
- 생존 일지는 서버 저장 없이 `localStorage` 유지 원칙을 따른다.

### 데이터 소스 메모
- 한국 공시/재무: `Dartlab/OpenDART`
- 한국 가격/거래대금/시가총액: `PyKRX`
- 미국 전체 종목 유니버스: `SEC EDGAR`
- 미국 가격/기초지표: `yfinance`

### 캐시/적재 메모
- 읽기 우선순위는 `in-memory -> Supabase -> 부분 폴백`
- 가격 데이터만 온디맨드 보충 허용
- 재무/공시/AI 집계는 배치 적재본 우선
- 파일 캐시는 런타임 산출물이며 git 추적 대상이 아니다
