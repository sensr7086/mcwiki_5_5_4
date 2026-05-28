---
type: entity
title: "UAnimMontage"
aliases: [UAnimMontage, AnimMontage, Montage]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-animation-skill]]"
tags: [ue, asset, animation]
last_updated: 2026-05-09
---

# UAnimMontage

## 요약

[[entities/UObject]] 자손. [[entities/UAnimSequence]] 들의 *섹션화·블렌드 트리거 가능* 컨테이너 — 996 lines. Slot 기반 (AnimGraph 의 Slot 노드와 짝) + Sections (jumpable points) + Branch Points + Notify 통합. `Montage_Play` / `Montage_Stop` / `Montage_JumpToSection` 으로 런타임 제어.

## 관계

- 부모: [[entities/UObject]]
- 컨텐츠: [[entities/UAnimSequence]] (한 또는 여러 개)
- 런타임 호스트: [[entities/UAnimInstance]] (`Montage_Play` 진입점)
- 협력: [[entities/UCharacterMovementComponent]] (RootMotion)

## 핵심 주장

- Slot 시스템: Montage 가 AnimGraph 의 Slot 노드 위에 *덮어 씀*. base pose 와 weighted blend.
- Sections: 시간 구간을 named — JumpToSection / SetNextSection 으로 분기. Combo / Hit reaction 에 표준.
- Branch Points: section 끝에서 다음 section 결정 — Loop / Linear / Branch.
- Notify 통합: Montage 에 직접 Notify 추가 가능 (Sequence 의 Notify 와 별개). Branch Point notify 가 흔함 (콤보 윈도우 등).
- RootMotion: Montage 에 RootMotion 활성 + Character 의 bEnableRootMotionMontagesOnly 또는 IAnimRootMotionProvider. Server Authoritative. [[concepts/RootMotion]]
- 메모리: 1MB ~ 10MB (긴 Montage). 자주 쓰면 [[concepts/Asset-Loading-Policy]] PreloadPrimaryAssets 의무. [[raw/ue-wiki-llm/skills/Animation/SKILL.md]]

## 열린 질문

- [ ] Montage_Play 의 Multiplayer 동기화 — Server Authoritative + Client Prediction 패턴
- [ ] Branch Point notify 와 일반 Notify 의 호출 순서
