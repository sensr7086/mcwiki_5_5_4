---
type: synthesis
title: "Soft 참조 컴포넌트 작성 표준 — Mesh / AnimClass / PhysicsAsset / Materials / AssetUserData 통합 패턴"
slug: mc-soft-asset-component-pattern
created: 2026-05-10
last_updated: 2026-05-12
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-components-meshcomponents]]"
  - "[[sources/ue-assetclasses-mesh]]"
  - "[[sources/ue-assetclasses-assetuserdata]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-coreuobject-objecthandles]]"
  - "[[sources/ue-niagara-skill]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UStaticMesh]]"
  - "[[entities/UAnimInstance]]"
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/UNiagaraSystem]]"
concepts:
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Object-Handles]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
status: living
tags: [synthesis, kmcproject, soft-pointer, async-load, components, assetuserdata]
---

# Soft 참조 컴포넌트 작성 표준

## 1. Thesis

KMCProject 의 Soft 참조 컴포넌트 — `MCSoftStaticMeshComponent` (StaticMesh) / `MCSoftSkeletalMeshComponent` (SkeletalMesh + AnimClass + PhysicsAsset) — 는 **모든 자산 멤버를 `TSoftObjectPtr` / `TSoftClassPtr` 로 보유**해 [[concepts/Asset-Loading-Policy]] §3 의 SpawnActor 4단 히칭 (Class load → CDO load → Asset members → Constructor) 중 **[3] Asset members 동기 로드** 를 회피한다. 새 Soft 컴포넌트를 만들 때 따라야 할 골격: **(1) Soft 멤버 + (2) BeginPlay 비동기 로드 + (3) `LoadHandle` Pin / EndPlay Cancel + (4) 콜백에서 `IsValid` + Setter 적용 + (5) 빈 메시 안전 디폴트 + (6) [[concepts/MC-Asset-Validation-Policy]] LOG/ensure + (7) ApplyLoadedAssets 후 AssetUserData 자동 처리 hook + (8) `OnRegister` 동기 path 로 BP archetype / Level Editor preview 일치 + (9) 머티리얼 슬롯 자동 미러링 (옵션)**.

## 2. 6 단계 골격 (skeleton)

| 단계 | 코드 | 정책 |
| -- | -- | -- |
| 1. Soft 멤버 | `UPROPERTY() TSoftObjectPtr<UAsset>` (Mesh/Material/Anim/Physics) · `TSoftClassPtr<UClass>` (AnimInstance/Subclass) | [[concepts/Soft-Reference-vs-Hard]] |
| 2. Constructor 안전 디폴트 | `Tick OFF`, `bAutoActivate=false`, `Mobility=Movable`, `NoCollision`, 메시 비워둠 | [[concepts/Component-Policies-6]] §1·5 |
| 3. BeginPlay 비동기 로드 | `Streamable.RequestAsyncLoad(Paths, Lambda, LoadPriority, false, false, "DebugTag")` | [[concepts/Asset-Loading-Policy]] §2 단계 5 |
| 4. Handle Pin | 멤버 `TSharedPtr<FStreamableHandle> LoadHandle` 보관, EndPlay 에서 `CancelHandle` | 같은 정책 |
| 5. 콜백 안전 | 람다 캡처 = `TWeakObjectPtr<this>`, `IsValid(this)` + `CachedOwner.IsValid()` 검사 | [[concepts/Component-Policies-6]] §3·4 |
| 6. Setter 적용 | `SetStaticMesh` / `SetSkeletalMeshAsset` / `SetAnimInstanceClass` / `SetMaterial` / `SetPhysicsAsset` | UE 표준 |

## 3. 자산별 매트릭스

