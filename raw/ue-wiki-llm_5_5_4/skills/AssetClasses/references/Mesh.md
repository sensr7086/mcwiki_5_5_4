---
name: assetclasses-mesh
description: UStaticMesh (2,213 lines) + USkeletalMesh (3,103) + USkeleton (1,089) + UPhysicsAsset (428) - 5.x Nanite + Compatible Skeleton + Virtual Bones + Ragdoll + LOD.
---

# AssetClasses/Mesh — UStaticMesh + USkeletalMesh + USkeleton + UPhysicsAsset

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h` (2,213) + `SkeletalMesh.h` (3,103) + `Animation/Skeleton.h` (1,089) + `PhysicsEngine/PhysicsAsset.h` (428)
> **베이스**: `UStaticMesh : public UStreamableRenderAsset` / `USkeletalMesh : public USkinnedAsset` / `USkeleton : public UObject` / `UPhysicsAsset : public UObject`
> **요지**: **모든 메시 자산의 루트** — 컴포넌트 (StaticMeshComponent / SkeletalMeshComponent) 의 페어. **5.x Nanite (Static) + Animation (Skeletal)** 핵심.

---

## 🚨 공통 정책 (어셋 로드 + 6대 정책 적용)

| 정책 | Mesh 자산 적용 |
|------|--------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | **메시 자산 = 매우 큼** (StaticMesh 5MB~50MB / SkeletalMesh 10MB~100MB+). **TSoftObjectPtr<UStaticMesh>` / `TSoftObjectPtr<USkeletalMesh>` 표준** + UAssetManager Primary Asset + Bundle. Constructor 안 ConstructorHelpers::FObjectFinder 절대 금지. 자주 사용 메시 (Player Character / 적) = Match Start `PreloadPrimaryAssets(bLoadRecursive=true)` — Subobject (Material / Texture / Skeleton / PhysicsAsset / AnimBP) 모두 함께. |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | GC 방어 + CDO. 메시 멤버 = `UPROPERTY()` + `TObjectPtr<UStaticMesh>` (Hard) 또는 `TSoftObjectPtr` (Soft). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | PostLoad / Serialize / BeginCacheForCookedPlatformData 첫 줄 스코프 의무. |
| [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | 🛠 SourceModel / Build Settings / DDC — 모두 `WITH_EDITORONLY_DATA`. Cooked 빌드는 RenderData 만. |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | **§1 SkeletalMesh Bone LOD** (USkeletalMeshLODSettings + BonesToRemove + BonesToPrioritize + LODHysteresis + SkinCacheUsage 5.x) + **§2 StaticMesh LOD** (ScreenSize 표준 1.0/0.5/0.25/0.1/0.05 + 5.x Nanite 결정) + **§3 Actor Merging** (HISM / Mesh Merge / HLOD / 5.x WorldPartition HLOD). **다수 NPC 환경 = §6 통합 매트릭스** (LOD 5단계 9개 항목). |

---

## 1. UStaticMesh (StaticMesh.h:572 — 2,213 lines)

### 1.1 베이스 + 인터페이스

```cpp
class UStaticMesh : public UStreamableRenderAsset,
                    public IInterface_CollisionDataProvider,
                    public IInterface_AssetUserData,
                    public IInterface_AsyncCompilation
{
    // StaticMesh.h:603 — 렌더 데이터 (LOD 별 Vertex/Index Buffer)
    TUniquePtr<class FStaticMeshRenderData> RenderData;

    // StaticMesh.h:720 — 5.x Nanite 설정
    UPROPERTY(EditAnywhere, Category=NaniteSettings)
    FMeshNaniteSettings NaniteSettings;
};
```

### 1.2 핵심 멤버 (UPROPERTY)

| 필드 | 의미 |
|------|------|
| `RenderData` | LOD 0~N 의 Vertex/Index Buffer + Material Slot Map (런타임 사용) |
| `StaticMaterials` | Material Slot 배열 — 컴포넌트가 `SetMaterial(SlotIndex, Mat)` 으로 변경 |
| `BodySetup` | 콜리전 설정 (FBodySetup — Convex/TriMesh) |
| `LightingGuid` | 라이트맵 캐시 키 |
| `LightmapUVDensity` | 라이트맵 해상도 결정 |
| `MinLOD` | 최소 LOD 강제 (모바일 / Quality Level) |
| `NaniteSettings` | 5.x Nanite 활성 + 정밀도 / Fallback Triangles |
| `AssetUserData` | 사용자 정의 메타데이터 (BP에서 Get/Set) |

### 1.3 LOD 구조 (`FStaticMeshLODGroup`)

```cpp
// 5.x Nanite 활성 시 LOD 시스템 우회 — Auto-LOD
NaniteSettings.bEnabled = true;            // Nanite 활성
NaniteSettings.PercentTriangles = 1.0f;    // 100% 정밀도

// Nanite 비활성 시 — 전통 LOD 0~N
struct FStaticMeshLODResources
{
    FStaticMeshVertexBuffers VertexBuffers;
    FRawStaticIndexBuffer IndexBuffer;
    FStaticMeshSectionArray Sections;
    float MaxDeviation;                     // LOD 전환 거리
    float ScreenSize[MAX_STATIC_MESH_LODS]; // ScreenSize 비교
};

// 컴포넌트 측 LOD 강제
StaticMeshComp->SetForcedLodModel(2);       // LOD 2 강제 (1-based)
StaticMeshComp->MinLOD = 1;                  // 최소 LOD 1
```

### 1.4 5.x Nanite 통합

```cpp
struct FMeshNaniteSettings
{
    bool bEnabled;                          // 활성 토글
    float PercentTriangles;                  // 정밀도 (0~1)
    float FallbackPercentTriangles;          // Fallback Mesh
    float FallbackRelativeError;             // Fallback 정밀도
    float TrimRelativeError;                 // Trim Threshold
    int32 PositionPrecision;                 // 위치 정밀도 (auto = -1)
};

// 활성 조건
// 1. Static Mesh + No Skin
// 2. r.Nanite = 1
// 3. RHI 지원 (D3D12 / Metal / Vulkan)
// 4. NaniteSettings.bEnabled = true

// Nanite 활성 시 — LOD / 거리 기반 자동 처리
// MeshComp 측 LOD 설정 무시
```

### 1.5 PostLoad — 자산 검증 + DDC

```cpp
// StaticMesh.h:720 (대략) — Cooked 빌드 시 RenderData 캐시
ENGINE_API virtual void BeginCacheForCookedPlatformData(const ITargetPlatform* TargetPlatform) override;
{
    // Cook 시 플랫폼별 압축 + LOD 선별 + Lightmap 빌드
}

ENGINE_API virtual void PostLoad() override;
{
    Super::PostLoad();
    // SourceModel 마이그레이션 + Build Settings 검증 + RenderData 빌드
}
```

### 1.6 Bounds + Collision

```cpp
// 컴포넌트가 사용
FBoxSphereBounds Bounds = StaticMesh->GetExtendedBounds();   // Asset Bounds 확장 포함
FBoxSphereBounds RawBounds = StaticMesh->GetBoundingBox();

// Collision (BodySetup)
UBodySetup* BodySetup = StaticMesh->GetBodySetup();
BodySetup->CollisionTraceFlag = CTF_UseSimpleAsComplex;       // 단순 콜리전 사용
BodySetup->CreatePhysicsMeshes();                              // 런타임 빌드
```

---

## 2. USkeletalMesh (SkeletalMesh.h:436 — 3,103 lines, 가장 큼)

### 2.1 베이스 + 인터페이스

```cpp
class USkeletalMesh : public USkinnedAsset,
                      public IInterface_CollisionDataProvider,
                      public IInterface_AssetUserData,
                      public INodeMappingProviderInterface
{
    // 핵심 — Skeleton 페어 (의무)
    UPROPERTY(Category=Mesh, BlueprintGetter=GetSkeleton)
    TObjectPtr<USkeleton> Skeleton;

    // Material 슬롯 (다중)
    UPROPERTY(EditAnywhere, BlueprintGetter=GetMaterials)
    TArray<FSkeletalMaterial> Materials;

    // PhysicsAsset 페어 (Ragdoll / Cloth)
    UPROPERTY(EditAnywhere)
    TObjectPtr<UPhysicsAsset> PhysicsAsset;
};
```

### 2.2 Skeleton 페어 (의무)

> **모든 SkeletalMesh 는 USkeleton 자산을 참조** — Skeleton 이 본 트리 정의. 같은 Skeleton 공유 시 AnimBP / AnimSequence 호환.

```cpp
// 같은 Skeleton 공유 — Modular Character (Body/Cape/Hair)
USkeletalMesh* BodyMesh   = LoadObject<USkeletalMesh>(...);
USkeletalMesh* CapeMesh   = LoadObject<USkeletalMesh>(...);
check(BodyMesh->GetSkeleton() == CapeMesh->GetSkeleton());

// 다른 Skeleton — AnimBP 별도 / Compatible Skeleton 으로 호환 가능
```

### 2.3 LOD + LODSettings

```cpp
// USkeletalMeshLODSettings 별도 자산 (LOD 임계값 정의)
UPROPERTY(EditAnywhere)
TObjectPtr<USkeletalMeshLODSettings> LODSettings;

// 또는 인라인 LOD 정보
UPROPERTY()
TArray<FSkeletalMeshLODInfo> LODInfo;

// MinLOD (Quality Level 기반)
UPROPERTY(EditAnywhere)
FPerQualityLevelInt MinQualityLevelLOD;   // 5.x QualityLevel 별 MinLOD
```

### 2.4 PhysicsAsset 페어 (Ragdoll / Constraint)

```cpp
// SkeletalMesh 가 사용할 기본 PhysicsAsset
TObjectPtr<UPhysicsAsset> PhysicsAsset;

// 컴포넌트가 PhysicsAsset 변경 가능 (Ragdoll 활성)
SkelMeshComp->SetSimulatePhysics(true);                       // Ragdoll
SkelMeshComp->SetPhysicsAsset(NewPhysicsAsset, /*bForce=*/false);
```

### 2.5 Cloth 시뮬

```cpp
// Apex Cloth / Chaos Cloth (5.x)
ClothingAssets;                            // ChaosClothAsset 배열

// 컴포넌트 측
SkelMeshComp->SetEnableClothSimulation(true);
SkelMeshComp->SetClothMaxDistanceScale(1.5f);
```

### 2.6 RenderData (FSkeletalMeshRenderData)

```cpp
// LOD 별 Skin 정보
struct FSkeletalMeshLODRenderData
{
    TArray<FSkelMeshRenderSection> RenderSections;   // Material 별 그리기
    FSkinWeightVertexBuffer SkinWeightVertexBuffer;
    FStaticMeshVertexBuffers StaticVertexBuffers;
    FRawStaticIndexBuffer16or32Bit MultiSizeIndexContainer;
};

// 런타임 접근 (보통 직접 안 함 — 컴포넌트가 사용)
FSkeletalMeshRenderData* RenderData = SkelMesh->GetResourceForRendering();
```

### 2.7 Morph Targets (Blend Shape)

```cpp
// 블렌드 셰이프 (얼굴 표정)
UPROPERTY(BlueprintReadOnly)
TArray<TObjectPtr<UMorphTarget>> MorphTargets;

// 컴포넌트 측
SkelMeshComp->SetMorphTarget(TEXT("Smile"), 1.0f);     // 0~1
```

### 2.8 5.x USkinnedAsset 베이스

> **5.x — USkinnedAsset = USkeletalMesh 의 베이스 (5.0 부터 추가)** — 다른 스킨 자산 (USkinnedDestructionAsset 등) 도 같은 베이스. 컴포넌트는 USkinnedAsset 인터페이스 사용.

```cpp
// SkinnedMeshComponent 측 (5.x)
USkinnedAsset* SkinAsset = SkelMeshComp->GetSkinnedAsset();   // USkeletalMesh 또는 자손
```

---

## 3. USkeleton (Skeleton.h:294 — 1,089 lines)

### 3.1 핵심 멤버

```cpp
class USkeleton : public UObject,
                  public IInterface_AssetUserData,
                  public IInterface_PreviewMeshProvider
{
    // Skeleton.h:304 — 본 트리 (FBoneNode 배열)
    UPROPERTY()
    TArray<struct FBoneNode> BoneTree;

    // Skeleton.h:317 — Reference Skeleton (Bind Pose)
    FReferenceSkeleton ReferenceSkeleton;

    // Skeleton.h:335 — Virtual Bones (5.x — 동적 본)
    UPROPERTY()
    TArray<FVirtualBone> VirtualBones;
};
```

### 3.2 FBoneNode

```cpp
// Skeleton.h:93
struct FBoneNode
{
    FName Name_DEPRECATED;
    int32 ParentIndex_DEPRECATED;
    EBoneTranslationRetargetingMode::Type TranslationRetargetingMode;
    // 5.x — Reference Skeleton 으로 통합
};
```

### 3.3 Virtual Bones (5.x — Procedural Bone)

```cpp
// 본을 추가하지 않고 Hierarchy 변경 (예: IK Target)
struct FVirtualBone
{
    FName SourceBoneName;
    FName TargetBoneName;
    FName VirtualBoneName;
};

// 사용 케이스 — IK Target 본 추가 (Skeletal Mesh 수정 X)
USkeleton* Skeleton = GetSkeleton();
Skeleton->AddVirtualBone(TEXT("hand_l"), TEXT("ik_hand_target_l"), TEXT("ik_hand_root"));
```

### 3.4 Compatible Skeleton (호환 가능)

> **다른 Skeleton 끼리 AnimSequence 공유** — 본 이름·계층 호환. 5.x 표준 (Modular Animation).

```cpp
// Compatible 등록 (에디터에서)
Skeleton->AddCompatibleSkeleton(OtherSkeleton);

// Compatible 인 경우 AnimSequence 공유 가능
```

### 3.5 Reference Skeleton (Bind Pose)

```cpp
const FReferenceSkeleton& RefSkel = Skeleton->GetReferenceSkeleton();
int32 BoneIdx = RefSkel.FindBoneIndex(TEXT("head"));
FTransform RefPose = RefSkel.GetRefBonePose()[BoneIdx];
```

---

## 4. UPhysicsAsset (PhysicsAsset.h:170 — 428 lines)

### 4.1 핵심 멤버

```cpp
class UPhysicsAsset : public UObject,
                      public IInterface_PreviewMeshProvider,
                      public IInterface_AssetUserData
{
    // PhysicsAsset.h:208 — Body 배열 (본 당 1개)
    UPROPERTY()
    TArray<TObjectPtr<USkeletalBodySetup>> SkeletalBodySetups;

    // PhysicsAsset.h:215 — Constraint 배열 (Body ↔ Body 연결)
    UPROPERTY()
    TArray<TObjectPtr<class UPhysicsConstraintTemplate>> ConstraintSetup;
};
```

### 4.2 사용 패턴 (Ragdoll)

```cpp
// SkeletalMesh 의 PhysicsAsset → SkeletalMeshComponent 자동 사용
USkeletalMesh* SkelMesh = ...;
UPhysicsAsset* PhysAsset = SkelMesh->GetPhysicsAsset();

// 런타임 Ragdoll 활성
SkelMeshComp->SetSimulatePhysics(true);
SkelMeshComp->SetAllBodiesBelowSimulatePhysics(TEXT("pelvis"), true);

// 특정 본 Constraint 비활성 (Hit reaction)
SkelMeshComp->SetConstraintProfileForAll(TEXT("HitReaction"), /*bDefault=*/false);
```

### 4.3 SkeletalBodySetup (본 당)

```cpp
class USkeletalBodySetup : public UBodySetup
{
    FName BoneName;                    // 어느 본?
    EPhysicsType PhysicsType;          // PhysType_Default / Kinematic / Simulated
    TArray<FKAggregateGeom> AggGeom;   // 콜리전 모양 (Box/Sphere/Capsule/Convex)
};
```

---

## 5. 컴포넌트 사용 패턴 (런타임 Setter)

```cpp
// StaticMesh 변경
StaticMeshComp->SetStaticMesh(NewMesh);                        // 자동 RenderState Dirty + Bounds

// SkeletalMesh 변경 (5.x)
SkelMeshComp->SetSkeletalMeshAsset(NewMesh);                   // 5.x 권장
SkelMeshComp->SetSkeletalMesh(NewMesh, /*bReinitPose=*/true);   // legacy

// 같은 Skeleton 공유 시 — Mesh 만 교체 (AnimInstance 유지)
NewMesh->GetSkeleton() == OldMesh->GetSkeleton()  // 호환 검사

// PhysicsAsset 변경 (Ragdoll 셋업)
SkelMeshComp->SetPhysicsAsset(NewPhysAsset, /*bForce=*/false);

// Material 슬롯 변경
StaticMeshComp->SetMaterial(0, NewMaterial);                   // SlotIndex=0
StaticMeshComp->SetMaterialByName(TEXT("BodyMat"), NewMaterial);
```

---

## 6. Cooked Build 차이 + 함정

### 6.1 Cooked vs Uncooked 매트릭스

| 데이터 | Editor / Uncooked | Cooked Build |
|--------|-------------------|--------------|
| `StaticMesh::SourceModels` | 모든 LOD + Build Settings + Raw Mesh | strip 됨 (`WITH_EDITORONLY_DATA`) |
| `StaticMesh::RenderData` | DDC 캐시 / 빌드 시 생성 | .pak 안 사전 빌드 |
| `SkeletalMesh::ImportedModel` | LODModels (Editor 편집용) | strip 됨 |
| `SkeletalMesh::RenderData` | DDC 또는 빌드 | .pak 사전 빌드 |
| `Skeleton::AnimRetargetSources` | 메모리 상주 | 일부 strip |
| Nanite Mesh | 빌드 시 Cluster 생성 + DDC | .pak 안 Cluster 데이터 |

### 6.2 함정 (Cooked 빌드 깨짐)

```cpp
// ❌ 안티패턴 — Editor 전용 데이터 런타임 접근
StaticMesh->GetSourceModels();   // ⚠️ Cooked 안 strip — nullptr 또는 컴파일 오류

// ✅ 정답 — RenderData 사용
StaticMesh->GetRenderData()->LODResources[0];

// ✅ WITH_EDITOR 가드
#if WITH_EDITOR
    auto& Models = StaticMesh->GetSourceModels();
    // ...
#endif
```

---

## 7. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Constructor 안 `ConstructorHelpers::FObjectFinder<UStaticMesh>` | UPROPERTY EditAnywhere + BP 지정 또는 Soft + BeginPlay Async |
| 2 | `LoadObject<USkeletalMesh>` 동기 호출 | `FStreamableManager::RequestAsyncLoad` 비동기 |
| 3 | 다른 Skeleton 의 SkeletalMesh 변경 (`SetSkeletalMesh`) | AnimInstance 깨짐 — 같은 Skeleton 또는 Compatible Skeleton 의무 |
| 4 | Nanite 활성 + LOD 강제 (`SetForcedLodModel`) | Nanite 가 자동 LOD — 강제 무시됨 |
| 5 | StaticMesh 의 BodySetup 직접 변경 (런타임) | 모든 컴포넌트 영향 — 인스턴스 별도 BodySetup 사용 |
| 6 | PhysicsAsset 변경 시 `SetSimulatePhysics(true)` 안 호출 | Ragdoll 안 활성. SetAllBodiesBelowSimulatePhysics |
| 7 | Editor 전용 멤버 (`SourceModels`) Cooked 빌드 접근 | `WITH_EDITOR` 가드 / `RenderData` 사용 |
| 8 | StaticMesh `BlueprintReadWrite` UPROPERTY | 메시 자체는 자산 — 동적 변경 시 `SetStaticMesh` API 사용 |
| 9 | 🚨 `TObjectIterator<UStaticMesh>` / `TObjectIterator<USkeletalMesh>` | UAssetManager + Primary Asset Type 스캔 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 10 | 🚨 자주 Spawn 되는 메시 PreLoad 안 함 | Match Start `PreloadPrimaryAssets(bLoadRecursive=true)` ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |

---

## 8. 체크리스트 (Mesh 자산 사용 시)

- [ ] 멤버 = `TSoftObjectPtr<UStaticMesh>` / `TSoftObjectPtr<USkeletalMesh>` (가변·다수) 또는 `TObjectPtr<>` (영구·고정)
- [ ] Constructor 안 ConstructorHelpers / LoadObject 사용 안 함
- [ ] BeginPlay / Equip / Spawn 직전 = FStreamableManager Async Load
- [ ] 자주 사용 = UAssetManager Primary Asset + Bundle PreLoad
- [ ] SkeletalMesh 변경 시 Skeleton 호환 확인 (`GetSkeleton() == OldMesh->GetSkeleton()`)
- [ ] Nanite 활성 = LOD 강제 안 함 + Fallback 데이터 정상
- [ ] PhysicsAsset 변경 시 `SetSimulatePhysics(true)` 페어 호출
- [ ] Editor 전용 데이터 (`SourceModels`) 런타임 접근 안 함 (`WITH_EDITOR` 가드)
- [ ] 🚨 6대 정책 + 어셋 로드 정책 만족
- [ ] Cooked Build (Development) `stat unit` 메시 변경 시 검증

---

## 9. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인 (페어 매트릭스)
- [`AssetClasses/Material`](../Material/SKILL.md) — Material Slot (Mesh 가 참조)
- [`AssetClasses/Texture`](../Texture/SKILL.md) — Material 의 Texture (간접)
- [`AssetClasses/Animation`](../Animation/SKILL.md) — AnimSequence / AnimBP (SkeletalMesh 페어)
- [`AssetClasses/Physics`](../Physics/SKILL.md) — PhysicalMaterial / PhysicsConstraint
- [`Components/MeshComponents`](../../Components/references/MeshComponents.md) — **호스트 컴포넌트** (StaticMeshComponent / SkeletalMeshComponent / ISM / HISM / SplineMesh / PoseableMesh)
- [`Components/PhysicsComponents`](../../Components/references/PhysicsComponents.md) — Constraint / Handle (PhysicsAsset 페어)
- [`AssetRegistry`](../../AssetRegistry/SKILL.md) — `IAssetRegistry::GetAssetsByClass(UStaticMesh::StaticClass())` 검색
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (메시 자산 PreLoad 의무) · 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) (GC 방어) · [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) (Cooked 빌드)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UStaticMesh 2,543 lines** 분석 (RenderData / StaticMaterials / BodySetup / Lightmap / **5.x Nanite** FMeshNaniteSettings + 활성 조건 + Fallback / LOD 강제 / Bounds + Collision). **USkeletalMesh 3,248 lines