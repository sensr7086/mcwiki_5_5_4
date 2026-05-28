---
name: assetclasses-main
description: Tier 1 AssetClasses 메인 — Mesh + Material + Texture + Animation + Audio + Data + VFX + Camera + Physics + AssetUserData 10개 sub-skill. Components 의 페어 카테고리 (호스트 vs 자산). 컴포넌트 ↔ 자산 페어 매트릭스 + 자산 라이프사이클 (PostLoad / Cooking / DDC / BulkData) + Cooked vs Uncooked 차이 + 자산 메타 확장 (UAssetUserData).
---

# AssetClasses — 자산 클래스 (UStaticMesh / USkeletalMesh / UMaterial / UTexture / etc.)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/` + `Materials/` + `Sound/` + `Animation/` + `PhysicsEngine/` + Plugin (Niagara)
> **요지**: **컴포넌트가 사용하는 UObject 자산 클래스** — Components 가 호스트 (런타임 인스턴스), AssetClasses 가 자산 (디스크 데이터). 모든 자산은 `UObject` 자손이며 `.uasset` 디스크 파일로 저장됨. **Components ↔ AssetClasses 페어 구조** 가 게임 시스템의 근간.
> **카테고리**: `[AssetClasses]` — **Components 의 페어** (자산 데이터 측면).

---

## 🚨 모든 AssetClasses sub-skill 의무 정책 (본문 시작부 의무 블록)

