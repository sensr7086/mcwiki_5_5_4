---
type: source
title: "UE Input — InputCore sub-skill"
slug: ue-input-inputcore
source_path: raw/ue-wiki-llm/skills/Input/references/InputCore.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FKey]]"
tags: [ue, input]
---

# UE Input — InputCore sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/InputCore.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

InputCore 모듈 — [[entities/FKey]] + EKeys 200+ (Mouse / Keyboard / Gamepad / Touch / VR / Gesture / Tilt). Face Button 플랫폼 추상화 (BottomFace / RightFace / LeftFace / TopFace).

## 2. Key claims

- 분류:
  - Mouse: MouseX / MouseY / LeftMouseButton / RightMouseButton / MiddleMouseButton / MouseWheelAxis.
  - Keyboard: A~Z / 0~9 / SpaceBar / Escape / Enter / Modifier (Shift/Ctrl/Alt).
  - Gamepad: Gamepad_LeftThumbstick_X/Y / Gamepad_RightTrigger / Gamepad_FaceButton_Bottom (Xbox A / PS Cross).
  - Touch: Touch1 ~ Touch10.
  - VR: Various (OpenXR mappings).
  - Gesture: Pinch / Rotate / Swipe.
  - Tilt: Mobile 자이로.
- Face Button 추상화: 플랫폼 차이 흡수. Xbox A = PS Cross = Switch B (위치 기반).
- EKeys::IsValid / IsModifierKey / IsAxisKey / IsAnalogKey 헬퍼.
- Project Settings → Input 의 Action / Axis Mappings (Legacy) — IMC 의 우회.

## 3. Open questions

- [ ] Switch Pro Controller 의 platform-specific 매핑
- [ ] OpenXR 의 VR Controller 표준 키
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 2 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Input/references/InputCore.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Input/references/InputCore.md`
