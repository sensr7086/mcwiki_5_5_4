---
name: asset-optimization-policy
description: 🎯 어셋 최적화 5대 영역 — 60fps + 메모리 한계 회피 표준. (§1) SkeletalMesh Bone LOD (§2) StaticMesh LOD + 5.x Nanite (§3) Actor Merging 4종 (HISM/Mesh Merge/HLOD/WorldPartition HLOD) (§4) Audio Culling (Attenuation/Concurrency/Significance) (§5) Niagara Quality Scaling (EffectType + 품질 레벨 5종 매트릭스). 모든 자산 멤버 + 다수 NPC 환경 + 60fps 검증 시.
---

# 12. 어셋 최적화 정책 — Mesh LOD / Bone LOD / Actor Merging / Audio Culling / Niagara Scalability

> 본 인덱스는 **모든 sub-skill 의 어셋 최적화 5대 영역 통합 정책** — 자산이 메모리 + GPU + CPU 에 미치는 영향 최소화.
> **요지**: **로딩 / 렌더링 / 시뮬 비용은 자산 자체의 설정으로 결정** — 최적화는 **자산 단위 의무**.

---

## 0. 본 정책의 적용 범위

| 영역 | 영향 sub-skill | 책임 |
|------|---------------|------|
| **§1 SkeletalMesh Bone LOD** | `AssetClasses/Mesh` + `Components/MeshComponents` | 본 줄임 + Skin Weight 단순화 |
| **§2 StaticMesh LOD** | `AssetClasses/Mesh` + `Components/MeshComponents` | ScreenSize + 폴리곤 감축 + 5.x Nanite |
| **§3 Actor Merging** | `AssetClasses/Mesh` + `Components/MeshComponents` + `GameFramework/World` | 드로우콜 절감 + HISM/HLOD |
| **§4 Audio Culling** | `AssetClasses/Audio` + `Components/AudioComponent` | 거리 기반 비활성 + Concurrency |
| **§5 Niagara Scalability** | `Niagara` + `AssetClasses/VFX` + `Components/ParticleComponents` | 품질 레벨별 Spawn Rate Scale |

> **본 5대 영역은 모든 게임의 60fps 유지 + 메모리 한계 + GPU 한계 회피의 90% 책임**.

---

## 1 ~ 5 깊이 자료 — [`references/AssetOptimizationDeep.md`](./references/AssetOptimizationDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인은 통합 매트릭스 + 체크리스트 / 깊이는 reference.

