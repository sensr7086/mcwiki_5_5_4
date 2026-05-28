---
type: source
title: "UE refs — 12 AssetOptimizationPolicy (5대 영역 hub)"
slug: ue-ref-12-assetoptimizationpolicy
source_path: raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
tags: [ue, reference, policy, optimization, lod, nanite, significance]
---

# UE refs — 12 AssetOptimizationPolicy 🎯

> Source: [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]] · CLAUDE.md §0.1.3 의무 정책

## 1. Summary

🎯 **어셋 최적화 5 대 영역** — 60 fps + 메모리 한계 회피의 90% 책임. 자산이 메모리 / GPU / CPU 에 미치는 영향 최소화. 모든 자산 / 다수 NPC 환경 / 60fps 검증 시 의무. 권위 concept = [[concepts/Asset-Optimization-Policy]]. 깊이 자료 = [[sources/ue-ref-deep-assetoptimization]].

## 2. 5대 영역 통합 매트릭스 🟢

| § | 영역 | 핵심 룰 | sub-skill |
| -- | -- | -- | -- |
| 1 | **SkeletalMesh Bone LOD** | `USkeletalMeshLODSettings` + `BonesToRemove` (LOD별 70/50/30/15%) + `BonesToPrioritize` (head/hand/weapon_socket/IK) + `LODHysteresis 0.05` + 5.x `SkinCacheUsage` | [[sources/ue-assetclasses-mesh]] + [[sources/ue-components-meshcomponents]] |
| 2 | **StaticMesh LOD** | ScreenSize 표준 `1.0 / 0.5 / 0.25 / 0.1 / 0.05` + `bAutoComputeLODScreenSize=true` + `MinLOD` 플랫폼별 + 5.x **Nanite vs Traditional 결정 매트릭스** (Static + 정적 콜리전 = Nanite 의무) | [[sources/ue-assetclasses-mesh]] |
| 3 | **Actor Merging** | 4종 결정 트리 — HISM (동일 메시 100+) / Mesh Merge (작은 영역 — Editor 🛠) / HLOD (큰 영역 — 4.x) / 5.x **WorldPartition HLOD** (오픈 월드 자동) | [[sources/ue-spatialpartition-worldpartitionruntime]] |
| 4 | **Audio Culling** | Attenuation `MaxDistance + FalloffDistance` (1차 컬링) + Concurrency `MaxCount + StopFarthest` (16→4) + SoundMix Volume Mute + Significance 통합 | [[sources/ue-assetclasses-audio]] + [[sources/ue-components-audiocomponent]] |
| 5 | **Niagara Quality Scaling** | **모든 NiagaraSystem = `UNiagaraEffectType` 지정 의무** + 품질 레벨 5종 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2 `SpawnCountScale`) + Pool `ENCPoolMethod::AutoRelease` + `Scalability::SetQualityLevels` | [[sources/ue-niagara-skill]] |

## 3. 다수 NPC LOD 5단계 통합 매트릭스 🟢

> 50+ 캐릭터 환경 표준 — **Significance Manager 출력 = LOD 인덱스 → 9개 항목 일괄 적용**.

| 항목 | LOD 0 (근접) | LOD 1 | LOD 2 | LOD 3 (원거리) |
| -- | -- | -- | -- | -- |
| SkeletalMesh Bone | 100% | 70% (손가락 X) | 50% (보조 본 X) | 30% (Cloth X) |
| SkinCacheUsage | Enabled | Auto | Disabled | Disabled |
| EVisibilityBasedAnimTickOption | AlwaysTickPoseAndRefreshBones | OnlyTickPoseWhenRendered | OnlyTickMontages | AlwaysSkipPostProcess |
| URO | OFF | ON Rate=4 | ON Rate=8 | ON Rate=15 |
| PhysicsAsset | Full | Full | Simple | None (정적) |
| Niagara `SpawnCountScale` | 1.0 | 0.7 | 0.4 | 0.0 (Cull) |
| Audio | 3D + Concurrency | 3D + 거리 감쇠 | 거리 컬링 | OFF |
| NetUpdateFrequency | 33Hz | 10Hz | 2Hz | 1Hz |
| Capsule Overlap | 활성 | 활성 | 비활성 | 비활성 |

## 4. 함정 (10대 요약)

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | SkeletalMesh `LODSettings` 자산 미지정 | `USkeletalMeshLODSettings` 의무 — Bone LOD + Hysteresis |
| 2 | `BonesToPrioritize` 미지정 — LOD 4 에서 head 까지 제거 | head / hand / weapon_socket 의무 |
| 3 | LOD ScreenSize 임의 (0.8 / 0.4 / 0.2) | 표준 (0.5 / 0.25 / 0.1 / 0.05) |
| 4 | 5.x Nanite + Skin (SkeletalMesh) 시도 | Nanite = Static 전용. SkM = Traditional LOD |
| 5 | 동일 메시 100개 Spawn — HISM 안 씀 | HISM / Foliage / WorldPartition HLOD |
| 6 | 5.x WorldPartition + HLOD 비활성 | WP = HLOD 빌드 의무 |
| 7 | Audio Attenuation 미지정 (모든 Sound Global) | `MaxDistance + FalloffDistance` 의무 |
| 8 | Concurrency 미지정 + 발사음 16개 동시 재생 | `MaxCount = 4` + `StopFarthest` |
| 9 | NiagaraSystem `EffectType` 미지정 | `EffectType` 의무 — Cull / Scaling |
| 10 | 🚨 다수 NPC 환경 + Significance 통합 안 함 | `USignificanceManager` + 위 5대 영역 모두 |

## 5. 체크리스트 (모든 자산 표준)

- [ ] **SkM**: LODSettings 자산 / LOD 5단계 / BonesToRemove + BonesToPrioritize / `LODHysteresis 0.05`
- [ ] **SM**: LOD 5단계 ScreenSize 표준 / `bAutoComputeLODScreenSize` / 5.x Nanite (Static)
- [ ] **Merging**: 동일 메시 100+ = HISM / 큰 영역 = HLOD / 오픈 월드 = WP HLOD
- [ ] **Audio**: 3D Sound = Attenuation / 자주 재생 = Concurrency / 환경음 = Significance
- [ ] **Niagara**: `EffectType` 의무 / Quality `SpawnCountScale` / Pool `AutoRelease`
- [ ] **통합**: 다수 NPC = Significance + 5대 영역 모두 / **Cooked Build** `stat unit` `stat fps` 검증

## 6. Cross-link

- 권위 concept: [[concepts/Asset-Optimization-Policy]] · [[concepts/Bone-LOD]] · [[concepts/URO]] · [[concepts/EVisibilityBasedAnimTickOption]]
- 깊이 자료: [[sources/ue-ref-deep-assetoptimization]] (영역별 정밀)
- 자매 정책: [[sources/ue-ref-11-assetloadingpolicy]] (PreLoad — 페어) · [[sources/ue-ref-07-profilingscopeRule]] (Tick 스코프) · [[sources/ue-ref-09-globaliteratorpolicy]]
- 통합 진입점: [[sources/ue-significance-skill]] (§4 Audio + §5 Niagara Cull 동시 적용)
- 카테고리 main: [[sources/ue-assetclasses-skill]] · [[sources/ue-components-skill]] · [[sources/ue-niagara-skill]]
- 캐릭터 통합: [[sources/ue-gameframework-pawncharacter]] §6 (10종 최적화) · [[sources/ue-gameframework-characteroptimization]] (deep)
- 다수 NPC synthesis: [[synthesis/character-many-npc-5-fold-optimization]] · [[synthesis/ai-npc-squad-coordination-tick-budget]]