| 정책 | 적용 |
|------|------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) | **🔥 가장 중요** — 모든 자산은 **Soft Reference 권장** + UAssetManager Primary Asset / Bundle / FStreamableManager 비동기 로드. **Constructor 안 어셋 로드 절대 금지**. 자주 사용 자산 = Match Start `PreloadPrimaryAssets(bLoadRecursive=true)` 표준. SpawnActor 히칭 4단 원인 이해 + Cooked Build 검증 의무. |
| 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) | 6대 정책 중 **GC 방어 + CDO** 직접 적용 — 자산 클래스의 멤버 (Mesh / Material / Texture 등) = `UPROPERTY()` + `TObjectPtr<>` / `TSoftObjectPtr<>`. CDO 변경 금지. |
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | PostLoad / Serialize / BeginCacheForCooked 등 무거운 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`. |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) | Asset 검색 = AssetRegistry 또는 UAssetManager Primary Asset Type 스캔 — `TObjectIterator<UStaticMesh>` 등 절대 금지. |
| [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) | 🛠 BulkData / DerivedDataCache / Cooked vs Uncooked / WITH_EDITORONLY_DATA 가드 — 자산은 에디터 전용 데이터 다수 보유. |

---

## 1. sub-skill 인덱스 (10개 + 메인)

| # | sub-skill | 위치 | 한 줄 요약 | 주요 페어 컴포넌트 |
|---|-----------|------|----------|------------------|
| 1 | [`Mesh`](./Mesh/SKILL.md) | `skills/AssetClasses/references/Mesh.md` | **UStaticMesh 2,543 + USkeletalMesh 3,248 + USkeleton 1,037 + UPhysicsAsset 444** — LOD 구조 + RenderData + Bulk Data + Lightmap UV + Nanite 5.x | `MeshComponents` (StaticMesh/SkeletalMesh/HISM/SplineMesh) |
| 2 | [`Material`](./Material/SKILL.md) | `skills/AssetClasses/references/Material.md` | **UMaterial 2,166 + UMaterialInstance 1,256 + UMaterialInterface 1,385** — Domain (Surface/PostProcess/Decal/Volume/UI) + ShadingModel + BlendMode + MaterialFunction + ParameterCollection + PSO Compile | `MeshComponents`(Material 슬롯) / `RenderingComponents`(Decal/PostProcess) / `LightComponents`(LightFunction) |
| 3 | [`Texture`](./Texture/SKILL.md) | `skills/AssetClasses/references/Texture.md` | **UTexture 2,228 + UTexture2D 397 + UTextureCube + UTextureRenderTarget2D + UVolumeTexture** — Compression Settings (BC1/BC5/BC7) + Mip Maps + LODGroup + Streaming + bForceMiplevelsToBeResident | Material (모든 컴포넌트가 간접 사용) / `RenderingComponents`(SceneCapture RenderTarget) |
| 4 | [`Animation`](./Animation/SKILL.md) | `skills/AssetClasses/references/Animation.md` | **UAnimSequence 1,001 + UAnimMontage 996 + UBlendSpace 966 + UAnimBlueprint 299 + UAnimInstance 1,776 + USkeleton 1,037** — Pose 키 / Curve / Notify / Blend / Layer | `MeshComponents`(SkeletalMesh) / `MovementComponents`(RootMotion) |
| 5 | [`Audio`](./Audio/SKILL.md) | `skills/AssetClasses/references/Audio.md` | **USoundBase 418 + USoundCue 379 + USoundWave 1,822 + USoundClass + USoundConcurrency + USoundMix + USoundAttenuation + MetaSounds (5.x)** | `AudioComponent` |
| 6 | [`Data`](./Data/SKILL.md) | `skills/AssetClasses/references/Data.md` | **UDataAsset 67 + UPrimaryDataAsset + UDataTable 552 + UCurveTable 342 + UCurveFloat / UCurveLinearColor** — 표 기반 데이터 / Bundle 메타 | 모든 게임 시스템 (PrimaryAsset 표준) |
| 7 | [`VFX`](./VFX/SKILL.md) | `skills/AssetClasses/references/VFX.md` | **UNiagaraSystem (Plugin) + UParticleSystem (Cascade legacy) + UVectorField** — Stack 모듈 / Data Interface / GPU Sim | `ParticleComponents` / `Niagara` |
| 8 | [`Camera`](./Camera/SKILL.md) | `skills/AssetClasses/references/Camera.md` | **UCameraShakeBase + UCameraAnimationSequence + UCameraModifier** — 5.x 카메라 셰이크 표준 | `CameraComponent` / `Controller`(PlayerCameraManager) |
| 9 | [`Physics`](./Physics/SKILL.md) | `skills/AssetClasses/references/Physics.md` | **UPhysicalMaterial + UPhysicsAsset 444 + UPhysicsConstraintTemplate** — Friction / Restitution / Density / Damping / Constraint Setup | `MeshComponents`(PhysicsAsset) / `PhysicsComponents` |
| 10 | [`AssetUserData`](./AssetUserData/SKILL.md) ⭐ | `skills/AssetClasses/AssetUserData/SKILL.md` | **UAssetUserData (Engine/AssetUserData.h:16) + IInterface_AssetUserData (:19)** — 자산 클래스 수정 없이 커스텀 메타 첨부 (StaticMesh / SkeletalMesh / Material / Texture / Sound / Physics / WorldSettings 10종 지원) | 모든 자산 + Mesh Components (인스턴스 메타) |

---

## 2. 자산 ↔ 컴포넌트 페어 매트릭스

> **모든 컴포넌트는 1개+ 자산을 참조** — 자산 변경이 컴포넌트의 시각·동작 결정.

| 컴포넌트 (호스트) | 주요 자산 (Asset) | 보조 자산 |
|------------------|------------------|----------|
| `UStaticMeshComponent` | `UStaticMesh` | `UMaterialInterface` (다중 슬롯), `UPhysicalMaterial`, `UTexture` (간접) |
| `USkeletalMeshComponent` | `USkeletalMesh` + `USkeleton` | `UAnimBlueprint` / `UAnimInstance`, `UPhysicsAsset`, `UMaterialInterface`, `UAnimSequence` (DefaultAnim) |
| `UInstancedStaticMeshComponent` | `UStaticMesh` | `UMaterialInterface` |
| `UDecalComponent` | `UMaterialInterface` (Domain=Decal) | `UTexture` (간접) |
| `UTextRenderComponent` | `UFont` | `UMaterialInterface` |
| `USceneCaptureComponent2D` | `UTextureRenderTarget2D` | `UMaterialInterface` (PostProcess) |
| `UPostProcessComponent` | `UMaterialInterface` (Domain=PostProcess) | `UTexture` |
| `UAudioComponent` | `USoundBase` (자손 — Cue/Wave/Class) | `USoundConcurrency`, `USoundAttenuation`, `USoundMix` |
| `UParticleSystemComponent` | `UParticleSystem` (legacy Cascade) | `UMaterialInterface`, `UTexture` |
| `UNiagaraComponent` | `UNiagaraSystem` (Plugin) | Data Interface 9종 (SkeletalMesh/StaticMesh/Curve/Texture 등) |
| `ULightComponent` | (Material 의 LightFunction) | `UTexture` (Light Profile IES) |
| `UCameraComponent` / `UCameraShakeSourceComponent` | `UCameraShakeBase` 자손 | `UCameraAnimationSequence` |
| `UPhysicsConstraintComponent` | `UPhysicsConstraintTemplate` | `UPhysicalMaterial` |
| `UWidget` (UMG) | `UTexture2D` (Brush), `UFont` | `UMaterialInterface` |

---

## 3. 자산 라이프사이클 (PostLoad / Cooking / Bulk Data)

> **자산 = 디스크 `.uasset` 파일** + 메모리 인스턴스. 일반 Actor / Component 와 다른 라이프사이클.

```
[디스크] .uasset 파일
  ↓
