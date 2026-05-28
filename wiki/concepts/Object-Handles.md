---
type: concept
title: "UObject 핸들 4종"
aliases: [TObjectPtr, TWeakObjectPtr, TStrongObjectPtr, TSoftObjectPtr]
sources:
  - "[[sources/ue-coreuobject-skill]]"
related_concepts:
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UObject 핸들 4종

## 1. 정의 (한 줄)

[[entities/UObject]] 참조의 4 가지 안전 패턴 — 각각 GC / lifetime / loading 측면에서 다른 보장 + 비용.

## 2. 자세히

| 핸들 | GC edge | Lifetime | 사용처 |
| -- | -- | -- | -- |
| `TObjectPtr<T>` | ✅ Hard | 객체 살아있는 동안 | UPROPERTY 멤버 표준 (5.x). raw pointer 의 안전 wrapper. Editor 에서 lazy resolve. |
| `TWeakObjectPtr<T>` | ❌ | dangling 자동 NULL | 캐싱 / 비-소유 참조. Lifetime 분리. |
| `TStrongObjectPtr<T>` | ✅ Hard (외부) | 명시적 RAII | 비-UCLASS 컨텍스트 (FStruct / 일반 C++ 클래스) 에서 UObject 강참조. |
| `TSoftObjectPtr<T>` | ❌ (lazy) | path 만 보유, 필요 시 load | [[concepts/Asset-Loading-Policy]] 의 핵심 — 어셋 자체를 메모리에 안 올림. |

## 3. 변형 / 사례 / 응용

- 일반 raw `T*` 를 UPROPERTY 멤버로 사용 가능 (자동 GC) — 단 5.x 표준은 `TObjectPtr<T>`.
- `TSoftClassPtr<T>` = SoftObjectPtr 의 클래스 버전 — `TSubclassOf<T>` (Hard) 의 soft 변형.

## 4. 관련 entity

- [[entities/UObject]]

## 5. 열린 질문

- [ ] 5.x ObjectHandles 의 lazy resolve 메커니즘 — Editor vs Cooked
