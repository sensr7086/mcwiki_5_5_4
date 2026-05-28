---
type: entity
title: "UObject"
aliases: [UObject, UObjectBase, UObjectBaseUtility]
kind: model
sources:
  - "[[sources/ue-coreuobject-skill]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UObject

## 요약

UE 의 모든 GC-관리 객체의 베이스. `Engine/Source/Runtime/CoreUObject/` 에 정의. UCLASS 매크로로 표시된 모든 클래스의 부모. Reflection ([[entities/UClass]] + [[entities/FProperty]]) + GC + Serialization + Network 의 진입점.

## 관계

- 자손: [[entities/AActor]] (게임플레이) · [[entities/UActorComponent]] (컴포넌트) · [[entities/UMaterial]] / [[entities/UTexture]] / [[entities/UStaticMesh]] (자산) · [[entities/UAnimInstance]] (런타임 BP)
- 메타 클래스: [[entities/UClass]] (UObject 의 reflection 정보)
- 핸들 4종: `TObjectPtr<>` / `TWeakObjectPtr<>` / `TStrongObjectPtr<>` / `TSoftObjectPtr<>`

## 핵심 주장

- Outer 체인이 ownership 을 결정. NewObject 의 첫 인자가 Outer. [[sources/ue-coreuobject-skill]]
- GC 는 reachability 기반 (UPROPERTY 로 표시된 멤버 + 루트 셋). [[concepts/Garbage-Collection]]
- `StaticClass()` 가 [[entities/UClass]] 반환 → reflection 기반 NewObject / Cast / Property 접근. [[concepts/Reflection-System]]
- Lifetime 4 단계: Construct → PostInitProperties → PostLoad (디스크 로드 시) → BeginDestroy → FinishDestroy. [[concepts/Object-Lifecycle]]
- 멤버 직렬화는 `UPROPERTY` 표시된 것만 자동. 그 외는 `Serialize()` override. [[raw/ue-wiki-llm/skills/CoreUObject/SKILL.md#§1]]

## 열린 질문

- [ ] PostInitProperties vs PostLoad vs PostInitializeComponents 의 호출 순서 (Editor vs Cooked)
- [ ] `UObject::AddToRoot()` / `RemoveFromRoot()` 사용 시점
