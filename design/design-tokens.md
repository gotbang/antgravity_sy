# AntGravity Reference-Aligned Visual Tokens

## 작성시각
2026-03-21 16:32:27 KST

## 토큰 작성 원칙
이 토큰은 현재 구조를 바꾸기 위한 것이 아니다. 기존 화면 구조와 컴포넌트 구조를 유지한 채, 레퍼런스 이미지의 시각 감성만 입히기 위한 토큰이다.

핵심은 아래 네 가지다.
- 짙은 브라운 외곽선
- 아이보리와 크림 중심 배경
- 허니 골드 포인트
- 3D 개미 캐릭터와 어울리는 묵직한 한글 타이포

## Core Color Tokens

```css
:root {
  --canvas-ivory: #F6F1E7;
  --canvas-warm: #EFE4D2;
  --card-cream: #FCF8F1;

  --stroke-brown: #5E3A23;
  --stroke-brown-deep: #3D2416;
  --text-primary: #2F1C12;
  --text-secondary: #6E4C39;
  --text-muted: #8E715C;

  --honey-gold: #F1B640;
  --honey-gold-soft: #FFD56A;
  --honey-gold-deep: #C9831F;

  --leaf-green: #6AA84F;
  --bear-red-brown: #A45B3E;
  --soft-line: #D7C1A1;
}
```

## shadcn/ui 호환 매핑

```css
:root {
  --background: 246 241 231;       /* #F6F1E7 */
  --foreground: 47 28 18;          /* #2F1C12 */

  --card: 252 248 241;             /* #FCF8F1 */
  --card-foreground: 47 28 18;     /* #2F1C12 */

  --popover: 252 248 241;          /* #FCF8F1 */
  --popover-foreground: 47 28 18;  /* #2F1C12 */

  --primary: 241 182 64;           /* #F1B640 */
  --primary-foreground: 47 28 18;  /* #2F1C12 */

  --secondary: 239 228 210;        /* #EFE4D2 */
  --secondary-foreground: 47 28 18;

  --muted: 245 238 226;
  --muted-foreground: 110 76 57;   /* #6E4C39 */

  --accent: 255 213 106;           /* #FFD56A */
  --accent-foreground: 47 28 18;

  --destructive: 164 91 62;        /* #A45B3E */
  --destructive-foreground: 252 248 241;

  --border: 94 58 35;              /* #5E3A23 */
  --input: 94 58 35;               /* #5E3A23 */
  --ring: 241 182 64;              /* #F1B640 */

  --radius: 1.5rem;                /* 구조는 유지하되 시각적으로 더 둥글게 */
}
```

## Border Tokens

```css
:root {
  --border-strong: 3px solid var(--stroke-brown);
  --border-medium: 2px solid var(--stroke-brown);
  --border-soft: 1px solid var(--soft-line);
}
```

| 토큰 | 값 | 용도 |
|------|----|------|
| `--border-strong` | `3px` | 주요 카드, 버튼, 입력창 외곽선 |
| `--border-medium` | `2px` | 말풍선, 내부 프레임 |
| `--border-soft` | `1px` | 약한 구분선 |

## Radius Tokens

```css
:root {
  --radius-card: 24px;
  --radius-pill: 9999px;
  --radius-bubble: 22px;
  --radius-input: 18px;
  --radius-avatar: 9999px;
}
```

현재 구조를 무너뜨리지 않기 위해 반경은 레퍼런스 감성만 가져오되 과도하게 키우지 않는다.

## Shadow Tokens

레퍼런스는 그림자보다 외곽선이 중요하므로 그림자는 절제한다.

```css
:root {
  --shadow-soft: 0 4px 12px rgba(61, 36, 22, 0.10);
  --shadow-card: 0 6px 14px rgba(61, 36, 22, 0.08);
  --shadow-character: 0 8px 18px rgba(61, 36, 22, 0.16);
}
```

## Typography Tokens

```css
:root {
  --font-display: "Pretendard Variable", "Pretendard", "Noto Sans KR", sans-serif;
  --font-body: "Pretendard Variable", "Pretendard", "Noto Sans KR", sans-serif;

  --text-title-xl: 40px;
  --text-title-lg: 32px;
  --text-title-md: 26px;
  --text-body-lg: 20px;
  --text-body-md: 18px;
  --text-body-sm: 16px;
  --text-caption: 14px;
}
```

| 토큰 | 값 | 설명 |
|------|----|------|
| `--text-title-xl` | `40px` | 큰 페이지 타이틀 |
| `--text-title-lg` | `32px` | 카드/섹션 타이틀 |
| `--text-body-md` | `18px` | 본문 기본 |
| `--text-caption` | `14px` | 보조 라벨 |

## Icon and Gauge Tokens

```css
:root {
  --icon-stroke-width: 2.5px;
  --gauge-track: #7B573F;
  --gauge-needle: #4B2D1C;
  --gauge-fill-start: #F7D56C;
  --gauge-fill-end: #E8A72D;
}
```

## Character Tokens

```css
:root {
  --character-shell: #8A5637;
  --character-shell-deep: #5E3825;
  --character-face: #F2C2A7;
  --character-blush: #E9967A;
  --character-accessory: #F1B640;
}
```

| 토큰 | 값 | 용도 |
|------|----|------|
| `--character-shell` | `#8A5637` | 개미 몸통 기본 |
| `--character-face` | `#F2C2A7` | 얼굴/볼 하이라이트 |
| `--character-accessory` | `#F1B640` | 왕관, 헬멧, 버튼 장식 |

## Component Mapping

| 컴포넌트 | 배경 | 보더 | 텍스트 |
|----------|------|------|--------|
| 일반 카드 | `--card-cream` | `--border-strong` | `--text-primary` |
| 강조 카드 | 따뜻한 브라운 계열 | `--border-strong` | 크림 또는 브라운 |
| 버튼 | `--honey-gold` | `--border-strong` | `--text-primary` |
| 입력창 | `--card-cream` | `--border-strong` | `--text-secondary` |
| 말풍선 | `--card-cream` | `--border-medium` | `--text-primary` |
| 구분선 | 투명 | `--border-soft` | - |

## 적용 원칙
- 현재 컴포넌트 수와 배치는 유지한다
- 기존 기능성 클래스는 유지하고, 시각 토큰만 교체한다
- 카드 구조를 데스크톱 대시보드형으로 재배치하지 않는다

## 구현 금지 토큰
- `#EBEBEB` 같은 차가운 회색 보더
- `#FF9900` 같은 형광 주황 메인 컬러
- 지나치게 옅은 회색 텍스트
- 이모지 기반 완성형 캐릭터 표현
