---
type: source
title: "UE AssetClasses — Camera sub-skill"
slug: ue-assetclasses-camera
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Camera.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, asset, camera]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Camera sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Camera.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UCameraShakeBase + UCameraShakePattern 4 종 (Wave / Perlin / Sequence / Custom) + UCameraModifier + 5.x UCameraAnimationSequence.

## 2. Key claims

- UCameraShakeBase: 흔들림 자산 베이스. PlayCameraShake (PlayerCameraManager) 또는 Component 측 발화.
- UCameraShakePattern 4 종:
  - Wave: 단순 sin 진동 (TimingFunction).
  - Perlin: 비주기 noise (자연스러운 흔들림).
  - Sequence: 명시적 키프레임 (디자이너 곡선).
  - Custom: 사용자 정의 (override).
- UCameraModifier: PostProcess + 위치 / 회전 modifier. PlayerCameraManager 의 ModifierList.
- 5.x UCameraAnimationSequence: Sequencer 의 카메라 애니메이션 자산 — SequenceCameraShakePattern 의 입력.
- UCameraShakeSourceComponent: shake 발화 위치 + Attenuation (거리 약화).

## 3. Open questions

- [ ] Wave vs Perlin 결정 트리 (어떤 효과에 어느)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 0
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 5

**주요 시그니처 변경**:
- `> **위치**: `Engine/Source/Runtime/Engine/Classes/Camera/CameraShakeBase.h` (439+) → > **위치**: `Engine/Source/Runtime/Engine/Classes/Camera/CameraShakeBase.h` (690) `

**5.5.4 표현 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Camera.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Camera.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **0 변경** (CameraShakeBase.h 라인 수)
- 정합 후 tier: **pass-body-no-direct-cite**
