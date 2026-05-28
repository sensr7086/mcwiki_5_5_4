---
type: entity
title: "UBlueprint / UBlueprintGeneratedClass / UEdGraph"
aliases: [UBlueprint, UBlueprintGeneratedClass, UEdGraph, UFunction]
kind: model
sources:
  - "[[sources/ue-blueprint-skill]]"
tags: [ue, blueprint, editor]
last_updated: 2026-05-09
---

# UBlueprint / UBlueprintGeneratedClass

## 요약

UBlueprint = Editor 만의 자산 (그래프 + 메타). UBlueprintGeneratedClass = Cooked 빌드에도 남음 (실제 클래스). UEdGraph = Editor 의 노드 그래프 표현. UFunction = VM thunk + native 호출 wrapper.

## 관계

- 부모: [[entities/UObject]]
- 페어: UEdGraph (Editor 만), UBlueprintGeneratedClass (Cooked 에 남음)
- 협력: 모든 UFUNCTION / UPROPERTY 가 본 클래스의 reflection 데이터에 등록

## 핵심 주장

- Editor 분리: UBlueprint 는 `WITH_EDITORONLY_DATA` 로 stripped — Cooked 빌드에 안 남음. UBlueprintGeneratedClass 만 남음 → BP 의 native 클래스 처럼 동작.
- UEdGraph: Editor 의 노드 그래프 (Event Graph / Construction Script / Function Graphs / Macro Graphs). UEdGraphNode 자손 들의 컬렉션.
- UFunction VM Thunk: BP 함수 호출 = UFunction::Invoke → ProcessEvent → VM bytecode interpret. Native 함수보다 느림.
- BlueprintCompilerContext: Editor 가 BP → bytecode 컴파일.
- BlueprintFunctionLibrary 자손: static UFUNCTION 만 — BP 와 C++ 양쪽 호출 가능.

## 열린 질문

- [ ] Tick BP 의 정확한 VM thunk overhead 측정
- [ ] BP nativization (5.x deprecated) 의 대안
