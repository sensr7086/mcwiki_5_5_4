---
type: source
title: "UE 5.7.4 Input Module — Main SKILL"
slug: ue-input-skill
source_path: raw/ue-wiki-llm/skills/Input/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UInputAction]]"
  - "[[entities/UInputMappingContext]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
  - "[[entities/UEnhancedInputComponent]]"
  - "[[entities/FKey]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
  - "[[concepts/IMC-Stack]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, input]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE 5.7.4 Input Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Input/SKILL.md]]

## 1. Summary

5.x Enhanced Input Plugin 표준 + Legacy + InputCore + InputDevice. 5 sub-skill 분할.

## 2. Sub-skills (5 — Phase 4D 완료)

- [[sources/ue-input-enhancedinput]] — 5.x Plugin 메인 + 4 단 셋업 + Pawn/PC 통합
- [[sources/ue-input-action]] — UInputAction + ValueType 4 + ETriggerEvent 7 + UInputTrigger 8 + UInputModifier 9
- [[sources/ue-input-subsystem]] — UEnhancedInputLocalPlayerSubsystem + IMC Stack 7 단계 + Modular 5.x
- [[sources/ue-input-inputcore]] — FKey + EKeys 200+ + Face Button 플랫폼 추상화
- [[sources/ue-input-legacy]] — UInputComponent + DefaultInput.ini + Force Feedback 4 채널 + Haptic 5.x + Migration 5 단계

## 3. Open questions

- [ ] Enhanced Input 의 Multiplayer 동작 (Server-side Input)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| 2 | [`Action`](./Action/SKILL.md) | `skills/Input/references/Action.md` | **UI → | 2 | [`Action`](./Action/SKILL.md) | `skills/Input/references/Action.md` | **UI`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Input/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Input/SKILL.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
