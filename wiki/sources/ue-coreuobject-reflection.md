---
type: source
title: "UE CoreUObject — Reflection sub-skill"
slug: ue-coreuobject-reflection
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Reflection.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UClass]]"
  - "[[entities/FProperty]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/UPROPERTY-Markup]]"
tags: [ue, runtime, foundation, coreuobject, reflection]
---

# UE CoreUObject — Reflection sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Reflection.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

UCLASS / UPROPERTY / UFUNCTION / UENUM / USTRUCT 매크로 + UnrealHeaderTool (UHT) generated.h. [[entities/UClass]] / UEnum / UScriptStruct 메타 클래스. 메타데이터 키 + UObjectIterator / TObjectIterator (회피 권장 — [[concepts/Global-Iterator-Avoidance]]).

## 2. Key claims

- UHT (UnrealHeaderTool) C# 도구 — `*.generated.h` 자동 생성 → reflection 메타 빌드.
- UCLASS / UPROPERTY / UFUNCTION / UENUM / USTRUCT 5 매크로 — UHT 가 인식.
- UClass / UEnum / UScriptStruct — 각각 클래스/열거형/구조체의 메타 클래스. UStruct 베이스.
- 메타데이터 키 (UE 표준): Category / DisplayName / ToolTip / EditAnywhere / BlueprintReadWrite / ClampMin / ClampMax / Tags / etc.
- UObjectIterator / TObjectIterator: 모든 UObject 순회. 사용 금지 ([[concepts/Global-Iterator-Avoidance]]) — 등록 패턴 우선.
- CastField<FObjectProperty>(Property) — FProperty 자손으로 cast. → [[entities/FProperty]]

## 3. Quotations

> "UHT 가 generated.h 를 자동 생성 → reflection 메타 빌드 → 런타임 동적 멤버 접근."

## 4. Open questions

- [ ] UHT 의 incremental 갱신 (변경된 파일만)
- [ ] 5.x ObjectHandles + Reflection 통합
