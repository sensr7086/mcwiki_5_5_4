---
type: entity
title: "UClass"
aliases: [UClass, UStruct, UScriptStruct, UEnum]
kind: model
sources:
  - "[[sources/ue-coreuobject-skill]]"
tags: [ue, runtime, reflection]
last_updated: 2026-05-09
---

# UClass

## 요약

[[entities/UObject]] 의 reflection 정보를 담는 메타 클래스. `Class->StaticClass()` 가 본 객체. UPROPERTY / UFUNCTION 메타 + virtual table + 부모 chain + interface 목록.

## 관계

- 베이스: UStruct → UField → UObject
- 형제: UScriptStruct (USTRUCT 매크로) · UEnum (UENUM)
- Property 목록: [[entities/FProperty]] linked list
- Function 목록: UFunction linked list

## 핵심 주장

- `NewObject<T>(Outer, T::StaticClass())` 가 표준 — UClass 가 메모리 레이아웃 + 생성자 호출. [[sources/ue-coreuobject-skill]]
- `Cast<T>(Obj)` 는 UClass 의 IsChildOf 체크로 동작. CDO (Class Default Object) 비교 X — 단순 type id 체크. [[concepts/Reflection-System]]
- CDO = UClass 가 들고 있는 *전형* 인스턴스. `GetMutableDefault<T>()` 로 접근 가능하지만 **수정 금지** (Article 1 Compile Tier 위반). [[raw/ue-wiki-llm/references/16_PolicyPriority.md]]
- 5.x ObjectHandles + `TObjectPtr<>` 는 UClass 의 lazy load 지원. Editor 에서는 lazy resolve, Cooked 에서는 raw pointer. [[concepts/Object-Handles]]

## 열린 질문

- [ ] UClass 와 USTRUCT (UScriptStruct) 의 차이 — 언제 어느 쪽
- [ ] UClass 의 reflection 정보가 어떻게 빌드되는가 (UnrealHeaderTool generated.h)
