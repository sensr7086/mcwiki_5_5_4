---
type: source
title: "UE UMG — UUserWidget Invalidation Deep"
slug: ue-umg-invalidationdeep
source_path: raw/ue-wiki-llm/skills/UMG/references/UUserWidget/InvalidationDeep.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/UMG-Super-Call-Convention]]"
tags: [ue, umg, ui, deep]
---

# UE UMG — UUserWidget Invalidation Deep

> Source: [[raw/ue-wiki-llm/skills/UMG/UUserWidget/references/InvalidationDeep.md]]
> (Alternate path: `raw/ue-wiki-llm/skills/UMG/references/UUserWidget/InvalidationDeep.md` — 동일 파일)
> Parent: [[sources/ue-umg-uuserwidget]]

## 1. Summary

[[entities/UUserWidget]] 깊이 자료 — Native* 가상 함수 30+ + 라이프사이클 5 종 (NativeOnInitialized / PreConstruct / Construct / Destruct / Tick) + Super 호출 규약 + 인밸리데이션 갱신 흐름 + NativePaint 함정 + InvalidationBox + **5 핵심 원칙**.

## 2. Key claims

- 라이프사이클 5 단계: NativeOnInitialized → NativePreConstruct → NativeConstruct → NativeTick → NativeDestruct.
- Super 호출 규약: NativeConstruct/NativePreConstruct → Super FIRST, NativeDestruct → Super LAST.
- Native* 가상 함수 30+ 카탈로그 (NativeOnFocusReceived / NativeOnMouseMove / NativeOnKeyDown / etc).
- NativePaint 함정: SCompoundWidget 자손은 자식의 paint 자동, NativeOnPaint override 시 Super 호출 필수.
- InvalidationBox / RetainerBox: 비싼 sub-tree 캐싱 — [[concepts/Slate-Invalidation]] 참조.
- TickFrequency 결정 트리: Disabled (정적) / Auto (자동) / OnRegister / Always.
- 5 핵심 원칙 (raw 본문):
  1. PreConstruct 는 Editor preview + 런타임 양쪽 호출 — 멱등 의무.
  2. Construct 는 런타임 SWidget 트리 생성 후 — 자식 위젯 BindWidget 안전.
  3. Tick 비활성화 표준 (TickFrequency=Disabled), 필요 시만 활성.
  4. Destruct 는 delegate 해제 + 캐싱 해제 — Super LAST.
  5. NativeOnPaint 는 자손이 자식 paint 명시 호출 의무.

## 3. Open questions

- [ ] InvalidationBox 의 자식 변경 감지 정확도
- [ ] RetainerBox 의 RenderTarget 메모리 비용