| 자산 종류 | Soft 타입 | UE Setter | 페어 자산 자동 로드 |
| -- | -- | -- | -- |
| StaticMesh | `TSoftObjectPtr<UStaticMesh>` | `SetStaticMesh` | BodySetup (콜리전) |
| SkeletalMesh | `TSoftObjectPtr<USkeletalMesh>` | `SetSkeletalMeshAsset` (5.1+) | Skeleton + PhysicsAsset (hard) + ClothingAssets |
| AnimInstance Class | `TSoftClassPtr<UAnimInstance>` | `SetAnimInstanceClass` | AnimBP 의 모든 변수 / FunctionGraph |
| Material | `TSoftObjectPtr<UMaterialInterface>` | `SetMaterial(SlotIdx, Mat)` | 모든 Texture / Material Function (hard) |
| Texture | `TSoftObjectPtr<UTexture>` | `UMaterialInstanceDynamic::SetTextureParameterValue` | 없음 |
| PhysicsAsset | `TSoftObjectPtr<UPhysicsAsset>` | `SetPhysicsAsset(NewPhys, bForceReInit)` | SkeletalBodySetups / Constraints |
| NiagaraSystem | `TSoftObjectPtr<UNiagaraSystem>` | `SetAsset` | DataInterface 내부 자산들 (hard) |

각 자산 타입에서 [[sources/ue-assetclasses-mesh]] §7 같은 *함정 표* 를 참고 — 자산별 SetSimulate 페어 / Skeleton 호환 / 빈 메시 처리 등.

## 4. 시나리오 — 기존 컴포넌트 → Soft 변환 절차

기존에 `TObjectPtr<UStaticMesh> Mesh;` 로 hard 참조하던 컴포넌트를 Soft 로 바꿀 때:

```cpp
// before — hard reference (Cooked Build SpawnActor 히칭 원인)
UPROPERTY(EditAnywhere) TObjectPtr<UStaticMesh> Mesh;

// after — soft + 비동기 로드 골격
UPROPERTY(EditAnywhere) TSoftObjectPtr<UStaticMesh> SoftMesh;
TSharedPtr<FStreamableHandle> LoadHandle;

void BeginPlay() {
    Super::BeginPlay();
    if (SoftMesh.IsNull()) { return; }                       // (Validation Policy A)
    if (USoftMesh.Get()) { ApplyLoaded(); return; }           // 이미 메모리 상주
    const TWeakObjectPtr<UMyComp> Self(this);
    LoadHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(
        SoftMesh.ToSoftObjectPath(),
        FStreamableDelegate::CreateLambda([Self]() {
            if (auto* C = Self.Get()) C->ApplyLoaded();
        }));
}

void EndPlay(EEndPlayReason::Type R) {
    if (LoadHandle.IsValid()) LoadHandle->CancelHandle();
    Super::EndPlay(R);
}
```

[[sources/mc-soft-skeletalmesh-ragdoll]] / [[sources/ue-ref-11-assetloadingpolicy]] §6·8 의 표준.

## 5. 함정 / 열린 질문

- [x] **MCCOMPONENT_DEF 페어 누락** — 검증 완료.
- [x] **Niagara 확장 — Soft 컴포넌트 + UMCNiagaraSocketBindings 통합** — 2026-05-12 해소 (§7.2).
- [x] **PostEditChangeProperty 경로의 Editor preview 불일치** — 2026-05-12 해소 (§7.5).
- [x] **BP 컴포넌트 뷰포트 / Level Editor placed actor 의 메시·Niagara 미표시** — 2026-05-12 해소 (§7.6 OnRegister 동기 path).
- [x] **머티리얼 슬롯 디자이너 UX** — 2026-05-12 해소 (§7.7 자동 미러링).
- [ ] **Bundle PreLoad 결합** — 자주 Spawn 되는 캐릭터는 `UAssetManager::PreloadPrimaryAssets` 으로 사전 로드 → 컴포넌트 BeginPlay 시점엔 이미 메모리 상주. 본 패턴은 PreLoad 와 호환.
- [ ] **Skeleton 호환 검증** — `MC_ENSURE_SKELETON_COMPAT` 매크로 (`MCAssetValidation.h:159`) — `MCSoftSkeletalMeshComponent::ApplyLoadedAssets` 에 적용 여부 검증 필요.
- [ ] **Audio / DataAsset 확장** — `USoundCue` / `UMetaSoundSource` / `UDataAsset` 도 같은 골격으로 — `UMCSoftAudioComponent` 신설 후보.
- [ ] **GC 와 Bundle 충돌** — Bundle 로 hard 참조된 자산이 PreLoad 후에도 컴포넌트 Soft 핸들 Release 시 GC 되지 않음. Bundle 단위 release 절차 별도 필요.
- [ ] **BP archetype Save 시 부모 StaticMesh UPROPERTY hard ref 저장 위험** — §7.8 함정 #9. 빌드 시 BP archetype 검사 도구 작성 후보.

