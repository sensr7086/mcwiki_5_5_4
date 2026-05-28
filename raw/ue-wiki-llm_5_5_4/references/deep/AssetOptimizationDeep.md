---
name: asset-optimization-deep
description: 어셋 최적화 5대 영역 깊이 자료 — SkeletalMesh Bone LOD + StaticMesh LOD + Actor Merging (HISM/HLOD/WorldPartition) + Audio Culling (Attenuation/Concurrency) + Niagara Quality Scaling. 각 영역 상세 코드/매트릭스/결정 트리.
---

# Asset Optimization Policy — Deep Reference (§1~§5)

> 본 문서는 [`12_AssetOptimizationPolicy.md`](../12_AssetOptimizationPolicy.md) 의 §1~§5 깊이 자료. 메인 문서는 §0 적용 범위 + §6 통합 매트릭스 + §7 함정 + §8 체크리스트 + §9 sub-skill 적용 매트릭스. 본 reference 는 5대 영역 상세 코드/매트릭스.

---

## 1. SkeletalMesh Bone LOD 정책

### 1.1 핵심 — 거리에 따라 본 수 자동 감소

> **`USkeletalMeshLODSettings`** = LOD 별 본 처리 정의. 메시와 페어 자산 — **본 수 = 직접 CPU + GPU 비용**.

```cpp
// SkeletalMeshLODSettings.h:29 — 본 필터
struct FBoneFilter
{
    UPROPERTY(EditAnywhere)
    bool bExcludeSelf;     // 본 자체 제거

    UPROPERTY(EditAnywhere)
    FName BoneName;
};

// SkeletalMeshLODSettings.h:53 — LOD 별 그룹 설정
struct FSkeletalMeshLODGroupSettings
{
    // LOD 에서 제거할 본
    UPROPERTY(EditAnywhere)
    TArray<FBoneFilter> BoneList;

    // 우선 유지할 본 (얼굴 / 손 / 무기 본)
    UPROPERTY(EditAnywhere)
    TArray<FName> BonesToPrioritize;

    // BonesToPrioritize 가중치
    UPROPERTY(EditAnywhere)
    float WeightOfPrioritization;

    // LOD Hysteresis (전환 떨림 방지)
    UPROPERTY(EditAnywhere)
    float LODHysteresis;
};

// SkeletalMeshLODSettings.h:123
class USkeletalMeshLODSettings : public UDataAsset
{
    UPROPERTY()
    TArray<FSkeletalMeshLODGroupSettings> LODGroups;
};
```

### 1.2 표준 본 LOD 설정 (캐릭터 5단계)

| LOD | ScreenSize | Bone 비율 | BonesToRemove | BonesToPrioritize |
|-----|-----------|-----------|---------------|-------------------|
| **LOD 0** (가장 가까움) | 1.0 | 100% (모든 본) | 없음 | spine_03 / head / hand_l/r / weapon_socket |
| **LOD 1** | 0.5 | 70% | 손가락 본 (Phalanx) | 위 + foot_l/r |
| **LOD 2** | 0.25 | 50% | 손가락 + 발가락 + 보조 본 (twist_*) | 위 |
| **LOD 3** | 0.1 | 30% | 위 + IK 본 + Cloth 본 | head + spine_01 |
| **LOD 4** (가장 멀리) | 0.05 | 15% | 위 + 표정 본 (face_*) + 보조 본 | spine_01 (최소) |

```cpp
// 사용 — SkeletalMesh 측 LODSettings 자산 할당
SkeletalMesh->LODSettings = LoadObject<USkeletalMeshLODSettings>(...);
```

### 1.3 BonesToPrioritize 의무 적용

> **반드시 보존해야 할 본** — 시각적으로 중요한 본은 LOD 4 까지 살림.

```cpp
// 표준 BonesToPrioritize
TArray<FName> EssentialBones = {
    TEXT("head"),              // 얼굴 (가장 먼저 보임)
    TEXT("hand_l"),            // 무기 / 도구
    TEXT("hand_r"),
    TEXT("weapon_socket"),     // 무기 부착
    TEXT("ik_target_*"),       // IK 타겟 (제거 시 IK 깨짐)
};

// 가중치 — 1.0 ~ 5.0 (높을수록 보존)
LODGroupSettings.WeightOfPrioritization = 3.0f;
```

