---
type: source
title: "UE Asset Specialist — AssetClasses 10 sub-skill + 11/12 정책 + SpawnActor 4단"
slug: ue-agent-asset
source_path: raw/ue-wiki-llm/agents/ue-asset-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities: []
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
tags: [ue, agent, specialist, asset, asset-loading-12-step, asset-optimization-5-area, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Asset Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-asset-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[AssetClasses]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 자산 클래스 + 어셋 로드 / 최적화 통합 전문가. **AssetClasses 10 sub-skill** (Mesh / Material / Texture / Animation / Audio / Data / VFX / Camera / Physics / AssetUserData) + **11_AssetLoadingPolicy** (SpawnActor 히칭 4단) + **12_AssetOptimizationPolicy** (5대 영역) + Bone LOD + StaticMesh LOD + Niagara Quality 자동.

## 2. 자동 로드 (5 파일)

1. `skills/AssetClasses/SKILL.md`
2. [[sources/ue-ref-11-assetloadingpolicy]] (핵심)
3. [[sources/ue-ref-deep-assetloading]] (FStreamableManager / Bundle / 함정 12)
4. [[sources/ue-ref-12-assetoptimizationpolicy]] (5대 영역)
5. [[sources/ue-ref-deep-assetoptimization]]

## 3. 자산 종류별 결정 매트릭스

| 자산 | sub-skill | 핵심 |
|------|-----------|------|
| StaticMesh / SkeletalMesh | [[sources/ue-assetclasses-mesh]] | 5.x Nanite + Compatible Skeleton |
| Material / MaterialInstance | [[sources/ue-assetclasses-material]] | 5.x PSO Precache + MIC vs MID |
| Texture / Render Target | [[sources/ue-assetclasses-texture]] | CompressionSettings + 5.x VT/RVT |
| AnimSequence / Montage / AnimBP | [[sources/ue-assetclasses-animation]] | NativeThreadSafeUpdateAnimation |
| SoundCue / SoundWave | [[sources/ue-assetclasses-audio]] | MetaSounds + 5종 ResolutionRule |
| DataAsset / DataTable | [[sources/ue-assetclasses-data]] | UPrimaryDataAsset + Bundle |
| Niagara / Particle | [[sources/ue-assetclasses-vfx]] | 5.x Niagara |
| CameraShake / Modifier | [[sources/ue-assetclasses-camera]] | 5.x UCameraAnimationSequence |
| PhysicalMaterial | [[sources/ue-assetclasses-physics]] | EPhysicalSurface 32종 |
| AssetUserData ⭐ | [[sources/ue-assetclasses-assetuserdata]] | UMCHitBoneCurveUserData KMCProject 사례 |

## 4. SpawnActor 히칭 4단 표준

```cpp
// 의무 패턴 (Cooked Build OK)
1. PreLoad — UAssetManager::PreloadPrimaryAssets({...}, ..., bLoadRecursive=true)
2. Wait — Handle->WaitUntilComplete() 또는 Delegate
3. SpawnActorDeferred — World->SpawnActorDeferred<>(Class, Transform)
4. FinishSpawning — A->FinishSpawning(Transform)
```

> ❌ `World->SpawnActor<>()` 직접 — Cooked Build 첫 호출 100ms~1s 히칭.

## 5. 최적화 5대 영역 (12_AssetOptimizationPolicy)

- **SkeletalMesh Bone LOD** — `USkeletalMeshLODSettings` + BonesToRemove (70/50/30/15%)
- **StaticMesh** — ScreenSize (1.0/0.5/0.25/0.1/0.05) + 5.x Nanite
- **Actor Merging** — HISM (100+ 동일) / HLOD / 5.x WorldPartition HLOD
- **Audio Culling** — Attenuation + Concurrency (5종) + Significance
- **Niagara Quality** — `UNiagaraEffectType` 의무 + 품질 5종 (Cinematic/High/Medium/Low/Mobile)

## 6. Soft vs Hard 결정 매트릭스

| 시나리오 | Reference | 사유 |
|---------|----------|------|
| 항상 사용 + 작은 자산 | Hard (TObjectPtr) | 단순 |
| 자주 사용 + 종류 적음 | Hard + Match Start PreLoad | 첫 호출 히칭 회피 |
| 가끔 사용 + 종류 많음 | **Soft (TSoftObjectPtr) + Primary Asset** | 메모리 효율 |
| DLC / MOD | Soft + 동적 LoadPrimaryAsset | 확장 가능 |

## 7. Baseline Grep 의무

함정 키워드: `TSoftObjectPtr` / `FStreamableHandle` / `UAssetManager` / `Cooked` / `LOD` / `Bone-LOD` / `Nanite` / `PostLoad` / `BulkData`.

## 8. 거부 조건

- 호스트 Component — `ue-components-specialist`
- Actor / Pawn — `ue-gameframework-specialist`
- 자산 안 코드 (런타임 평가기 등) — 해당 specialist

## 9. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-animation]] · [[sources/ue-agent-components]]
- 정책 권위: [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-ref-deep-assetloading]] · [[sources/ue-ref-deep-assetoptimization]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 10 절. 10 자산 결정 + SpawnActor 4단 + 5대 최적화 + Soft/Hard 매트릭스 |
