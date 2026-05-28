---
type: entity
title: "UBlueprintGeneratedClass"
aliases: [UBlueprintGeneratedClass, BPGC, BP Class]
kind: model
sources:
  - "[[sources/ue-blueprint-skill]]"
tags: [ue, blueprint]
last_updated: 2026-05-09
---

# UBlueprintGeneratedClass

## 요약

[[entities/UClass]] 자손. **BP 의 컴파일 결과 클래스 — Cooked 빌드에 남음**. [[entities/UBlueprint]] 가 Editor 만 의 자산이라면, UBlueprintGeneratedClass 가 그것의 native 클래스 표현. 게임 코드는 BPGC 의 인스턴스를 native 처럼 사용.

## 관계

- 부모: [[entities/UClass]]
- 페어: [[entities/UBlueprint]] (Editor 만의 그래프 + 메타)
- 호스트: 컴파일된 BP 의 모든 인스턴스

## 핵심 주장

- Editor 의 BP 컴파일러가 [[entities/UBlueprint]] (그래프) → UBlueprintGeneratedClass (실행 클래스) 변환.
- Cooked 빌드: UBlueprint 는 stripped, BPGC 만 남음 — 게임 코드에서 native 클래스 처럼 동작.
- BP 변수 = UPROPERTY 로 BPGC 에 등록. BP 함수 = UFunction (VM thunk).
- UClass 의 메타 (CDO / Property linked list) 가 BPGC 에도 존재.
- TSubclassOf<MyClass> 에 BP 자손 cast 가능 — 런타임 type id 체크.

## 열린 질문

- [ ] BP nativization (5.x deprecated) 의 BPGC 영향
- [ ] BPGC 의 reflection vs native UClass 의 차이