### 1.4 LOD Hysteresis (전환 떨림 방지)

```cpp
// 캐릭터 거리 변경 시 LOD 떨림 회피
LODGroupSettings.LODHysteresis = 0.05f;   // 5% 마진
```

### 1.5 SkinCacheUsage (5.x — GPU 스킨 캐시)

```cpp
// SkinCache 활성 (5.x) — 거리 가까울 때만 사용 (LOD 0~1)
UPROPERTY(EditAnywhere)
ESkinCacheUsage SkinCacheUsage = ESkinCacheUsage::Auto;

// LOD 별 SkinCache 결정 매트릭스
// LOD 0 = ESkinCacheUsage::Enabled (Niagara 등 GPU 시뮬 사용)
// LOD 1 = ESkinCacheUsage::Auto
// LOD 2~ = ESkinCacheUsage::Disabled (메모리 절감)
```

### 1.6 컴포넌트 측 LOD 제어

```cpp
// 거리 기반 자동 LOD 위임 (기본)
SkelMeshComp->bComponentUseFixedSkelBounds = false;
SkelMeshComp->ForcedLodModel = 0;   // 0 = 자동

// 강제 LOD (디버그 / 멀리)
SkelMeshComp->ForcedLodModel = 3;   // LOD 3 강제

// MinLOD (Quality Level 5.x)
SkelMeshComp->MinLodModel = 1;       // 모바일 = LOD 1 부터
```

---

## 2. StaticMesh LOD 정책

### 2.1 ScreenSize 임계값 표준

> **ScreenSize** = 화면 안 메시가 차지하는 비율 (0~1). LOD 전환 기준.

| LOD | 권장 ScreenSize | 폴리곤 비율 (vs LOD 0) | 사용 케이스 |
|-----|---------------|--------------------|-----------|
| **LOD 0** | 1.0 | 100% | 가장 가까움 (5m 이내) |
| **LOD 1** | 0.5 | 50% | 중거리 (5~15m) |
| **LOD 2** | 0.25 | 25% | 멀리 (15~50m) |
| **LOD 3** | 0.1 | 10% | 매우 멀리 (50~100m) |
| **LOD 4** | 0.05 | 5% | 풍경 (100m+) |

### 2.2 5.x Nanite vs Traditional LOD 결정

| 메시 종류 | 권장 |
|----------|------|
| **Static Mesh + 정적 콜리전** | **Nanite 활성** (LOD 자동 — 폴리곤 무관) |
| **Static Mesh + Skin** | Nanite X — Traditional LOD |
| **Static Mesh + Movable + Physics Simulate** | Nanite X — Traditional LOD |
| **Static Mesh + Translucent / Masked Material** | 5.x Nanite (Masked 지원) / 4.x Traditional |
| **Static Mesh + 폴리곤 < 1,000** | LOD 무관 (작은 메시는 LOD 안 만듦) |
| **Foliage (잎사귀)** | 5.x Nanite / Traditional LOD + Imposter |

### 2.3 Auto LOD vs Manual LOD

```cpp
// StaticMesh.h:712 — 자동 ScreenSize 계산
UPROPERTY(EditAnywhere)
uint8 bAutoComputeLODScreenSize : 1;

// 자동 = true (대부분 권장)
StaticMesh->SetAutoComputeLODScreenSize(true);
```

### 2.4 MinLOD (플랫폼별 강제)

```cpp
// MinLOD = 모바일 / 저사양에서 LOD 0 안 사용
UPROPERTY()
FPerPlatformInt MinLOD;

// 예: PC = 0 / Mobile = 2 / Switch = 1
```

### 2.5 폴리곤 감축 매트릭스 (Auto Generate)

```
Editor — Static Mesh > LOD Group > Reduction Settings
- Percent Triangles: 50%/25%/10%/5% (LOD 1/2/3/4)
- Percent Vertices: 위 동일
- MaxDeviation: 자동 (Hausdorff 거리)
- WeldingThreshold: 0.0 (Vertex 합치기)
- HardAngleThreshold: 80 (Smoothing 그룹 결정)
```

