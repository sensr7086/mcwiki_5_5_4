---
type: source
title: "UE AssetClasses — Physics sub-skill"
slug: ue-assetclasses-physics
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Physics.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, asset, physics]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Physics sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Physics.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UPhysicalMaterial + EPhysicalSurface 32 종 + UPhysicalMaterialMask (5.x) + UPhysicsConstraintTemplate (6DoF Profile).

## 2. Key claims

- UPhysicalMaterial: Friction / Restitution / Density / Damping. Mesh / Mesh Section / Body Setup 에 적용.
- EPhysicalSurface 32 종: SurfaceType_Default + SurfaceType1 ~ SurfaceType31 (Project Settings 에서 명명 — Concrete / Metal / Wood / Flesh 등).
- UPhysicalMaterialMask (5.x): 텍스처 기반 surface 분리 — 한 mesh 의 여러 surface (예: 갑옷 = Metal, 살갗 = Flesh).
- UPhysicsConstraintTemplate: 6DoF (X / Y / Z / Twist / Swing1 / Swing2) Profile 자산 — 캐릭터 관절 / 로봇 / 차량 suspension.
- 사용처: HitResult.PhysMaterial — 발자국 / 피격 사운드 / VFX 결정.
- Anim Physics 통합: UPhysicalAnimationComponent 의 Profile 셋업.

## 3. Open questions

- [ ] PhysicalMaterialMask 의 5.x 표준 사용 패턴
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 0
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 0

**주요 시그니처 변경**:
- `> **위치**: `Engine/Source/Runtime/Engine/Public/PhysicalMaterials/PhysicalMateria → > **위치**: `Engine/Source/Runtime/PhysicsCore/Public/PhysicalMaterials/PhysicalMa`

**5.5.4 표현 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Physics.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Physics.md]]

### Body Reconciliation (2026-05-28 — promoted)

- 자동 substitution + §X 외 본문 grep 검토 완료
- **본문 정합 OK**: PhysicalMaterials/ 본문 잔존 없음 (§X cite 만, false positive)
- 정합 후 tier: **🟢 pass-body-reconciled** (promoted from partial-needs-manual-review)
