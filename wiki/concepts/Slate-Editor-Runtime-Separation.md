---
type: concept
title: "Slate 런타임/에디터 분리 원칙"
aliases: [Slate Editor Separation, Slate 4단 방어]
sources:
  - "[[sources/ue-slate-skill]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, slate, build, policy]
last_updated: 2026-05-09
---

# Slate 런타임/에디터 분리 원칙

## 1. 정의 (한 줄)

Slate 모듈 안에 게임 위젯과 에디터 도구가 공존하므로, 인하우스 툴 위젯 (Docking / Menu / Commands / GraphEditor) 은 Editor 모듈에만 두고 Runtime 게임 모듈은 의존 X — 4 단 방어.

## 2. 자세히

Slate 모듈의 두 영역:
- **A. 게임+에디터 공통**: SButton / STextBlock / SListView / SBorder / 기본 위젯들. Runtime 모듈에서 사용 OK.
- **B. 인하우스 툴 🛠**: SDockTab / [[entities/FTabManager]] / [[entities/FUICommandList]] / FMenuBuilder / SGraphEditor. **Editor 빌드만**.

[[concepts/Editor-Only-4-Tier-Separation]] 의 Slate 특화 적용. 게임 모듈에서 SDockTab 사용 시 Cooked 빌드 실패.

## 3. 변형 / 사례 / 응용

- 게임 HUD / 메뉴 = SButton / STextBlock / SImage 등 공통 위젯만.
- 에디터 도구 (커스텀 에셋 에디터) = SDockTab / FTabManager / FUICommandList — Editor 모듈.
- 5.x 권장: 게임 UI 는 [[entities/UWidget]] / [[entities/UUserWidget]] (UMG) — 에디터 의존 자동 회피.

## 4. 관련 entity

- [[entities/SWidget]], [[entities/FSlateApplication]] (공통)
- [[entities/FTabManager]], [[entities/FUICommandList]] (Editor 만)

## 5. 열린 질문

- [ ] Slate 의 일부 게임 + 에디터 양쪽 사용 위젯 (SListView 등) 의 의존 관리