### 2.6 컴포넌트 측 강제 LOD

```cpp
StaticMeshComp->SetForcedLodModel(2);   // 1-based (LOD 1)
StaticMeshComp->MinLOD = 1;
StaticMeshComp->bOverrideMinLOD = false;
```

---

## 3. Actor Merging 정책 (드로우콜 절감)

### 3.1 4종 Merging 방법 비교

| 방법 | 의미 | 장점 | 단점 |
|------|------|------|------|
| **HISM (Hierarchical ISM)** | 동일 메시 자동 인스턴스 | 드로우콜 1번 / N개 | 본 충돌 별도 |
| **Mesh Merge (Editor)** | 여러 메시 → 1 메시 | 드로우콜 + 메모리 | LOD 재생성 / Material 합치기 |
| **HLOD (Hierarchical LOD)** | 거리 멀면 자동 통합 메시 | 자동 + 효율 | 빌드 시간 / 메모리 |
| **5.x WorldPartition HLOD** | Grid 기반 자동 HLOD | 오픈 월드 표준 | WP 의존 |

### 3.2 HISM 자동화 (가장 흔함)

```cpp
// 게임 시작 시 동일 StaticMesh 모든 Actor → HISM 변환
// 5.x — Foliage Tool / Procedural Foliage 가 자동

// 수동 코드
UHierarchicalInstancedStaticMeshComponent* HISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
HISM->SetStaticMesh(SharedMesh);
HISM->RegisterComponent();

// 인스턴스 추가
for (const auto& Transform : Transforms)
{
    HISM->AddInstance(Transform);
}
```

### 3.3 Mesh Merge (Editor 도구)

```cpp
// 5.x — Window > Developer Tools > Merge Actors
// 또는 코드 (Editor 전용)
#if WITH_EDITOR
#include "MeshMerge/MeshMergingSettings.h"

FMeshMergingSettings Settings;
Settings.bMergeMaterials = true;       // Material 합치기
Settings.bGenerateLightMapUV = true;
Settings.MergeType = EMeshMergeType::MeshMergeType_Default;

UStaticMesh* MergedMesh = nullptr;
TArray<UPrimitiveComponent*> ComponentsToMerge = ...;
MeshUtilities.MergeComponentsToStaticMesh(ComponentsToMerge, World, Settings, ..., MergedMesh, ...);
#endif
```

### 3.4 HLOD (Hierarchical LOD — 4.x 표준)

> **거리 멀면 여러 메시를 1개 단순 메시로 통합** — 자동.

```ini
; DefaultEngine.ini
[/Script/Engine.HierarchicalLODSetup]
HLODSetupAsset=/Engine/EditorResources/HLODProxyDefault.HLODProxyDefault

; HLOD Level 0: 거리 5,000 — Material Atlas + 폴리곤 50%
; HLOD Level 1: 거리 20,000 — 단일 Material + 폴리곤 10%
; HLOD Level 2: 거리 50,000 — Imposter Sprite
```

### 3.5 5.x WorldPartition HLOD (오픈 월드 표준)

```cpp
// WorldPartition/HLOD/HLODBuilder.h
class UWorldPartitionHLODBuilder : public UObject
{
    // Grid 기반 자동 HLOD
    // - HLOD0: Cell 합치기 (200m)
    // - HLOD1: Layer 합치기 (1km)
    // - HLOD2: Region 합치기 (10km)
};

// 활성 — Project Settings > World Partition > HLOD
// 빌드 — Build > Build HLOD
```

### 3.6 Actor Merging 결정 트리

```
같은 메시 100+ 개?
├── Foliage / Procedural 가능 → InstancedFoliageActor 자동
├── 정적 배치 → HISM 컴포넌트
└── 동적 (런타임 추가) → ISM (단일 LOD)

여러 종류 메시 (도시 / 건물)?
├── 작은 영역 (단일 빌딩) → Mesh Merge (Editor)
├── 중간 영역 (블록) → HLOD Level 0
├── 큰 영역 (구역) → HLOD Level 1~2
└── 오픈 월드 5.x → WorldPartition HLOD (자동)
```

---

## 4. Audio Culling 정책 (거리 기반 비활성)