## 6. 관련

### Sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/mc-asset-validation-policy]] · [[sources/ue-components-meshcomponents]] · [[sources/ue-assetclasses-mesh]] · [[sources/ue-assetclasses-assetuserdata]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-components-skill]] · [[sources/ue-coreuobject-objecthandles]] · [[sources/ue-niagara-skill]]

### Entities

[[entities/USkeletalMeshComponent]] · [[entities/UStaticMeshComponent]] · [[entities/USkeletalMesh]] · [[entities/UStaticMesh]] · [[entities/UAnimInstance]] · [[entities/UPrimitiveComponent]] · [[entities/UNiagaraSystem]]

### Concepts

[[concepts/Soft-Reference-vs-Hard]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Component-Policies-6]] · [[concepts/MC-Asset-Validation-Policy]] · [[concepts/Object-Handles]] · [[concepts/Garbage-Collection]] · [[concepts/Editor-Only-4-Tier-Separation]]

### Related synthesis

[[synthesis/spawnactor-hitching-4-step-pattern]] · [[synthesis/mc-character-hit-reaction-pipeline]] · [[synthesis/component-vs-actor-lifecycle-table]] · [[synthesis/editor-preview-scene-runtime-handoff]]

---


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/bp-scs-preview-viewport-lifecycle]] (inbound=4, suggest_missing_cross_link high confidence)
## 7. AssetUserData / Editor Preview / Material 자동화 통합 (2026-05-12)

### 7.1 배경 — 왜 Soft 컴포넌트가 직접 책임지는가

UE 의 `UStaticMesh` / `USkeletalMesh` 가 모두 `IInterface_AssetUserData` 구현 → 메시 자산에 `UMCNiagaraSocketBindings` 같은 `UAssetUserData` 자손 첨부 가능. KMCProject 의 런타임 측 처리는 `UMCStaticMeshNiagaraSpawnerComponent` 가 담당했지만 Soft 컴포넌트와 race:

```
[Frame N]   Owner BeginPlay
  ├─ UMCSoftStaticMeshComponent::BeginPlay → RequestLoadAsync (비동기)
  └─ UMCStaticMeshNiagaraSpawnerComponent::BeginPlay
      └─ GetStaticMesh() == nullptr → "No bindings" → 영구 비활성
```

해결 — Soft 컴포넌트가 *자기 메시는 자기가 책임* (Option B 채택). 다섯 진입점 (BeginPlay / PostEditChangeProperty / OnRegister / RequestSocketNiagaraSpawn / SetSoftStaticMesh) 모두 통합 hook.

### 7.2 런타임 (PIE / Cooked) 경로 — `ApplyLoadedAssets` 끝의 hook

```cpp
void UMCSoftStaticMeshComponent::ApplyLoadedAssets()
{
    // ... (SetStaticMesh + SetMaterial + 콜리전/가시성 복원)
    OnSoftMeshLoaded.Broadcast(this, LoadedMesh);

    if (bAutoSpawnSocketNiagara)
    {
        ProcessAssetUserDataAfterMeshLoaded();   // 비동기
    }
}

void UMCSoftStaticMeshComponent::ProcessAssetUserDataAfterMeshLoaded()
{
    MC_LOGRET_IF_NULL(GetStaticMesh(), "Mesh not applied");
    // 재진입 정리 → GetBindingsFromMesh → RequestLoad → HandleSocketBindingsLoaded
}
```

### 7.3 정책 매핑 (런타임)