LoadPackage / LoadObject (FStreamableManager 가 호출)
  ↓
[1] Constructor                ── UObject 생성 (메모리 할당)
[2] Serialize(FArchive&)        ── 디스크 데이터 → 메모리 (Bulk Data 포함)
[3] PostLoad()                  ── ⚠️ 자산 특화 — 데이터 검증 / DDC / 플랫폼 변환 / 캐시 복원
[4] PostInitProperties()        ── 일반 UObject 표준
[5] FinishDestroy / BeginDestroy ── GC

[Cooking 시 — 에디터 전용]
  ↓ BeginCacheForCookedPlatformData(Platform)   ── 플랫폼별 캐시 생성 (Texture compress / Mesh DDC)
  ↓ ClearAllCachedCookedPlatformData             ── 종료 시 정리
  ↓ NeedsLoadForServer / IsEditorOnly             ── Cook 시 strip 결정
```

> **자세한 PostLoad / Cooking = [`CoreUObject/UObject`](../CoreUObject/references/UObject.md) §3 + [`CoreUObject/Cooking`](../CoreUObject/references/Cooking.md)**.

### 3.1 PostLoad — 자산 특화 의무

```cpp
// MyAsset.cpp
void UMyAsset::PostLoad()
{
    Super::PostLoad();
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyAsset::PostLoad);

    // ⚠️ 자산 데이터 검증 — 마이그레이션 / Default 적용
    if (Version < CurrentVersion)
    {
        MigrateData();
        Version = CurrentVersion;
    }

    // 의존 자산 동기 — Mesh 가 Material 참조 등
    if (DefaultMaterial)
    {
        DefaultMaterial->ConditionalPostLoad();   // 의존 자산도 PostLoad 보장
    }
}
```

### 3.2 BulkData (대용량 바이너리 — Texture / Mesh)

```cpp
// FBulkData = 4MB+ 큰 데이터 (이미지 픽셀 / 메시 정점) — UPROPERTY 안 됨
class UMyAsset : public UObject
{
    FByteBulkData ImageData;   // 직접 Serialize
    virtual void Serialize(FArchive& Ar) override
    {
        Super::Serialize(Ar);
        ImageData.Serialize(Ar, this);   // Async load 자동 + 메모리 매핑
    }
};
```

> **자세한 BulkData = [`CoreUObject/Serialization`](../CoreUObject/references/Serialization.md)**.

### 3.3 DerivedDataCache (DDC — 에디터 전용 캐시)

```cpp
// 비싼 변환 (Texture compress / Mesh tangents 계산) 결과를 DDC 에 캐시
// 에디터 전용 — 다음 로드 시 재사용
#if WITH_EDITOR
void UMyAsset::CacheDerivedData()
{
    FString KeyHash = ComputeDataHash();
    TArray<uint8> CachedData;
    if (GetDerivedDataCacheRef().GetSynchronous(*KeyHash, CachedData))
    {
        // 캐시 히트
    }
    else
    {
        // 변환 실행 + 저장
        TArray<uint8> NewData = ExpensiveTransform();
        GetDerivedDataCacheRef().Put(*KeyHash, NewData);
    }
}
#endif
```

---

## 4. Cooked vs Uncooked Build 차이

| 항목 | Editor / Uncooked | Cooked Build |
|------|-------------------|--------------|
| 자산 형식 | `.uasset` (Editor 메타 포함) | `.pak` (압축 + Editor 메타 strip) |
| BulkData 위치 | 별도 파일 또는 Inline | `.pak` 안 또는 메모리 매핑 |
| DDC | 활성 (에디터 캐시) | OFF (모두 사전 계산) |
| `WITH_EDITORONLY_DATA` 멤버 | 살아있음 | 컴파일 안 됨 |
| `BeginCacheForCookedPlatformData` | 호출됨 (Cook 명령 시) | 호출 안 됨 |
| `IsEditorOnly() = true` 자산 | 메모리 상주 | 자동 strip |
| StaticMesh LOD 데이터 | 모든 LOD + Editor 메타 | 플랫폼별 필요 LOD 만 |
| Texture | 원본 + Mip 모두 | 플랫폼별 압축 (Mobile = ASTC, PC = BC1~7) |

> **🚨 함정 — Editor PIE 에서 잘 동작하지만 Shipping 빌드에서 깨짐**:
> - `WITH_EDITORONLY_DATA` 안 가드 + Cooked 에서 컴파일 오류
> - `IsEditorOnly()` 자산을 런타임 코드가 참조 → Shipping 에서 nullptr
> - DDC 캐시 의존 코드 → Cooked 에 DDC 없음

---

## 5. 자산 ↔ 컴포넌트 변경 패턴 (런타임)

### 5.1 자산 변경 시 컴포넌트 갱신

```cpp
// 표준 패턴 — Setter 가 자동으로 컴포넌트 갱신
StaticMeshComp->SetStaticMesh(NewMesh);     // → MarkRenderStateDirty + 콜리전 갱신
SkelMeshComp->SetSkeletalMesh(NewMesh);     // → AnimBP 재초기화 + 본 매핑
AudioComp->SetSound(NewSound);              // → 재생 중지 후 재시작 (필요 시)
NiagaraComp->SetAsset(NewSystem);           // → 시뮬 재시작
DecalComp->SetDecalMaterial(NewMaterial);   // → MarkRenderStateDirty
```

### 5.2 Material 동적 인스턴스 (런타임 파라미터)

```cpp
// 인스턴스마다 다른 색상 / 데미지 효과 등
UMaterialInstanceDynamic* MID = MeshComp->CreateAndSetMaterialInstanceDynamic(0);
MID->SetVectorParameterValue(TEXT("Color"), FLinearColor::Red);
MID->SetScalarParameterValue(TEXT("DamageAmount"), 0.5f);
```

> **자세한 패턴 = [`AssetClasses/Material`](./Material/SKILL.md) + [`Render`](../../CLAUDE.md#4-🎨-render-렌더링) 카테고리**.

### 5.3 자산 비동기 변경 (히칭 회피)

```cpp
// ❌ 안티패턴 — 동기 로드 후 변경 (히칭)
UStaticMesh* NewMesh = LoadObject<UStaticMesh>(nullptr, *MeshPath);   // 첫 로드 시 히칭
MeshComp->SetStaticMesh(NewMesh);

