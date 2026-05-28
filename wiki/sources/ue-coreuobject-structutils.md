---
type: source
title: "UE CoreUObject — StructUtils sub-skill"
slug: ue-coreuobject-structutils
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/StructUtils.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Reflection-System]]"
tags: [ue, runtime, foundation, coreuobject]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE CoreUObject — StructUtils sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/StructUtils.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

5.x 동적 USTRUCT 시스템 — FInstancedStruct (단일 USTRUCT 의 동적 wrapper) + FSharedStruct (TSharedRef) + FStructView (non-owning view) + UPropertyBag (런타임 USTRUCT 정의) + UUserDefinedStruct (Editor 의 동적 struct).

## 2. Key claims

- FInstancedStruct: 어느 USTRUCT 자손이든 담을 수 있는 polymorphic wrapper. Editor 의 디테일 패널에서 type 선택.
- FSharedStruct: TSharedRef<USTRUCT> — 다중 객체가 공유 (immutable).
- FStructView: const reference — 소유 없이 USTRUCT 데이터 접근.
- UPropertyBag (5.x): 런타임에 USTRUCT 처럼 동작하는 dynamic key-value 컨테이너.
- UUserDefinedStruct (Editor 만): 디자이너가 C++ 없이 USTRUCT 정의. BP 변수처럼.
- 사용처: Quest 데이터 / Item 데이터 / 다양한 type 의 다중 컴포넌트 / 데이터 기반 게임플레이.

## 3. Quotations

> "FInstancedStruct 가 5.x 의 polymorphic USTRUCT 표준. 다양한 데이터 type 의 컬렉션에서 매우 유용."

## 4. Open questions

- [ ] UPropertyBag vs FInstancedStruct 결정 트리
- [ ] FInstancedStruct 의 BP 노출 함정
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