| 정책 | 적용 위치 |
| -- | -- |
| [[concepts/Asset-Loading-Policy]] §2 단계 5 | `SocketBindingsLoadHandle` 별도 핸들 보관 |
| [[concepts/Component-Policies-6]] §3 | `CachedSocketBindings` = UPROPERTY(Transient) + TObjectPtr |
| [[concepts/Profiling-Scope-Rule]] | 모든 진입점 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| [[concepts/MC-Asset-Validation-Policy]] (A) | `MC_LOGRET_IF_NULL` / `MC_LOGRET_IF_INVALID_WEAK` |
| [[sources/ue-niagara-skill]] AutoRelease | `DeactivateAll(bForceDestroy=false)` Pool 호환 |

### 7.4 디자이너 워크플로 (실사용)

```
1. StaticMesh.uasset 더블클릭 → UE StaticMesh Editor
   Details → "Asset User Data" → +Add → "MC Niagara Socket Bindings"
   Bindings 배열 채우기 → Save

2. 게임 BP — Actor 에 UMCSoftStaticMeshComponent 부착
3. Details → Soft Static Mesh = (해당 StaticMesh)
   ├─ §7.7 머티리얼 자동 미러링 → SoftOverrideMaterials 슬롯이 자동으로 채워짐
   ├─ §7.6 OnRegister → BP 컴포넌트 뷰포트 즉시 메시 + Niagara 표시
   └─ §7.5 PostEditChangeProperty → 디테일 변경 시 즉시 Level Editor viewport 갱신

4. Level Editor 의 placed actor 도 동일 — PIE / Simulate 안 켜도 viewport 정상
5. PIE → §7.2 비동기 path 가 BeginPlay 에서 발화 (같은 결과)
```

**별도 `UMCStaticMeshNiagaraSpawnerComponent` 부착 불필요**.

### 7.5 PostEditChangeProperty Editor preview 동기 path

§7.2 의 hook 은 `ApplyLoadedAssets` 끝 → BeginPlay 가 시작되어야 발화 → 시뮬레이션에서만. Level Editor placed actor 가 디테일 변경 시는 `PostEditChangeProperty` 가 호출되어 `SetStaticMesh` 만 갱신 → Niagara 미스폰. 해결: 동기 path 추가.

```cpp
void UMCSoftStaticMeshComponent::PostEditChangeProperty(FPropertyChangedEvent& E)
{
    Super::PostEditChangeProperty(E);
    if (HasAnyFlags(RF_ClassDefaultObject)) return;

    const FName PropName = E.GetPropertyName();
    const bool bMeshOrMatChanged = (PropName == SoftStaticMesh || PropName == SoftOverrideMaterials);
    const bool bSocketPreviewOptionChanged = (PropName == bAutoSpawnSocketNiagara
                                           || PropName == bEditorPreviewSocketNiagara);

    if (bMeshOrMatChanged)
    {
        if (UStaticMesh* Mesh = SoftStaticMesh.LoadSynchronous())
        {
            // §7.7 머티리얼 자동 미러링 (SoftStaticMesh 변경 + 옵션 ON + 배열 빈 경우만)
            if (PropName == SoftStaticMesh && bAutoFillOverrideMaterialsFromMesh
                && SoftOverrideMaterials.Num() == 0)
            {
                AutoFillOverrideMaterialsFromMesh(Mesh);
            }

            SetStaticMesh(Mesh);
            for (int32 Idx = 0; Idx < SoftOverrideMaterials.Num(); ++Idx)
            {
                if (UMaterialInterface* Mat = SoftOverrideMaterials[Idx].LoadSynchronous())
                {
                    SetMaterial(Idx, Mat);
                }
            }

            if (bAutoSpawnSocketNiagara && bEditorPreviewSocketNiagara)
            {
                ProcessAssetUserDataAfterMeshLoadedEditorSync();   // 동기 path
            }
        }
        else
        {
            SetStaticMesh(nullptr);
            // 메시 끊기면 잔여 Niagara 즉시 destroy
            MCNiagaraSocketBindingHelpers::DeactivateAll(SpawnedSocketNiagaras, true);
        }
    }
    else if (bSocketPreviewOptionChanged) { /* 옵션 토글 즉시 반영 */ }
}
```