// ✅ 정답 — Soft + Async
TSoftObjectPtr<UStaticMesh> SoftMesh(MeshPath);
FStreamableManager& SM = UAssetManager::GetStreamableManager();
LoadHandle = SM.RequestAsyncLoad(SoftMesh.ToSoftObjectPath(),
    FStreamableDelegate::CreateLambda([this, SoftMesh]()
    {
        if (IsValid(this) && MeshComp)
        {
            MeshComp->SetStaticMesh(SoftMesh.Get());
        }
    })
);
```

> **자세한 패턴 = 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md)**.

---

## 6. AssetClasses vs Components 차이 정리 (Cross-Reference)

| 항목 | `[Components]` | `[AssetClasses]` |
|------|----------------|------------------|
| 베이스 | `UActorComponent` (런타임 인스턴스) | `UObject` (디스크 자산) |
| 호스트 | Actor 안 부속 | UPackage (디스크 .uasset) |
| Spawn | `Actor->AddComponent` 또는 `CreateDefaultSubobject` | LoadObject / FStreamableManager |
| 라이프사이클 | OnRegister / BeginPlay / EndPlay / OnUnregister | Constructor / Serialize / **PostLoad** / BeginDestroy |
| 인스턴스 수 | 매 Actor 마다 | 1개 (모든 컴포넌트가 공유) |
| Replication | bReplicated + DOREPLIFETIME | 일반적으로 X (자산 자체는 클라/서버 동일) |
| Mobility | 의무 | 무관 (UObject) |
| Tick | PrimaryComponentTick | 없음 (Tick 불필요) |
| 6대 정책 적용 | 모두 적용 | **GC 방어 + CDO 만 직접** + 어셋 로드 정책 의무 |
| PostLoad 의무 | 일반 | **🔥 자산 특화 — 데이터 검증·마이그레이션·DDC** |
| Cooking | 일반 | **🔥 BeginCacheForCookedPlatformData / IsEditorOnly / WITH_EDITORONLY_DATA** |

---

## 7. cross-cutting 인덱스 (모두 Read 권장)

- 🎯 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) — **🔥 가장 중요** — Soft / Hard / FStreamableManager / UAssetManager Primary Asset / Bundle / PreLoad
- 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) — 6대 정책 (GC 방어 + CDO 직접 적용)
- 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — PostLoad / Serialize 등 무거운 콜백 스코프
- 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) — 자산 검색 = AssetRegistry / UAssetManager (TObjectIterator 금지)
- [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — 🛠 BulkData / DDC / WITH_EDITORONLY_DATA
- [`Components/SKILL.md`](../Components/SKILL.md) — Components 카테고리 (페어)
- [`AssetRegistry`](../AssetRegistry/SKILL.md) — IAssetRegistry / FAssetData / FARFilter (자산 검색)
- [`CoreUObject/UObject`](../CoreUObject/references/UObject.md) — UObject 베이스 + PostLoad
- [`CoreUObject/Serialization`](../CoreUObject/references/Serialization.md) — FArchive / FBulkData / Async Load
- [`CoreUObject/Cooking`](../CoreUObject/references/Cooking.md) — BeginCacheForCookedPlatformData

---

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | **`[AssetClasses]` 카테고리 신설** — 메인 SKILL.md + 9 sub-skill 분할안 (Mesh / Material / Texture / Animation / Audio / Data / VFX / Camera / Physics). 컴포넌트 페어 매트릭스 (15+ 컴포넌트 ↔ 자산) + 자산 라이프사이클 (PostLoad / Serialize / BulkData / DDC) + Cooked vs Uncooked Build 차이 + 자산 ↔ 컴포넌트 변경 패턴 (Setter / 동적 Material 인스턴스 / Async 변경). AssetClasses vs Components 비교 표. 11_AssetLoadingPolicy 의무. |
