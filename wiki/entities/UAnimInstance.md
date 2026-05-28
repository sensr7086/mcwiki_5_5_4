---
type: entity
title: "UAnimInstance"
aliases: [UAnimInstance, AnimInstance, AnimBP, AnimBlueprint]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation]
last_updated: 2026-05-09
---

# UAnimInstance

## 요약

[[entities/UObject]] 자손. **SkeletalMesh 의 런타임 애니메이션 호스트** — 1,776 lines (UE 5.7.4). [[entities/USkeletalMeshComponent]] 의 AnimClass 로 등록. 게임 스레드 측 NativeUpdate + 워커 스레드 측 NativeThreadSafeUpdate 분리. [[entities/FAnimInstanceProxy]] 가 워커 스레드 데이터 owner.

## 관계

- 부모: [[entities/UObject]]
- 페어 호스트: [[entities/USkeletalMeshComponent]]
- 워커 스레드 owner: [[entities/FAnimInstanceProxy]]
- 협력: [[entities/FAnimNode-Base]] (AnimGraph 노드들), [[entities/UAnimNotify]]
- 자산: UAnimBlueprint (Editor 만 — Cooked 에서는 UAnimInstance 자손 클래스만)

## 핵심 주장

- 라이프사이클 5 단계: NativeInitializeAnimation → NativeBeginPlay → NativeUpdateAnimation (게임 스레드) → NativeThreadSafeUpdateAnimation (워커 스레드) → NativeUninitializeAnimation. [[raw/ue-wiki-llm/skills/Animation/SKILL.md]]
- **NativeUpdate vs NativeThreadSafeUpdate 분리 의무**: 게임 스레드 의존 (Owner Pawn 의 InputVector 등) 은 NativeUpdate, 그 외 무거운 계산은 ThreadSafe 로. ThreadSafe 안에서 GameThread-only API 호출 금지.
- [[entities/FAnimInstanceProxy]]: 워커 스레드 데이터 owner. AnimInstance 가 게임 스레드에서 데이터 푸시 → Proxy 가 워커 스레드에서 사용. TWeakObjectPtr 로 캐싱하거나 값 복사만.
- Curve API: GetCurveValue / GetCurveValueFiltered / SetCurveValue. AnimSequence 의 Curve 가 런타임에 노출.
- Montage API: Montage_Play / Montage_Stop / Montage_JumpToSection / Montage_IsPlaying / OnMontageBlendingOut delegate.
- AnimGraph 의 entry point — UAnimBlueprint 의 그래프 (또는 native 의 [[entities/FAnimNode-Base]] 자손) 가 Pose 평가.
- [[concepts/URO]] / [[concepts/EVisibilityBasedAnimTickOption]] 적용 시 NativeUpdate 호출 빈도 자동 분할.

## 열린 질문

- [ ] FAnimInstanceProxy 의 정확한 데이터 흐름 — 게임 → 워커 → 게임
- [ ] AnimBlueprint vs Native AnimInstance 의 결정 기준 (BP 함정 인지)
