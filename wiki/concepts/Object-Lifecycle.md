---
type: concept
title: "UObject Lifecycle"
aliases: [UObject Lifetime, PostLoad, BeginDestroy]
sources:
  - "[[sources/ue-coreuobject-skill]]"
related_concepts:
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Actor-Lifecycle]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UObject Lifecycle

## 1. 정의 (한 줄)

[[entities/UObject]] 의 생성 ~ 소멸 6 단계 — Construct / PostInitProperties / PostLoad (디스크 로드 시) / Serialize / BeginDestroy / FinishDestroy.

## 2. 자세히

```
NewObject<T>() ─┐
                ├─▶ Construct (C++ ctor) — UPROPERTY default 값 설정
                ├─▶ PostInitProperties — Constructor 후 추가 초기화
                ├─▶ (디스크 로드 시) PostLoad — Editor 만의 fixup, 마이그레이션
                └─▶ 사용 가능

GC 사이클 ──┐
            ├─▶ unreachable 판정
            ├─▶ MarkAsGarbage (5.x)
            ├─▶ BeginDestroy — 외부 참조 해제 / 리소스 release 시작
            └─▶ FinishDestroy — 메모리 해제. 이 시점 이후 dangling.
```

## 3. 변형 / 사례 / 응용

- **PostLoad vs PostInitProperties**: PostLoad 는 디스크에서 deserialize 후만, PostInitProperties 는 매 NewObject. fixup / version migration 은 PostLoad.
- **BeginDestroy 함정**: 이 시점에 다른 UObject 참조는 이미 dangling 가능 — TWeakObjectPtr 로 안전 접근.
- **CDO (Class Default Object)**: `RF_ClassDefaultObject` flag — Constructor 안에서 `if (HasAnyFlags(RF_ClassDefaultObject))` 로 분기. CDO 수정 금지.
- [[concepts/Component-Lifecycle]] 와 [[concepts/Actor-Lifecycle]] 가 본 lifecycle 위에 layer 추가.

## 4. 관련 entity

- [[entities/UObject]]

## 5. 열린 질문

- [ ] 5.x MarkAsGarbage vs Legacy MarkPendingKill 의 동작 차이
