---
type: concept
title: "UPROPERTY Markup"
aliases: [UPROPERTY, UPROPERTY specifier]
sources:
  - "[[sources/ue-coreuobject-skill]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/Garbage-Collection]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UPROPERTY Markup

## 1. 정의 (한 줄)

[[concepts/Reflection-System]] 의 변수 표시 매크로 — UPROPERTY(specifiers) 로 [[entities/FProperty]] 등록 + GC edge + 직렬화 + 네트워크 복제 + Editor/BP 노출 결정.

## 2. 자세히

표시되지 않은 멤버는 reflection 시스템 밖 — [[concepts/Garbage-Collection]] 가 못 봄 → UObject 멤버는 dangling 위험. [[entities/UPrimitiveComponent]] / [[entities/USkeletalMeshComponent]] 같은 자손 클래스의 모든 UE 자산 멤버는 의무적으로 UPROPERTY.

## 3. 변형 / 사례 / 응용

흔한 specifier:
- **EditAnywhere** / VisibleAnywhere — Editor 패널 노출
- **BlueprintReadWrite** / BlueprintReadOnly — BP 그래프 노출
- **Replicated** + DOREPLIFETIME — 네트워크 복제
- **ReplicatedUsing=OnRep_Foo** — 복제 시 callback
- **Transient** — 직렬화 제외
- **Category="Movement"** — Editor 그룹화
- **meta=(ClampMin="0", ClampMax="100")** — Editor validation
- **SaveGame** — UGameplayStatics::SaveGame 대상

## 4. 관련 entity

- [[entities/FProperty]]
- [[entities/UObject]]

## 5. 열린 질문

- [ ] specifier 충돌 매트릭스 (BlueprintReadOnly + EditAnywhere 등)
- [ ] 5.x AdvancedDisplay / EditFixedSize 등의 활용