### 7.6 OnRegister Editor World 동기 path (2026-05-12 후속 — BP 컴포넌트 뷰포트 케이스)

**왜 별도 path?**

`PostEditChangeProperty` 는 *디테일 변경* 이벤트 발생 시에만 호출. BP 컴포넌트 디테일에서 미리 SoftStaticMesh 가 지정된 상태로 컴파일된 BP 의 *컴포넌트 뷰포트 preview 인스턴스* 는 `PostEditChangeProperty` 가 발화 안 됨 → 메시조차 안 보임. 또 Level Editor 에 placed 된 새 인스턴스도 동일.

해결: `OnRegister` 안에서 Editor World 분기 후 동기 로드.

```cpp
void UMCSoftStaticMeshComponent::OnRegister()
{
    Super::OnRegister();
    TRACE_CPUPROFILER_EVENT_SCOPE(UMCSoftStaticMeshComponent::OnRegister);

    if (HasAnyFlags(RF_ClassDefaultObject)) return;

    const UWorld* World = GetWorld();
    if (!World) return;

    const bool bIsEditorWorld = World->WorldType == EWorldType::Editor
                             || World->WorldType == EWorldType::EditorPreview;
    if (!bIsEditorWorld) return;          // PIE / Game — BeginPlay 위임

    if (IsValid(GetStaticMesh())) return; // 이미 적용됨 — 재진입 noop

    if (!SoftStaticMesh.IsNull())
    {
        ApplyMeshAndMaterialsSynchronous();  // 공용 동기 헬퍼

        if (bAutoSpawnSocketNiagara && bEditorPreviewSocketNiagara && IsValid(GetStaticMesh()))
        {
#if WITH_EDITOR
            ProcessAssetUserDataAfterMeshLoadedEditorSync();
#endif
        }
    }
}
```

**OnRegister 가 호출되는 케이스 매트릭스** (모두 hook 됨):

| 케이스 | OnRegister 호출 | World 타입 | 동기 path 실행 |
| -- | -- | -- | -- |
| BP 컴파일 → SCS preview 인스턴스 재생성 | ✅ | EditorPreview | ✅ |
| Level Editor 에 placed 시 | ✅ | Editor | ✅ |
| Level Editor placed actor 의 BP recompile | ✅ | Editor | ✅ |
| StaticMesh Asset Editor preview | ✅ | EditorPreview | ✅ (Preview Subsystem 와 양립) |
| PIE 시작 시 | ✅ | PIE | ❌ noop (BeginPlay 위임) |
| Cooked Game SpawnActor | ✅ | Game | ❌ noop (BeginPlay 위임) |

### 7.7 머티리얼 슬롯 자동 미러링

**디자이너 UX 문제**: SoftStaticMesh 만 지정하면 SoftOverrideMaterials 가 빈 채로 남음 → 디자이너가 슬롯별 머티리얼 override 시작점으로 사용하려면 수동으로 슬롯 추가 필요.

**해결**: 옵션 `bAutoFillOverrideMaterialsFromMesh = true` (기본). 메시 변경 시 메시의 모든 머티리얼 슬롯을 `TSoftObjectPtr<UMaterialInterface>` 로 자동 미러링.

```cpp
void UMCSoftStaticMeshComponent::AutoFillOverrideMaterialsFromMesh(UStaticMesh* Mesh)
{
    MC_LOGRET_IF_NULL(Mesh, "Mesh nullptr — caller must LoadSynchronous first");

    const int32 NumMaterials = Mesh->GetStaticMaterials().Num();
    if (NumMaterials <= 0) return;

    SoftOverrideMaterials.Reset(NumMaterials);
    SoftOverrideMaterials.SetNum(NumMaterials);

    for (int32 Idx = 0; Idx < NumMaterials; ++Idx)
    {
        UMaterialInterface* SlotMat = Mesh->GetStaticMaterials()[Idx].MaterialInterface;
        SoftOverrideMaterials[Idx] = TSoftObjectPtr<UMaterialInterface>(SlotMat);
    }
}
```

