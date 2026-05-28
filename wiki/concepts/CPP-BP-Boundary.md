---
type: concept
title: "C++ ↔ Blueprint 경계 + VM Thunk"
aliases: [VM Thunk, BP Boundary, BlueprintCallable, BlueprintImplementableEvent]
sources:
  - "[[sources/ue-blueprint-skill]]"
related_concepts:
  - "[[concepts/UPROPERTY-Markup]]"
  - "[[concepts/Reflection-System]]"
tags: [ue, blueprint]
last_updated: 2026-05-09
---

# C++ ↔ Blueprint 경계

## 1. 정의 (한 줄)

UFUNCTION 매크로로 C++ 함수를 BP 에 노출 (BP → C++) + BlueprintImplementableEvent / NativeEvent 로 BP 가 C++ 호출 (C++ → BP). VM Thunk 비용 고려.

## 2. 자세히

| 매크로 | 방향 | 설명 |
| -- | -- | -- |
| BlueprintCallable | BP → C++ | BP 가 C++ 함수 호출. C++ 본체. |
| BlueprintPure | BP → C++ | const + 부작용 없음 — 노드에 실행 핀 없음. |
| BlueprintImplementableEvent | C++ → BP | BP 가 구현. C++ 호출 시 BP 구현 없으면 NOP. |
| BlueprintNativeEvent | 양방향 | C++ 기본 + BP override. _Implementation 접미. |
| BlueprintCosmetic | BP → C++ | 서버에서 호출 안 됨. dedicated server 최적화. |
| BlueprintAuthorityOnly | BP → C++ | Authority 만. 클라 호출 = NOP. |

## 3. 변형 / 사례 / 응용

- VM Thunk 비용: BP 호출 = native call 보다 ~10-100x 느림 (ProcessEvent 스택 변환). Tick 안 BP 호출 = 핫스팟.
- BlueprintFunctionLibrary: static UFUNCTION 만. BP + C++ 양쪽.
- BP Macro / Interface: 디자이너 협업.
- Cooked: UBlueprint stripped, UBlueprintGeneratedClass 만 남음. Editor 에서만 그래프 편집.
- 함정: TArray<float> 값 전달 — 매 호출 복사. TArray<UObject*> = pointer 배열 (안전).

## 4. 관련 entity

- [[entities/UBlueprint]] / [[entities/UBlueprintGeneratedClass]]

## 5. 열린 질문

- [ ] Tick 안 다중 BP 호출의 ProcessEvent overhead 측정
- [ ] BP nativization (5.x deprecated) 의 대안
