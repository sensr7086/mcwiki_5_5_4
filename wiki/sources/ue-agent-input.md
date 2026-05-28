---
type: source
title: "UE Input Specialist — Enhanced Input 5.x + 5 sub-skill + IMC Priority 7단"
slug: ue-agent-input
source_path: raw/ue-wiki-llm/agents/ue-input-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/UInputAction]]"
  - "[[entities/UInputMappingContext]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
  - "[[concepts/IMC-Stack]]"
tags: [ue, agent, specialist, input, enhanced-input, imc-priority-7, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Input Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-input-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Input]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 UE 5.7.4 Enhanced Input 표준 전문가 — **5 sub-skill** (EnhancedInput / Action / Subsystem / InputCore / Legacy). `UInputAction` + `UInputMappingContext` + ETriggerEvent + DeadZone + IMC Priority 7단 + Couch Co-op LocalPlayer Subsystem 자동.

## 2. 자동 로드 (4 파일)

1. `skills/Input/SKILL.md` (메인 — 5 sub-skill)
2. [[sources/ue-input-enhancedinput]] (5.x 표준)
3. [[sources/ue-components-systemcomponents]] §1 (`UInputComponent`)
4. [[sources/ue-ref-07-profilingscopeRule]]

## 3. Enhanced Input 의무 (5.x)

❌ Legacy `BindAction(TEXT(...))` — 마이그레이션 / 에디터만 허용
✅ Enhanced Input — 모든 5.x 신규 게임 의무

```ini
; DefaultInput.ini (의무)
[/Script/Engine.InputSettings]
DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput
DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent
```

```cpp
if (auto* EIC = Cast<UEnhancedInputComponent>(InInputComponent))
{
    EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyChar::OnMove);
    EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
}
```

## 4. ETriggerEvent 매트릭스

| 입력 | ETriggerEvent | 사유 |
|------|--------------|------|
| Move (Axis) | `Triggered` | 매 프레임 |
| Jump | `Started + Completed` | 한 번 + 떼는 순간 |
| Charge (Hold) | `Started + Triggered + Canceled` | 충전 |
| Auto-Fire | `Triggered` (Pulse) | 일정 간격 |
| Combo | `Started + Combo Trigger` | 시퀀스 |
| Sprint (Chord) | `Triggered` (Chorded) | 다른 키 + |
| Tap | `Triggered` (Tap) | 짧은 누름 |

## 5. IMC Priority 7단

| Priority | 의미 | 예시 |
|---------|------|------|
| 200 | System | 메뉴 호출 (Esc) |
| 150 | Modal | 다이얼로그 |
| 100 | Menu | UI |
| 50 | Dialog | 인게임 |
| 20 | Vehicle | 차량 모드 |
| 10 | FirstPerson | 1인칭 |
| 0 | Default | 일반 |

## 6. DeadZone / LocalPlayer Subsystem / Face Button

- DeadZone: Radial **0.20** / Trigger 0.05 / VR 0.10
- LocalPlayer Subsystem (Couch Co-op): `UEnhancedInputLocalPlayerSubsystem` — `ClearAllMappings` + `AddMappingContext(IMC, Priority)`
- Face Button 추상: `Gamepad_FaceButton_Bottom` (Confirm) / `Right` (Cancel) — Xbox/PS/Switch 자동

## 7. Pause Action

`bTriggerWhenPaused = true` UInputAction + Priority 200 IMC 만 활성 (다른 IMC 비활성).

## 8. Baseline Grep 의무

함정 키워드: `UInputAction` / `IMC` / `ETriggerEvent` / `Enhanced` / `UEnhancedInputComponent` / `LocalPlayerSubsystem` / `Modifier` / `FKey`.

## 9. 거부 조건

- UInputComponent 없는 단순 컴포넌트 — `ue-components-specialist`
- Player Controller / Pawn 입력 흐름 — `ue-gameframework-specialist`

## 10. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-gameframework]] (Possession + PlayerController) · [[sources/ue-agent-components]] (UInputComponent)
- sub-skill: [[sources/ue-input-skill]] · [[sources/ue-input-enhancedinput]] · [[sources/ue-input-action]] · [[sources/ue-input-subsystem]] · [[sources/ue-input-inputcore]] · [[sources/ue-input-legacy]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 11 절. Enhanced Input 의무 + ETriggerEvent 7 매트릭스 + IMC 7단 + Couch Co-op |
