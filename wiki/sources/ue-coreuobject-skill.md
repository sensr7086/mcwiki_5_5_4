---
type: source
title: "UE 5.7.4 CoreUObject Module — Main SKILL"
slug: ue-coreuobject-skill
source_path: raw/ue-wiki-llm/skills/CoreUObject/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
  - "[[entities/UClass]]"
  - "[[entities/FProperty]]"
  - "[[entities/UPackage]]"
  - "[[entities/UInterface]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/UPROPERTY-Markup]]"
  - "[[concepts/Object-Handles]]"
  - "[[concepts/Object-Lifecycle]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE 5.7.4 CoreUObject Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/SKILL.md]]

## 1. Summary

`Core` 위에 **객체 시스템 + 리플렉션 + GC + 직렬화 + 패키지 로딩** 을 얹는 L2 모듈. 거의 모든 게임플레이/엔진/에디터 모듈이 이 위에 쌓인다. 13 개 sub-skill 로 분할.

## 2. Key claims

- 베이스 의존: Public Core/TraceLog/CorePreciseFP, Private AutoRTFM/Projects/Json (+ DerivedDataCache 에디터/서버).
- `bMinimizeGeneratedIncludes = true` — `*.generated.h` include 최소화 → 내부 순환 의존 회피.
- `UnsafeTypeCastWarningLevel = Error` — 위험한 cast 는 컴파일 에러.
- 객체 핸들 4종 — `TObjectPtr<>` (UPROPERTY 표준), `TWeakObjectPtr<>`, `TStrongObjectPtr<>`, `TSoftObjectPtr<>`. → [[entities/UObject]] · [[concepts/Object-Handles]]
- 객체 생성: `NewObject<T>(Outer, Class, Name)`, `LoadObject<T>(nullptr, Path)`, `FindObject<T>(World, Name)`. → [[concepts/Object-Lifecycle]]
- `CollectGarbage(RF_NoFlags, bPerformFullPurge)` — GC 진입점. → [[concepts/Garbage-Collection]]

## 3. Sub-skills (13 — Phase 4A 완료)

- [[sources/ue-coreuobject-uobject]] — UObject 베이스 라이프사이클 + Super 호출 + ProcessEvent
- [[sources/ue-coreuobject-reflection]] — UCLASS/UPROPERTY 매크로 + UHT generated.h
- [[sources/ue-coreuobject-property]] — FProperty 5.x + CastField + TFieldIterator
- [[sources/ue-coreuobject-package]] — UPackage / Mount Point / GetTransientPackage
- [[sources/ue-coreuobject-interface]] — UINTERFACE + IInterface + Execute_* 매크로
- [[sources/ue-coreuobject-gc]] — CollectGarbage / FGCObject / FReferenceChainSearch
- [[sources/ue-coreuobject-serialization]] — FArchive / Serialize override / Custom Version
- [[sources/ue-coreuobject-network]] — RPC + DOREPLIFETIME + RepNotify + NetSerialize
- [[sources/ue-coreuobject-editor]] 🛠 — PostEditChangeProperty + Modify + IsDataValid
- [[sources/ue-coreuobject-cooking]] 🛠 — NeedsLoadForServer/Client + BeginCacheForCookedPlatformData
- [[sources/ue-coreuobject-structutils]] — FInstancedStruct + UPropertyBag (5.x)
- [[sources/ue-coreuobject-objecthandles]] — TObjectPtr / TWeakObjectPtr / TSoftObjectPtr / Lazy Load
- [[sources/ue-coreuobject-deprecateduproperty]] — UProperty → FProperty 마이그레이션

## 4. Open questions

- [ ] `UPROPERTY` markup 의 모든 specifier 카탈로그 (BlueprintReadWrite/Replicated/Transient 등)
- [ ] 5.x ObjectHandles (lazy load) 의 `TObjectPtr<>` 동작 차이 — Editor vs Cooked
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
