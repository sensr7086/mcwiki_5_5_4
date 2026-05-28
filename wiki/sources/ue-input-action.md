---
type: source
title: "UE Input — Action sub-skill"
slug: ue-input-action
source_path: raw/ue-wiki-llm/skills/Input/references/Action.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UInputAction]]"
tags: [ue, input, plugin]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Input — Action sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/Action.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

[[entities/UInputAction]] + ValueType 4 종 (Bool / Axis1D / Axis2D / Axis3D) + ETriggerEvent 7 종 + UInputTrigger 8 종 + UInputModifier 9 종.

## 2. Key claims

- ValueType 4 종: Bool / Axis1D (float) / Axis2D (FVector2D) / Axis3D (FVector). BindAction 콜백 시그니처 자동 결정.
- ETriggerEvent 7 종:
  - **Triggered** (활성 동안 매 frame), **Started** (시작), **Ongoing** (활성 중간), **Canceled** (Hold 중 미충족), **Completed** (정상 종료), **None**.
- UInputTrigger 8 종:
  - **Pressed** (한 번): 누른 frame.
  - **Released** (한 번): 뗀 frame.
  - **Hold**: N 초 유지.
  - **Tap**: N 초 안에 떼기.
  - **Pulse**: N 초마다 발화 (auto-fire).
  - **Chord** (다른 Action 활성 + 본 Action): 조합 키.
  - **Down**: 누르고 있는 동안 매 frame.
  - **Combo**: 시퀀스 입력 (격투 게임).
- UInputModifier 9 종: DeadZone / Scale / Negate / Swizzle / Smooth / ResponseCurve / FOVScaling / etc — value 변환.

## 3. Open questions

- [ ] Custom Trigger / Modifier 작성 패턴
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 6
- 추가 (5.5.4 에만): 13
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `description: UInputAction (ValueType 4종 - Bool/Axis1D/Axis2D/Axis3D) + ETriggerE → description: UInputAction (ValueType 4종 - Bool/Axis1D/Axis2D/Axis3D) + ETriggerE`
- `## 2. ETriggerEvent 7종 (가장 중요) → ## 2. ETriggerEvent 5종 + None (가장 중요)`
- `| `UInputTriggerCombo` (5.x) | **시퀀스 (예: 위→위→아래→발사)** | `Combo` 배열 | → | `UInputTriggerChordAction` | **다른 Action 과 함께 눌림** | `ChordAction` (참조) |`
- `- UInputTriggerChord (ChordAction = IA_ShiftKey)   // Shift 도 눌려있어야 → - UInputTriggerChordAction (ChordAction = IA_ShiftKey)   // Shift 도 눌려있어야`

**5.5.4 에만 (5.7.4 에 없음)**:
- ``
- `> **트리거가 활성 조건 결정** — Action 또는 IMC 매핑에 추가. 여러 Trigger AND 조합. UE 5.5 concrete 클래스 10종.`
- ``
- `### 3.1 표준 10종`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Input/references/Action.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Input/references/Action.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