### 4.1 Attenuation MaxDistance (1차 컬링)

```cpp
// USoundAttenuation 자산
class USoundAttenuation
{
    FSoundAttenuationSettings Attenuation;
    // - DistanceAlgorithm: NaturalSound / Inverse / Logarithmic
    // - AttenuationShape: Sphere
    // - InnerRadius: 100   (감쇠 시작)
    // - FalloffDistance: 5000   (Volume = 0 거리)
};

// 거리 > InnerRadius + FalloffDistance → Volume = 0
// 거리 > 50m + 마진 → Sound 자동 비활성 (Audio Engine)
```

### 4.2 Concurrency MaxCount (동시 재생 제한)

```cpp
// USoundConcurrency 자산
USoundConcurrency* WeaponConc = ...;
WeaponConc->Concurrency.MaxCount = 4;   // 4개 동시
WeaponConc->Concurrency.ResolutionRule = EMaxConcurrentResolutionRule::StopFarthest;

// 16개 발사음 → 가장 먼 4개 자동 정지
```

### 4.3 Sound Class Volume Mute (그룹 단위)

```cpp
// 메뉴 열면 BGM 죽임 (USoundMix)
USoundMix* MenuMix = ...;
// MenuMix 안 SoundClassEffects 정의
// - MusicSoundClass.VolumeMultiplier = 0.2f
// - SFXSoundClass.VolumeMultiplier = 0.5f

UGameplayStatics::PushSoundMixModifier(this, MenuMix);
```

### 4.4 거리 기반 활성/비활성 (수동)

```cpp
// AudioComponent Tick 안 거리 검사 (매 프레임 회피)
// → Significance Manager 통합

void AAudioActor::BeginPlay()
{
    Super::BeginPlay();
    if (auto* SigMgr = USignificanceManager::Get<USignificanceManager>(GetWorld()))
    {
        SigMgr->RegisterObject(this, TEXT("Audio"),
            [](USignificanceManager::FManagedObjectInfo* Info, const FTransform& Viewer)
            {
                FVector Loc = Cast<AActor>(Info->GetObject())->GetActorLocation();
                return FMath::InvSqrt(FVector::DistSquared(Loc, Viewer.GetLocation()));
            },
            USignificanceManager::EPostSignificanceType::Sequential,
            [](USignificanceManager::FManagedObjectInfo* Info, float Old, float New, bool)
            {
                auto* Actor = Cast<AAudioActor>(Info->GetObject());
                if (New < 0.01f && Actor->AudioComp->IsPlaying())
                {
                    Actor->AudioComp->Stop();   // 매우 멀면 정지
                }
                else if (New > 0.05f && !Actor->AudioComp->IsPlaying())
                {
                    Actor->AudioComp->Play();
                }
            });
    }
}
```

### 4.5 Audio Engine 자동 Voice Limit

```ini
; DefaultEngine.ini
[Audio]
MaxChannels=64                ; 동시 64 채널
MaxChannelsForMobile=32

; 거리 멀면 자동 Stealing (가장 조용한 / 멀리)
```

### 4.6 Audio Culling 결정 트리

```
사운드 종류?
├── BGM / 글로벌 → SoundMix VolumeMute (UI 열면 줄임)
├── 3D SFX (발사 / 발자국) → Attenuation MaxDistance + Concurrency
├── 환경음 (앰비언트) → Significance + 거리 기반 활성/비활성
└── 다이얼로그 → Priority + Concurrency StopLowestPriority
```

---

## 5. Niagara Quality Scaling 정책

### 5.1 UNiagaraEffectType — Performance Baseline

> **자산 — Niagara System 마다 EffectType 지정** — 성능 한계 정의 + 자동 Cull/Scale.

