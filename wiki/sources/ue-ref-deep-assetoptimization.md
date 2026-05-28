---
type: source
title: "12_AssetOptimizationPolicy — Deep Reference (Bone LOD + StaticMesh LOD + Merging + Audio + Niagara)"
slug: ue-ref-deep-assetoptimization
source_path: raw/ue-wiki-llm/references/deep/AssetOptimizationDeep.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities: []
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
tags: [ue, reference, policy, optimization, enriched-card]
citation_disclosure: "🟢 10 / 🟡 4 / 🔴 0 · raw verified · Cycle 5f #1 enrich"
---

# 12_AssetOptimizationPolicy — Deep Reference

> Source: [[raw/ue-wiki-llm/references/deep/AssetOptimizationDeep.md]]
> 부모 정책: 🎯 [[sources/ue-ref-12-assetoptimizationpolicy]] · [[concepts/Asset-Optimization-Policy]]
> Cycle 5f #1 — stub 카드 → enrich 카드 (5대 영역 매트릭스 + 3-tier marker)

## 1. Summary

🟢 SkeletalMesh Bone LOD + StaticMesh LOD + Actor Merging (HISM/HLOD/WP) + Audio Culling + Niagara Quality Scaling 5대 영역.

## 2. 핵심 §/매트릭스 카탈로그 (raw §1~§5)

### 2.1 SkeletalMesh Bone LOD (raw §1) 🟢

- 🟢 `USkeletalMeshLODSettings` (`SkeletalMeshLODSettings.h:123`) — UDataAsset
- 🟢 `FSkeletalMeshLODGroupSettings` (h:53) — BoneList/BonesToPrioritize/WeightOfPrioritization/LODHysteresis
- 🟢 표준 5단계 매트릭스 (LOD 0~4) — ScreenSize 1.0/0.5/0.25/0.1/0.05 + Bone 비율 100/70/50/30/15%
- 🟢 BonesToPrioritize 표준: head / hand_l/r / weapon_socket / ik_target_*
- 🟢 SkinCacheUsage (5.x) — LOD 별 Enabled/Auto/Disabled
- 🟢 컴포넌트 측: `ForcedLodModel` / `MinLodModel`

### 2.2 StaticMesh LOD (raw §2) 🟢

- 🟢 ScreenSize 임계값 표준 (LOD 0~4) — 1.0/0.5/0.25/0.1/0.05 + 폴리곤 비율 100/50/25/10/5%
- 🟢 Nanite vs Traditional 결정 매트릭스 (6 기준): Skin / Movable+Physics / Translucent / 폴리곤<1000 / Foliage / 정적 콜리전
- 🟢 `bAutoComputeLODScreenSize` 자동 (`StaticMesh.h:712`)
- 🟢 `FPerPlatformInt MinLOD` — PC=0 / Mobile=2 / Switch=1
- 🟢 폴리곤 감축 (Editor — LOD Group > Reduction Settings)

### 2.3 Actor Merging (raw §3) 🟢

- 🟢 4종 방법 비교: HISM / Mesh Merge / HLOD / 5.x WorldPartition HLOD
- 🟢 HISM 코드: `UHierarchicalInstancedStaticMeshComponent::AddInstance`
- 🟡 Mesh Merge (Editor 전용): `MeshUtilities.MergeComponentsToStaticMesh` (`#if WITH_EDITOR`)
- 🟢 HLOD DefaultEngine.ini 설정 (`[/Script/Engine.HierarchicalLODSetup]`)
- 🟡 5.x WorldPartition HLOD: `UWorldPartitionHLODBuilder` (자동 Grid)
- 🟢 결정 트리: 같은 메시 100+ → HISM / 작은 영역 → Mesh Merge / 중~큰 영역 → HLOD / 오픈월드 5.x → WP HLOD

### 2.4 Audio Culling (raw §4) 🟢

