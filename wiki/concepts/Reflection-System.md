---
type: concept
title: "UE Reflection System"
aliases: [Reflection, UCLASS, UPROPERTY, UFUNCTION]
sources:
  - "[[sources/ue-coreuobject-skill]]"
related_concepts:
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Object-Lifecycle]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UE Reflection System

## 1. 정의 (한 줄)

UCLASS / UPROPERTY / UFUNCTION 매크로 + UnrealHeaderTool (UHT) 가 빌드 시 generated.h 를 만들어 [[entities/UClass]] / [[entities/FProperty]] 메타 정보를 생성, 런타임에 동적 멤버 접근/직렬화/네트워크 복제/BP 노출이 가능해지는 시스템.

## 2. 자세히

C++ 에는 native reflection 이 없으므로 UE 가 **UHT 가 generated.h 를 자동 생성** 하는 방식으로 추가. 모든 UObject 자손 클래스의 메타 정보가 [[entities/UClass]] 에 등록되고, 그 클래스의 멤버 변수 (UPROPERTY) 는 [[entities/FProperty]] linked list 로, 함수 (UFUNCTION) 는 UFunction linked list 로 등록.

## 3. 변형 / 사례 / 응용

- **GC 통합**: UPROPERTY 로 표시된 UObject 멤버 = GC reachability 그래프의 edge. UPROPERTY 누락 시 GC 가 dangling pointer.
- **Replication**: UPROPERTY(Replicated) + DOREPLIFETIME → FProperty flag 가 복제 대상 표시.
- **Serialization**: UPROPERTY 만 자동 직렬화. Transient 는 제외.
- **BP 노출**: UPROPERTY(BlueprintReadWrite) / UFUNCTION(BlueprintCallable) — Editor 의 BP 그래프에서 사용 가능.
- **Editor 메타**: EditAnywhere / VisibleAnywhere / Category / meta=(ClampMin=0) 등.

## 4. 관련 entity

- [[entities/UObject]] (모든 UCLASS 의 부모)
- [[entities/UClass]] (메타 클래스)
- [[entities/FProperty]] (변수 메타)

## 5. 열린 질문

- [ ] 5.x ObjectHandles + TObjectPtr 의 lazy load 가 reflection 에 미치는 영향
- [ ] CDO (Class Default Object) 의 reflection 에서의 역할
