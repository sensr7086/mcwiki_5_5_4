---
type: source
title: "UE AssetClasses — Animation sub-skill"
slug: ue-assetclasses-animation
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Animation.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UAnimSequence]]"
  - "[[entities/UAnimMontage]]"
  - "[[entities/UBlendSpace]]"
  - "[[entities/UAnimInstance]]"
tags: [ue, asset, animation]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Animation sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Animation.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

[[entities/UAnimSequence]] (973) + [[entities/UAnimMontage]] (982) + [[entities/UBlendSpace]] (948) + UAnimBlueprint (299) + [[entities/UAnimInstance]] (1,705) + USkeleton (1,037). 5.x NativeThreadSafeUpdateAnimation + Curve API + Montage_* + AnimNotify.

## 2. Key claims

- UAnimSequence: 단일 모션 클립. Pose 키 + Curve + Notify + 5.x ACL compression.
- UAnimMontage: AnimSequence 들의 컨테이너 + Slot + Sections + Branch Points + Notify. `Montage_Play` API.
- UBlendSpace / BlendSpace1D: 다차원 파라미터 → 모션 블렌드 (Locomotion 표준).
- UAnimBlueprint: Editor 만의 AnimGraph 그래프. Cooked 빌드는 UAnimInstance 자손 클래스만.
- UAnimInstance (런타임 측): Pose 평가 + Curve + Montage_* + Native* 라이프사이클. → [[sources/ue-animation-animinstance]]
- USkeleton: 본 계층 + Slot 정의 + Curve Mapping + Compatible Skeletons (5.x).
- 5.x ACL (Animation Compression Library): default compression. 메모리 절감.

## 3. Open questions

- [ ] ACL 5.x 압축 비율 비교 (legacy 대비)
- [ ] Montage 의 Multiplayer 동기 표준
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 5
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 2
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 18

**주요 시그니처 변경**:
- `description: UAnimSequence (1,001) + UAnimMontage (996) + UBlendSpace (966) + UA → description: UAnimSequence (973) + UAnimMontage (982) + UBlendSpace (948) + UAni`
- `> **파일**: `AnimSequence.h` (1,001) + `AnimSequenceBase.h` (319) + `AnimMontage.h → > **파일**: `AnimSequence.h` (973) + `AnimSequenceBase.h` (351) + `AnimMontage.h` `
- `│   ├── UAnimSequence (1,001 lines — 가장 흔함, 일반 애니) → ├── UAnimSequenceBase (351 lines — 키 기반 시퀀스)`
- `└── UBlendSpace (966 lines — 1D / 2D / AimOffset Blend) → │   └── UAnimMontage (982 lines — Section + BlendIn/Out + Notify + RootMotion)`
- `## 2. UAnimSequence (가장 흔함 — 1,001 lines) → ## 2. UAnimSequence (가장 흔함 — 973 lines)`

**5.5.4 표현 (5.7.4 에 없음)**:
- `│   ├── UAnimSequence (973 lines — 가장 흔함, 일반 애니)`
- `└── UBlendSpace (948 lines — 1D / 2D / AimOffset Blend)`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Animation.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Animation.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **4 변경** (1,001 → 973 / 996 → 982 / 966 → 948)
- 정합 후 tier: **pass-body-reconciled**