- 🟢 `USoundAttenuation` MaxDistance 1차 컬링 (`FSoundAttenuationSettings`)
- 🟢 `USoundConcurrency` MaxCount + ResolutionRule (StopFarthest 등)
- 🟢 `USoundMix` 그룹 단위 Volume mute (`PushSoundMixModifier`)
- 🟢 Significance Manager 통합 — 매우 멀면 Stop, 가까우면 Play
- 🟢 Audio Engine 자동 Voice Limit (`MaxChannels=64`)
- 🟢 결정 트리: BGM=Mix / 3D SFX=Attenuation+Concurrency / 환경음=Significance / 다이얼로그=Priority

### 2.5 Niagara Quality Scaling (raw §5) 🟢

- 🟢 `UNiagaraEffectType` — PerformanceBaseline + ScalabilityOverrides + SignificanceHandling
- 🟢 `FNiagaraSystemScalabilitySettings` — Cull 3종 + SpawnRateScale + UpdateRateScale
- 🟢 품질 5단계 매트릭스 (Cinematic/High/Medium/Low/Mobile) — SpawnCount/UpdateRate/MaxDistance/MaxSystemInstances
- 🟢 표준 EffectType 자산 5종 (Hero/Enemy/Environment/HitEffect/BGFX)
- 🟢 `ENiagaraSignificanceHandling` 4종 (EarliestCullDistance 등)
- 🟢 Quality Level 런타임 전환 (`Scalability::SetQualityLevels`)
- 🟢 Pool 통합 — `ENCPoolMethod::AutoRelease`

## 3. 함정 카탈로그 (raw §5.7 + 일반화)

| # | 함정 | tier |
|---|------|------|
| 1 | NiagaraSystem EffectType 미지정 | 🟢 |
| 2 | Pool 안 사용 + 매 프레임 Spawn (히칭) | 🟢 |
| 3 | Mobile GPU Sim + Bounds 자동 | 🟢 |
| 4 | Quality Level 안 변경 가능 (Settings 메뉴 X) | 🟡 |
| 5 | SkeletalMesh BonesToPrioritize 미지정 → LOD 4 에서 IK 깨짐 | 🟢 |
| 6 | Mesh Merge Editor 전용 코드를 `#if WITH_EDITOR` 외부 호출 | 🟢 |
| 7 | HLOD 빌드 안 함 → 멀리서 메시 누락 | 🟡 |

## 4. Cross-link

- 부모: 🎯 [[sources/ue-ref-12-assetoptimizationpolicy]] · [[concepts/Asset-Optimization-Policy]]
- 페어: [[sources/ue-ref-deep-assetloading]] · [[sources/ue-ref-11-assetloadingpolicy]]
- Animation 페어: [[concepts/Bone-LOD]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[sources/ue-animation-optimization]]
- Significance: [[sources/ue-significance-skill]] · [[entities/USignificanceManager]]
- Niagara: [[sources/ue-niagara-skill]] · [[entities/UNiagaraComponent]]
- sub-skill: [[synthesis/character-many-npc-5-fold-optimization]]

## 5. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| Bone LOD 표준 5단계 | 🟢 verified | `SkeletalMeshLODSettings.h:29-123` |
| StaticMesh LOD 5단계 + Nanite 결정 | 🟢 verified | `StaticMesh.h:712` + 5.x Nanite docs |
| Merging 4종 비교 | 🟢 verified | raw §3 + Engine source |
| Audio Culling 4축 | 🟢 verified | `SoundAttenuation.h` + Significance |
| Niagara Quality 5단계 | 🟢 verified | `NiagaraEffectType.h` + `Scalability.h` |
| 함정 7 (5 🟢 + 2 🟡) | 🟢/🟡 | raw §5.7 + KMCProject 실측 |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | 12_AssetOptimizationPolicy 분리 |
| 2026-05-15 | Cycle 5f #1 — stub 카드 → enrich 카드 (5대 영역 매트릭스 + 3-tier marker + Cross-link 8건) |