```cpp
// 가상 — Plugin 안 NiagaraEffectType.h
class UNiagaraEffectType : public UObject
{
    // Performance Baseline — 목표 시뮬 시간
    UPROPERTY(EditAnywhere)
    FNiagaraSystemScalabilitySettings DefaultScalability;

    // 품질 레벨별 (Cinematic / High / Medium / Low / Mobile)
    UPROPERTY(EditAnywhere)
    TArray<FNiagaraSystemScalabilityOverride> ScalabilityOverrides;

    // Significance 처리
    UPROPERTY(EditAnywhere)
    ENiagaraSignificanceHandling SignificanceHandling;

    // Performance Baseline (실측)
    UPROPERTY()
    FNiagaraPerfBaselineStats PerfBaselineStats;
};

struct FNiagaraSystemScalabilitySettings
{
    // Cull
    bool bCullByDistance;
    float MaxDistance;             // 5,000 ~ 50,000

    bool bCullByMaxCountPerSystem;
    int32 MaxSystemInstances;      // 글로벌 인스턴스 한계

    bool bCullByMaxTimeWithoutRender;
    float MaxTimeWithoutRender;     // 안 보이면 N초 후 Cull

    // Spawn Rate Scale
    bool bScaleEmitterSpawnCounts;
    float SpawnCountScale;          // 0.0~1.0 (Mobile = 0.5)

    // Update Frequency
    bool bScaleEmitterUpdateRate;
    float UpdateRateScale;          // 0.0~1.0 (Mobile = 0.5 = 2배 느림)
};
```

### 5.2 품질 레벨별 표준 매트릭스

| 품질 | SpawnCountScale | UpdateRateScale | MaxDistance | MaxSystemInstances |
|------|----------------|-----------------|-------------|--------------------|
| **Cinematic** | 1.0 | 1.0 | 100,000 | 1,000 |
| **High** | 1.0 | 1.0 | 30,000 | 500 |
| **Medium** | 0.7 | 0.7 | 15,000 | 200 |
| **Low** | 0.4 | 0.5 | 8,000 | 100 |
| **Mobile** | 0.2 | 0.3 | 5,000 | 50 |

### 5.3 EffectType 사용 패턴 (모든 Niagara System)

```cpp
// 모든 NiagaraSystem 자산에 EffectType 의무
NiagaraSystem->EffectType = LoadedEffectType;

// 표준 EffectType 자산
// - EffectType_Hero       (Player 효과 — 1.0 / 1.0 / Always)
// - EffectType_Enemy      (NPC 효과 — Significance)
// - EffectType_Environment (배경 — 거리 컬링 강함)
// - EffectType_HitEffect  (충돌 효과 — MaxCount=20)
// - EffectType_BGFX       (배경 입자 — Cull 강함)
```

### 5.4 ENiagaraSignificanceHandling

```cpp
enum class ENiagaraSignificanceHandling : uint8
{
    EarliestCullDistance,        // 거리 컬링 (표준)
    EarliestActorBased,           // Significance Manager 통합
    EarliestKill,                 // Kill (재사용 X)
    EarliestKeepActive,           // 항상 활성
};
```

### 5.5 Quality Level 런타임 전환

```cpp
// 5.x — Project Settings > Engine > Scalability
// scalabilityquality 콘솔 명령
// sg.EffectsQuality 0~4 (Low~Cinematic)

// 코드
Scalability::FQualityLevels Levels = Scalability::GetQualityLevels();
Levels.EffectsQuality = 1;   // Low
Scalability::SetQualityLevels(Levels);
Scalability::SaveState(GGameUserSettingsIni);
```

### 5.6 Niagara Pool 통합

```cpp
// Pool + EffectType + Significance 통합
UNiagaraComponent* PooledNC = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    this, NiagaraSys, Location, Rot, Scale,
    /*bAutoDestroy=*/ true,
    /*bAutoActivate=*/ true,
    ENCPoolMethod::AutoRelease   // ⭐ Pool
);
// Cooked Build 첫 Spawn = Pool 안 인스턴스 사용 (히칭 회피)
```

### 5.7 Niagara 함정

| # | 함정 | 정답 |
|---|------|-----|
| 1 | NiagaraSystem 의 EffectType 미지정 | Significance / Cull / Scaling 모두 안 됨 — 의무 |
| 2 | Pool 안 사용 + 매 프레임 Spawn | `ENCPoolMethod::AutoRelease` 의무 |
| 3 | Mobile 빌드에 GPU Sim 사용 + Bounds 자동 | GPU Bounds 수동 설정 의무 |
| 4 | Quality Level 안 변경 가능 (Settings 메뉴 X) | UGameUserSettings + Scalability::SetQualityLevels |

---

