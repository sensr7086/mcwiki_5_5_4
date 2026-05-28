---
type: source
title: "UE AssetClasses — Material sub-skill"
slug: ue-assetclasses-material
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Material.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UMaterial]]"
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, asset, rendering]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE AssetClasses — Material sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Material.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UMaterial (2,083) + UMaterialInstanceConstant (MIC, 디스크) + UMaterialInstanceDynamic (MID, 런타임) + UMaterialInterface (1,278). Domain 7 종 + BlendMode 7 종 + ShadingModel 12 종 + 5.x PSO Precache.

## 2. Key claims

- Domain 7 종: Surface (3D) / DeferredDecal / Light Function / Post Process / UI / Volume / Subsurface — 호스트 컴포넌트 결정자.
- ShadingModel 12 종: DefaultLit / Unlit / Subsurface / PreintegratedSkin / ClearCoat / Hair / Cloth / Eye / TwoSidedFoliage / Volumetric / ThinTranslucent / SingleLayerWater.
- BlendMode 7 종: Opaque / Masked / Translucent / Additive / Modulate / AlphaComposite / AlphaHoldout. Translucent = sort 영향 + 추가 비용.
- MIC vs MID:
  - MIC = `.uasset`, 빌드 시 결정.
  - MID = `UMaterialInstanceDynamic::Create(Parent, Outer)` 런타임 생성. Component 마다 별개 → 동적 파라미터.
- 5.x PSO Precache: 첫 프레임 hitch 회피 — Pipeline State Object 사전 컴파일. Project Settings → Rendering → PSO Precaching.
- MaterialParameterCollection: 글로벌 파라미터 (시간 / 기상).
- MaterialFunction: 노드 그래프의 재사용 단위.

## 3. Open questions

- [ ] PSO Precache 의 Cook 단계 통합
- [ ] Translucent OIT 5.x 통합
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 2
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 13

**주요 시그니처 변경**:
- `└── UMaterialInstance (1,256 lines — 파라미터 오버라이드 + Static Permutation) → └── UMaterialInterface (1,278 lines — IBlendableInterface, IInterface_AssetUserD`

**5.5.4 표현 (5.7.4 에 없음)**:
- `├── UMaterial (2,083 lines — 베이스 머티리얼, Material Editor 그래프)`
- `└── UMaterialInstance (1,177 lines — 파라미터 오버라이드 + Static Permutation)`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Material.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Material.md]]

### Body Reconciliation (2026-05-28 — promoted)

- 자동 substitution + §X 외 본문 grep 검토 완료
- **본문 정합 OK**: UMaterialInstance (1,256 본문 잔존 없음 + 본문 line 23 이미 "UMaterialInterface (1,278)" 5.5.4 값 정합
- 정합 후 tier: **🟢 pass-body-reconciled** (promoted from partial-needs-manual-review)
