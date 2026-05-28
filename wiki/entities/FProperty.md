---
type: entity
title: "FProperty"
aliases: [FProperty, UProperty (deprecated)]
kind: model
sources:
  - "[[sources/ue-coreuobject-skill]]"
tags: [ue, runtime, reflection]
last_updated: 2026-05-09
---

# FProperty

## 요약

UE 5.x 의 reflection 표준 — UPROPERTY 마크업으로 표시된 멤버 변수 1개당 1개의 FProperty 인스턴스. 메모리 offset + 타입 정보 + flag (Replicated / Transient / EditAnywhere 등) 보유. UE 4.25+ 에서 `UProperty` 가 `FProperty` 로 마이그레이션 — 신규 코드는 항상 FProperty.

## 관계

- 부모 클래스 [[entities/UClass]] 에 linked list 로 등록
- 자손: FBoolProperty / FIntProperty / FObjectProperty / FArrayProperty / FStructProperty / FMulticastDelegateProperty / ...
- Deprecated 형: UProperty (UE 4.x) — 호환·이해용으로만 (`raw/ue-wiki-llm/skills/CoreUObject/DeprecatedUProperty/`)

## 핵심 주장

- UE 4.25+ 에서 `FProperty` 가 표준. 신규 코드는 `UProperty` 사용 금지 (deprecated). [[sources/ue-coreuobject-skill]]
- FProperty 의 메모리 offset 으로 동적 멤버 접근 가능 (`Property->ContainerPtrToValuePtr<>(Object)`). [[concepts/Reflection-System]]
- Replication = `UPROPERTY(Replicated)` + DOREPLIFETIME 매크로 + GetLifetimeReplicatedProps override. FProperty 가 어떤 멤버를 복제할지 결정. [[concepts/Reflection-System]]
- 위험한 cast 는 컴파일 에러: `UnsafeTypeCastWarningLevel = WarningLevel.Error` (CoreUObject.Build.cs).

## 열린 질문

- [ ] UProperty → FProperty 마이그레이션의 5.x 잔여 영향 — `raw/ue-wiki-llm/skills/CoreUObject/DeprecatedUProperty/` 에서 디테일
- [ ] FProperty 기반 동적 직렬화 패턴 (Editor 도구 작성 시)
