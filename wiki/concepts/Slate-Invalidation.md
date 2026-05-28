---
type: concept
title: "Slate Invalidation (Volatile / Cached)"
aliases: [Slate Invalidation, SInvalidationPanel, SRetainerPanel, Invalidation Hotspot]
sources:
  - "[[sources/ue-slatecore-skill]]"
  - "[[sources/ue-umg-skill]]"
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, slate, ui, optimization]
last_updated: 2026-05-09
---

# Slate Invalidation

## 1. 정의 (한 줄)

Slate 위젯의 **재 paint 결정** — Volatile (매 프레임 invalidate, 매번 paint) vs Cached (변경 시만). SInvalidationPanel / SRetainerPanel 로 비싼 위젯 캐싱.

## 2. 자세히

- **Volatile**: 매 프레임 OnPaint 호출. 텍스트 / 이미지 / 변하는 데이터.
- **Cached**: SInvalidationPanel 안에서 자식이 변경 안 될 때 OnPaint skip + 이전 결과 재사용.
- **SRetainerPanel**: 자식을 RenderTarget 으로 캐싱 (GPU 텍스처) — 매우 비싼 sub-tree 의 cache.

Hotspot 카탈로그 ([[raw/ue-wiki-llm/references/06_InvalidationHotspots.md]]):
- RichText: 텍스트 변경 마다 layout 재계산.
- EditableText / EditableTextBox: 입력 시마다 invalidate.
- Throbber / CircularThrobber: 매 프레임 회전 = invalidate.
- ListView / TreeView: 자주 invalidate (item 변경).

## 3. 변형 / 사례 / 응용

- HUD 의 점수 / 체력 = Volatile (매 프레임 변경).
- HUD 의 정적 배경 / 메뉴 = SInvalidationPanel 로 cache.
- 매우 비싼 미니맵 / 인벤토리 그리드 = SRetainerPanel 로 RenderTarget.
- UMG 측: URetainerBox / UInvalidationBox 자손 위젯 — 동일 패턴.

## 4. 관련 entity

- [[entities/SWidget]] · [[entities/UWidget]]

## 5. 열린 질문

- [ ] SRetainerPanel 의 RenderTarget 메모리 비용
- [ ] Invalidation 디버깅 (Slate Trace) 사용