**호출 정책** — 호출자(`PostEditChangeProperty` / `ApplyMeshAndMaterialsSynchronous`) 가 가드:

- `bAutoFillOverrideMaterialsFromMesh == true` (옵션 ON)
- `SoftOverrideMaterials.Num() == 0` (빈 배열 — 디자이너 명시 override 보존)
- SoftStaticMesh *변경* 의 경우만 발화 (SoftOverrideMaterials 자체 변경에는 발화 X — 무한 루프 회피)

**디자이너 워크플로**:

```
1. SoftStaticMesh = SM_Sword_F06 (4 머티리얼 슬롯)
   → SoftOverrideMaterials 자동 채워짐 [M_Sword_Blade, M_Sword_Hilt, M_Sword_Grip, M_Sword_Pommel]
2. (선택) Slot 0 만 override = M_Sword_Blade_Damaged
3. PIE → 메시 + 슬롯 0 override + 슬롯 1~3 디폴트
```

### 7.8 함정 / 안티패턴

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | Soft 컴포넌트 + Spawner 컴포넌트 *동시* 부착 → Niagara 중복 spawn | 디자이너가 하나만 선택 |
| 2 | `bAutoSpawnSocketNiagara=false` 인데 `RequestSocketNiagaraSpawn` 미호출 | BP `OnSoftMeshLoaded` 구독 + 명시 호출 |
| 3 | 메시 미로드 상태에서 `RequestSocketNiagaraSpawn` 호출 | `MC_LOGRET_IF_NULL(GetStaticMesh(), …)` Soft fail |
| 4 | 런타임 메시 swap 후 기존 Niagara 그대로 | `ProcessAssetUserDataAfterMeshLoaded` 진입 시 `DeactivateAll(bForceDestroy=false)` 자동 |
| 5 | EndPlay 시 SocketBindingsLoadHandle Cancel 누락 | 람다 안 `IsValid(StrongThis)` 검사 + 명시 Cancel |
| 6 | `CachedSocketBindings` raw 포인터 저장 | UPROPERTY(Transient) + TObjectPtr — GC 안전 |
| 7 | PostEditChangeProperty sync path 가 `bForceDestroy=false` | Editor viewport stale 회피 — `bForceDestroy=true` |
| 8 | Editor sync path 안에서 SoftStaticMesh 가 다른 path 와 race | PostEditChangeProperty 는 메인 스레드 동기 — 자체 race 없음 |
| 9 | **BP archetype Save 시 부모 `StaticMesh` UPROPERTY hard ref 저장** | UStaticMeshComponent::SetStaticMesh 가 `Modify()` 호출 → archetype dirty → Save 시 BP .uasset 에 hard ref. **디자이너 가이드**: SoftStaticMesh 만 지정하고 BP 컴포넌트 뷰포트의 Save 후 patch tool 로 부모 StaticMesh 필드를 nullptr 재설정 검토. 빌드 시 BP archetype 검사 도구 후보. |
| 10 | **머티리얼 자동 미러링이 디자이너 명시 override 덮어씀** | `SoftOverrideMaterials.Num() == 0` 가드 — 빈 배열에서만 발화. 이미 채워둔 경우 보존. |

### 7.9 SkeletalMesh 측 확장 (열린)

`UMCSoftSkeletalMeshComponent` 도 동일 hook 적용 가능 (`USkeletalMesh` 도 `IInterface_AssetUserData` 구현). `ApplyLoadedAssets` 끝 + `PostEditChangeProperty` + `OnRegister` + 머티리얼 자동 미러링 모두. 추가로 *Skeleton 호환* 검증 (`MC_ENSURE_SKELETON_COMPAT`) 의무.

### 7.10 측정 (TBD)

[[sources/ue-measure-mcsoftstaticmesh-2026-05-08]] 의 후속 — Soft + AssetUserData + OnRegister + 머티리얼 자동 미러링 통합 패턴 측정. BP 컴포넌트 뷰포트 / Level Editor placed / PIE 세 시나리오.
