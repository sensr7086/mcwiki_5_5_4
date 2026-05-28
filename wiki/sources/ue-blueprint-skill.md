---
type: source
title: "UE 5.7.4 Blueprint Module — Main SKILL"
slug: ue-blueprint-skill
source_path: raw/ue-wiki-llm/skills/Blueprint/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UBlueprint]]"
  - "[[entities/UBlueprintGeneratedClass]]"
  - "[[entities/UEdGraph]]"
related_concepts:
  - "[[concepts/CPP-BP-Boundary]]"
  - "[[concepts/UPROPERTY-Markup]]"
tags: [ue, blueprint]
---

# UE 5.7.4 Blueprint Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Blueprint/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

C++ ↔ BP 경계 + 성능 함정 (VM Thunk, Tick BP) + Cooked Build 동작. [[entities/UBlueprint]] (Editor 만, 그래프 + 메타) + [[entities/UBlueprintGeneratedClass]] (Cooked 에 남음, 클래스 자체) + [[entities/UEdGraph]] (Editor 의 노드 그래프 표현) + UFunction (VM thunk).

## 2. Key claims

- C++ → BP 노출 매크로: UFUNCTION(BlueprintCallable / BlueprintPure / BlueprintImplementableEvent / BlueprintNativeEvent / BlueprintCosmetic / BlueprintAuthorityOnly). UPROPERTY(EditAnywhere/BlueprintReadWrite/...).
- BlueprintImplementableEvent: BP 가 구현, C++은 시그니처만. 호출 시 BP 구현 없으면 NOP.
- BlueprintNativeEvent: C++ 기본 + BP override 가능. `_Implementation` 접미 함수에 본체.
- VM Thunk 비용: BP 호출 = native call 보다 느림 (스택 변환). Tick 안 BP 호출 = 핫스팟. → [[concepts/CPP-BP-Boundary]]
- BlueprintFunctionLibrary (UBlueprintFunctionLibrary 자손) = static 유틸 — BP 와 C++ 모두 호출.
- BP Macro / Interface = 디자이너 협업 표준.
- Cooked 빌드: UBlueprint 는 stripped, UBlueprintGeneratedClass 만 남음. Editor 에서만 그래프 편집 가능.

## 3. Quotations

> "본 sub-skill 은 C++ 코드를 Blueprint 에 어떻게 노출하는지 + BP 의 성능/Cooked-build 함정 정리. BP 자체의 노드 사용법은 디자이너/공식 문서 영역."

## 4. Open questions / next sources

- [ ] Tick BP 의 정확한 VM thunk overhead 측정
- [ ] BlueprintCosmetic / BlueprintAuthorityOnly 의 dedicated server 동작