| § | 영역 | 핵심 룰 | reference |
|---|------|---------|-----------|
| 1 | **SkeletalMesh Bone LOD** | `USkeletalMeshLODSettings` + `BonesToRemove` (LOD 별 70/50/30/15%) + `BonesToPrioritize` (head/hand/weapon_socket/IK) + `LODHysteresis 0.05` + 5.x `SkinCacheUsage` | [`§1`](./references/AssetOptimizationDeep.md#1-skeletalmesh-bone-lod-정책) |
| 2 | **StaticMesh LOD** | ScreenSize 표준 1.0/0.5/0.25/0.1/0.05 + `bAutoComputeLODScreenSize=true` + `MinLOD` 플랫폼별 + 5.x **Nanite vs Traditional 결정 매트릭스** (Static + 정적 콜리전 = Nanite 의무) | [`§2`](./references/AssetOptimizationDeep.md#2-staticmesh-lod-정책) |
| 3 | **Actor Merging** | 4종 결정 트리 — HISM (동일 메시 100+) / Mesh Merge (작은 영역 — Editor) / HLOD (큰 영역 — 4.x) / 5.x **WorldPartition HLOD** (오픈 월드 자동) | [`§3`](./references/AssetOptimizationDeep.md#3-actor-merging-정책-드로우콜-절감) |
| 4 | **Audio Culling** | Attenuation `MaxDistance + FalloffDistance` (1차 컬링) + Concurrency `MaxCount + StopFarthest` (16→4) + SoundMix Volume Mute + Significance 통합 | [`§4`](./references/AssetOptimizationDeep.md#4-audio-culling-정책-거리-기반-비활성) |
| 5 | **Niagara Quality Scaling** | **모든 NiagaraSystem = `UNiagaraEffectType` 지정 의무** + 품질 레벨 5종 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2 SpawnCountScale) + Pool `ENCPoolMethod::AutoRelease` + `Scalability::SetQualityLevels` | [`§5`](./references/AssetOptimizationDeep.md#5-niagara-quality-scaling-정책) |

---

## 6. 모든 영역 통합 — 캐릭터 표준 매트릭스

> **다수 NPC 환경 (50+ 캐릭터) 표준 최적화 조합**:

| 항목 | LOD 0 (가까움) | LOD 1 | LOD 2 | LOD 3 (멀리) |
|------|---------------|-------|-------|-------------|
| **SkeletalMesh Bone** | 100% (모든 본) | 70% (손가락 X) | 50% (보조 본 X) | 30% (Cloth X) |
| **SkinCacheUsage** | Enabled | Auto | Disabled | Disabled |
| **AnimationTickOption** | AlwaysTickPoseAndRefreshBones | OnlyTickPoseWhenRendered | OnlyTickMontages | AlwaysSkipPostProcess |
| **URO** | OFF | ON (Rate=4) | ON (Rate=8) | ON (Rate=15) |
| **PhysicsAsset** | Full | Full | Simple | None (정적) |
| **Niagara Spawn** | 1.0 | 0.7 | 0.4 | 0.0 (Cull) |
| **Audio** | 3D + Concurrency | 3D + 거리 감쇠 | 거리 컬링 | OFF |
| **NetUpdateFrequency** | 33Hz | 10Hz | 2Hz | 1Hz |
| **Capsule Overlap** | 활성 | 활성 | 비활성 | 비활성 |

---

## 7. 함정 & 안티패턴 (15종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | SkeletalMesh LODSettings 자산 미지정 | USkeletalMeshLODSettings 의무 — Bone LOD / Hysteresis |
| 2 | BonesToPrioritize 미지정 — LOD 4 에서 head 까지 제거 | head / hand / weapon_socket 의무 |
| 3 | StaticMesh LOD ScreenSize 임의 (0.8 / 0.4 / 0.2) | 표준 (0.5 / 0.25 / 0.1 / 0.05) |
| 4 | 5.x Nanite + Skin (SkeletalMesh) 시도 | Nanite = Static 만. SkeletalMesh = Traditional LOD |
| 5 | HISM 안 사용 + 동일 메시 100개 Spawn | InstancedFoliageActor 또는 HISM 자동화 |
| 6 | Mesh Merge 후 Material Atlas 적용 안 함 | bMergeMaterials = true 의무 |
| 7 | HLOD 빌드 안 함 | Build > Build HLOD 의무 (큰 맵) |
| 8 | 5.x WorldPartition + HLOD 비활성 | WP = HLOD 의무 |
| 9 | Audio Attenuation 미지정 (모든 Sound Global) | MaxDistance + FalloffDistance 의무 |
| 10 | Concurrency 미지정 + 발사음 16개 동시 재생 | MaxCount = 4 + StopFarthest |
| 11 | NiagaraSystem EffectType 미지정 | EffectType 의무 — Cull / Scaling |
| 12 | Niagara Mobile 빌드 + GPU Sim + Bounds 자동 | GPU Bounds 수동 (FixedBounds) |
| 13 | Quality Level 변경 안 됨 (Settings 메뉴 X) | UGameUserSettings + Scalability API |
| 14 | LOD Hysteresis 0.0 — 거리 변경 시 LOD 떨림 | 0.05 (5% 마진) 의무 |
| 15 | 🚨 다수 NPC 환경 + Significance 통합 안 함 | Significance Manager + 위 5대 영역 모두 |

---

## 8. 체크리스트 (모든 게임 표준)

### 8.1 SkeletalMesh
- [ ] USkeletalMeshLODSettings 자산 할당
- [ ] LOD 5단계 정의 (ScreenSize 1.0/0.5/0.25/0.1/0.05)
- [ ] BonesToRemove 정의 (LOD 별 본 비율 100/70/50/30/15%)
- [ ] BonesToPrioritize 정의 (head / hand / weapon_socket / IK)
- [ ] LODHysteresis = 0.05
- [ ] SkinCacheUsage LOD 별 결정

### 8.2 StaticMesh
- [ ] LOD 5단계 ScreenSize 표준 (1.0/0.5/0.25/0.1/0.05)
- [ ] bAutoComputeLODScreenSize = true
- [ ] MinLOD 플랫폼별 (Mobile = 2)
- [ ] 5.x Nanite 활성 (Static + 정적 콜리전)

### 8.3 Actor Merging
- [ ] 동일 메시 100+ = HISM / Foliage
- [ ] 큰 영역 (구역) = HLOD 빌드
- [ ] 5.x 오픈 월드 = WorldPartition HLOD

### 8.4 Audio
- [ ] 모든 3D Sound = Attenuation 의무
- [ ] 자주 재생 SFX = Concurrency MaxCount
- [ ] BGM = SoundMix (메뉴 시 죽임)
- [ ] 환경음 = Significance 통합

### 8.5 Niagara
- [ ] 모든 NiagaraSystem = EffectType 의무
- [ ] Quality Level 별 SpawnCountScale 정의
- [ ] Pool (`ENCPoolMethod::AutoRelease`) 의무
- [ ] Mobile = GPU Bounds 수동

### 8.6 통합
- [ ] 다수 NPC 환경 = Significance Manager + 5대 영역 모두 통합
- [ ] AI vs Player 분리 매트릭스 ([`PawnCharacter §6.9`](../skills/GameFramework/references/PawnCharacter.md))
- [ ] **Cooked Build (Development)** `stat unit` / `stat fps` 검증

---

## 9. sub-skill 적용 매트릭스

| sub-skill | 적용 §|
|-----------|------|
| [`AssetClasses/Mesh`](../skills/AssetClasses/references/Mesh.md) | §1 Bone LOD + §2 StaticMesh LOD + §3 Actor Merging |
| [`Components/MeshComponents`](../skills/Components/references/MeshComponents.md) | §1 + §2 + §3 + URO 통합 |
| [`AssetClasses/Audio`](../skills/AssetClasses/references/Audio.md) | §4 Audio Culling |
| [`Components/AudioComponent`](../skills/Components/references/AudioComponent.md) | §4 + Significance 통합 |
| [`AssetClasses/VFX`](../skills/AssetClasses/references/VFX.md) | §5 Niagara Scalability |
| [`Niagara`](../skills/Niagara/SKILL.md) | §5 + Pool + EffectType |
| [`Components/ParticleComponents`](../skills/Components/references/ParticleComponents.md) | §5 Pool 사용 |
| [`Significance`](../skills/Significance/SKILL.md) | §1-§5 모두 통합 진입점 |
| [`GameFramework/PawnCharacter`](../skills/GameFramework/references/PawnCharacter.md) | §1 + §6 통합 매트릭스 (§6 최적화 10종) |
| [`GameFramework/World`](../skills/GameFramework/references/World.md) | §3 HLOD + 5.x WorldPartition |

---

## 10. 관련 문서

- 🎯 [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) — 어셋 로드 정책 (PreLoad)
- 🚨 [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) — 프로파일링 스코프 (Tick / 콜백)
- 🚨 [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) — 등록 패턴 (Significance)
- [`Significance`](../skills/Significance/SKILL.md) — USignificanceManager 통합 (§4 Audio Culling + §5 Niagara Cull)
- [`AssetClasses/SKILL.md`](../skills/AssetClasses/SKILL.md) — 자산 카테고리 메인
- [`Components/SKILL.md`](../skills/Components/SKILL.md) — 컴포넌트 카테고리 (페어)

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **5대 어셋 최적화 정책 통합** — (1) **SkeletalMesh Bone LOD** USkeletalMeshLODSettings + FBoneFilter + BonesToRemove + BonesToPrioritize + WeightOfPrioritization + LODHysteresis + SkinCacheUsage (5.x) + LOD 5단계 표준 매트릭스. (2) **StaticMesh LOD** ScreenSize 표준 (1.0/0.5/0.25/0.1/0.05) + 5.x Nanite vs Traditional 결정 매트릭스 + AutoComputeLODScreenSize + MinLOD 플랫폼별. (3) **Actor Merging** 4종 비교 (HISM / Mesh Merge / HLOD / 5.x WorldPartition HLOD) + 결정 트리 + FMeshMergingSettings + MergeComponentsToStaticMesh API. (4) **Audio Culling** Attenuation MaxDistance + Concurrency MaxCount 5종 ResolutionRule + SoundMix Volume Mute + Significance 통합 + Audio Engine MaxChannels. (5) **Niagara Quality Scaling** UNiagaraEffectType + FNiagaraSystemScalabilitySettings + 품질 레벨 5종 매트릭스 (Cinematic/High/Medium/Low/Mobile) + ENiagaraSignificanceHandling 4종 + Pool 통합 + Scalability API. **§6 통합 매트릭스** (다수 NPC LOD 5단계 + 9개 항목). 함정 15종 + 6대 체크리스트 + sub-skill 적용 매트릭스 10종. |
