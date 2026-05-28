---
name: asset-loading-policy
description: 🚨 어셋 로드 정책 — SpawnActor 히칭 방지 표준. SpawnActor 히칭 4단 원인 (Class CDO/Subobject/재귀 어셋/Material PSO) + Soft/Hard Reference 6종 비교 + 환경 모드별 로드 정책 (Editor Pure = Sync TryLoad / PIE / Cooked Game = Async) + FStreamableManager + UAssetManager Primary Asset/Bundle + SpawnActorDeferred + FinishSpawning 4단 패턴 + PreLoadAsset 5대 정책. 모든 어셋 멤버 추가 시 + Cooked Build 검증 시.
---

# 11. 어셋 로드 정책 — Soft/Hard Reference + FStreamableManager + UAssetManager + SpawnActor 히칭 방지

> 본 인덱스는 **모든 sub-skill 에 적용되는 횡단 정책** — 어셋 참조 방식·비동기 로드 규약·SpawnActor 히칭 원인 분석·PreLoad 표준 패턴.
> **요지**: **Hard Reference 의 무분별한 사용이 SpawnActor 히칭 + Cooked Build 메모리 폭발 + 첫 프레임 stall 의 90% 원인** — 본 문서의 4단 정책으로 회피.

---

## 0. 본 정책의 적용 범위

| 적용 영역 | 의무 사항 |
|---------|----------|
| **`[GameFramework]`** | Actor / Pawn / Character / Controller / GameMode 의 **클래스 슬롯 (TSubclassOf)** 모두 SoftClassPtr 검토 + SpawnActor 히칭 방지 4단 |
| **`[Components]`** | UActorComponent / SceneComponent / Mesh / Material 멤버 — UPROPERTY UObject* (Hard) vs TSoftObjectPtr (Soft) 결정 |
| **`[Slate]/[UMG]`** | 위젯 BP 클래스 / Texture / Font / Brush — 화면 표시 직전 Pre-Load |
| **`[Render]`** | Material / Texture / Mesh — PSO Precache + Stream-in |
| **모든 sub-skill** | Constructor 안 어셋 로드 절대 금지 + BeginPlay 안 동기 LoadObject 금지 — FStreamableManager 통한 비동기 로드 |

> **본 정책 위반 시 — Cooked Build 첫 Spawn 에 100ms+ 히칭 + Editor PIE 와 동작 차이 (Editor 는 모든 어셋 메모리 상주) → QA 회피**.

---

## 1. SpawnActor 히칭 원인 분석 (가장 중요)

### 1.1 히칭 발생 4단계 (Cooked Build)

```
World->SpawnActor<AMyActor>(Class, Transform, Params)
  ↓
[1] Class CDO 로드 (Cooked Build 첫 호출)
    ↓ Class 가 메모리 안 없으면 동기 LoadObject — 디스크 IO 발생
    ↓ 자식 BP Class 의 경우 부모 Class 도 모두 로드
    ↓ ⚠️ 100ms+ 히칭 (HDD) / 10~30ms (SSD)
  ↓
[2] Subobject 의 CDO 들 로드 (`CreateDefaultSubobject` 가 만든 Component 들)
    ↓ StaticMesh / SkeletalMesh / Material / Texture / SoundCue 등 Hard Reference
    ↓ 한 Class 당 5~20개 Subobject — 모두 동기 로드
    ↓ ⚠️ 200ms+ 히칭
  ↓
[3] Subobject 의 Subobject 도 재귀 로드
    ↓ Mesh 가 참조하는 Material / Material 이 참조하는 Texture / AnimBP 가 참조하는 SkeletalMesh
    ↓ 5단계 깊이까지 Hard Reference 체인 가능
    ↓ ⚠️ 1초+ 히칭 (대형 캐릭터)
  ↓
[4] 첫 Render 시 Material/Shader PSO 컴파일 + Texture 첫 업로드 + GPU 메모리 할당
    ↓ 첫 가시화 프레임에 추가 히칭 — Spawn 직후 1~2 프레임
    ↓ ⚠️ 50~500ms (Material 복잡도 따라)
```

**총합 — Cooked Build 첫 SpawnActor 히칭**: **수백 ms ~ 수 초** (캐릭터 / 차량 등 복잡 Actor).

### 1.2 Editor PIE 와의 차이 (디버그 함정)

| 환경 | 어셋 로드 시점 | SpawnActor 히칭 |
|------|------------|----------------|
| **Editor PIE** | Editor 시작 시 모든 어셋 메모리 상주 | **거의 0ms** — 모두 캐시됨 |
| **Standalone Game (Editor)** | 첫 호출 시 동기 로드 | **수십 ms** |
| **Cooked Build (Development)** | 첫 호출 시 .pak 에서 IO + LoadPackage | **100ms~1초** |
| **Cooked Build (Shipping)** | 위 + Shader 컴파일 캐시 | **200ms~수 초** |

> **🚨 Editor PIE 에서 잘 동작하지만 Shipping 빌드에서 히칭** — 본 정책 위반의 가장 흔한 증상.

### 1.3 히칭 원인 분류

| 원인 | 비용 | 회피 방법 |
|------|------|---------|
| **Class CDO 로드** (TSubclassOf<T>) | 10~100ms | `TSoftClassPtr<T>` + FStreamableManager 사전 로드 |
| **Subobject Hard Reference** (UPROPERTY UObject*) | 50~500ms | `TSoftObjectPtr<T>` + Bundle 로 묶음 사전 로드 |
| **Mesh / Material / Texture 체인** | 100ms~수 초 | UAssetManager + Primary Asset + Bundle |
| **Shader / PSO 컴파일** | 50~500ms | PSO Precache (5.x — 자동 + 수동 보강) |
| **첫 Texture GPU 업로드** | 10~100ms | TextureStreaming + bForceMiplevelsToBeResident 사전 |
| **AnimBP / Audio 첫 컴파일** | 20~100ms | BP Nativization (deprecated 5.x) / 사전 인스턴스 |

---

## 2. Soft vs Hard Reference 결정 매트릭스 (가장 중요)

### 2.1 6종 Reference 비교

| 종류 | 선언 | Cooked 시 즉시 로드 | 사용 시점 | 표준 사용 |
|------|------|------------------|---------|---------|
| **Hard Reference (UObject\*)** | `UPROPERTY() TObjectPtr<UMesh>` | ✅ Class 로드 시 동기 | 즉시 접근 | 영구 보유 객체 |
| **Hard Class Reference** | `UPROPERTY() TSubclassOf<AActor>` | ✅ | 즉시 SpawnActor | 항상 사용 |
| **Soft Object Reference** | `UPROPERTY() TSoftObjectPtr<UMesh>` | ❌ Path 만 | 명시적 로드 후 | 가끔 사용 |
| **Soft Class Reference** | `UPROPERTY() TSoftClassPtr<AActor>` | ❌ Path 만 | 명시적 로드 후 | DLC / 가변 |
| **FSoftObjectPath** | `UPROPERTY() FSoftObjectPath` | ❌ FString | UAssetManager / SoftPtr 변환 후 | Manager 패턴 |
| **FPrimaryAssetId** | `UPROPERTY() FPrimaryAssetId` | ❌ Type::Name | UAssetManager Load | DataAsset 표준 |

### 2.2 Hard Reference 사용 결정 트리

```
Asset 을 멤버로 보유?
├── ALWAYS USED (Constructor 부터 EndPlay 까지 항상 접근) → Hard Reference (TObjectPtr)
│   예: Pawn 의 CapsuleComponent / Mesh / CharacterMovement
│
├── 가끔 사용 (특정 상태에만)
│   ├── 미리 로드 가능 (BeginPlay 시 Primary Asset Pre-Load) → Soft Reference + Manager Pre-Load
│   │   예: 무기 Mesh (Equip 시), 특수 효과 (Skill 발동 시)
│   │
│   └── 동적 / DLC / 사용자 Custom → Soft Reference + 사용 직전 Async Load
│       예: 월드 안 모든 NPC 종류, MOD 어셋
│
└── 일회용 (Spawn 후 Destroy 까지) → Hard Reference (단순)
    예: 발사체 Bullet Class
```

> ⚠ **Editor 도구 예외**: 디테일 패널 / Custom Asset Editor / Factory / Importer 등 **Editor 순수 모드** (PIE/Game 아님) 에서는 Soft Reference 라도 **동기 로드 (TryLoad)** 표준 — 자세한 환경 분기 = §3.

### 2.3 Hard Reference 의 함정 — 메모리 + 첫 로드 비용

```cpp
// ❌ 안티패턴 — Hard Reference 가 모든 무기 Mesh 보유
UCLASS()
class AWeaponDatabase : public AInfo
{
    UPROPERTY(EditAnywhere)
    TArray<TObjectPtr<UStaticMesh>> AllWeaponMeshes;   // 100개 Mesh = 메모리 + 첫 로드 폭발
};

// ✅ 정답 — Soft Reference + Manager Load
UCLASS()
class AWeaponDatabase : public AInfo
{
    UPROPERTY(EditAnywhere)
    TArray<TSoftObjectPtr<UStaticMesh>> AllWeaponMeshes;   // Path 만 보유

    UFUNCTION()
    void LoadWeaponMesh(int32 Index, TFunction<void(UStaticMesh*)> Callback)
    {
        FStreamableManager& SM = UAssetManager::GetStreamableManager();
        SM.RequestAsyncLoad(AllWeaponMeshes[Index].ToSoftObjectPath(),
            FStreamableDelegate::CreateLambda([Path = AllWeaponMeshes[Index], Callback]()
            {
                Callback(Path.Get());
            })
        );
    }
};
```

---

## 3. 환경 모드별 로드 정책 — Editor Pure vs PIE vs Cooked Game ⭐

> **요지**: **같은 어셋이라도 환경 모드에 따라 로드 방식이 달라야 함**. Editor 순수 모드 (PIE 아님, RuntimeGame 아님) = **동기 로드 (TryLoad / LoadSynchronous) 표준**. PIE / Cooked Game = §5 비동기 로드 의무.
>
> Editor 도구 (디테일 패널 / Asset Editor / Thumbnail / Factory / Importer) 는 **프레임 예산 없음** + **즉시 접근 필요** — 비동기 콜백 대기는 UX 저해 / Race 위험.

### 3.1 환경 분류 매트릭스

| WorldType | 환경 | 로드 정책 | 이유 |
|-----------|------|----------|------|
| `EWorldType::Editor` | Editor 메인 (레벨 에디터) | ✅ **Sync (TryLoad)** | 프레임 예산 없음 / 도구 컨텍스트 |
| `EWorldType::EditorPreview` | Asset Editor / Thumbnail / Preview | ✅ **Sync (TryLoad)** | 위와 동일 |
| `EWorldType::PIE` | Play In Editor (게임 모드) | ❌ **Async (§5 표준)** | 게임 프레임 예산 — 히칭 회피 |
| `EWorldType::Game` | Cooked / Standalone Game | ❌ **Async (§5 표준)** | 위와 동일 |
| `EWorldType::GamePreview` | Game Preview (특수) | ❌ Async | 게임 컨텍스트 |

> 🚨 **PIE 는 Editor 안에서 실행되지만 Runtime 정책 적용** — `GIsEditor==true` 만 보고 Sync 처리하면 PIE 첫 프레임 히칭.

### 3.2 환경 검증 표준 헬퍼

```cpp
#if WITH_EDITOR
// Editor 순수 모드 검증 — PIE / RuntimeGame 모두 제외
static bool IsPureEditorMode(const UWorld* World)
{
    if (!GIsEditor) return false;
    if (!World) return true;   // World 없음 = 확실히 Editor 도구 컨텍스트
    return World->WorldType == EWorldType::Editor
        || World->WorldType == EWorldType::EditorPreview;
}
#endif
```

### 3.3 동기 로드 표준 코드 (Editor 도구)

```cpp
#if WITH_EDITOR
// 1. TSoftObjectPtr → 동기 로드
TSoftObjectPtr<UStaticMesh> SoftMesh = MyData->PreviewMeshPtr;
if (UStaticMesh* Mesh = SoftMesh.LoadSynchronous())
{
    // 즉시 사용 OK — Editor 프레임 예산 없음
}

// 2. FSoftObjectPath → 동기 로드
FSoftObjectPath Path = MyData->ConfigPath;
if (UObject* Obj = Path.TryLoad())
{
    // 즉시 사용
}

// 3. TSoftClassPtr → 동기 로드
TSoftClassPtr<AActor> SoftClass = MyData->ActorClassPtr;
if (UClass* LoadedClass = SoftClass.LoadSynchronous())
{
    // 즉시 SpawnActor / CDO 접근
}
#endif
```

### 3.4 환경별 로드 API 매트릭스

| 환경 | TSoftObjectPtr | FSoftObjectPath | TSoftClassPtr | 비고 |
|------|---------------|-----------------|---------------|------|
| **Editor Pure** ⭐ | `LoadSynchronous()` | `TryLoad()` | `LoadSynchronous()` | 즉시 접근 / 도구 컨텍스트 |
| **PIE** | `FStreamableManager::RequestAsyncLoad` | 동일 | 동일 | 게임 프레임 예산 |
| **Cooked Game** | `FStreamableManager::RequestAsyncLoad` | 동일 | 동일 | 위와 동일 |

### 3.5 환경 분기 표준 — 같은 컴포넌트가 양쪽 지원

```cpp
class UMyComponent : public UActorComponent
{
    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> SoftMesh;

    UPROPERTY()
    TObjectPtr<UStaticMesh> CachedMesh;

    void LoadMeshAdaptive()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComponent::LoadMeshAdaptive);

#if WITH_EDITOR
        // Editor Pure (디테일 패널 프리뷰 / Factory) = Sync OK
        if (IsPureEditorMode(GetWorld()))
        {
            CachedMesh = SoftMesh.LoadSynchronous();
            return;
        }
#endif

        // PIE / Cooked Game = §5 Async 의무
        FStreamableManager& SM = UAssetManager::GetStreamableManager();
        Handle = SM.RequestAsyncLoad(
            SoftMesh.ToSoftObjectPath(),
            FStreamableDelegate::CreateWeakLambda(this, [WeakThis = TWeakObjectPtr<UMyComponent>(this)]()
            {
                if (WeakThis.IsValid())
                {
                    WeakThis->CachedMesh = WeakThis->SoftMesh.Get();
                }
            })
        );
    }

private:
    TSharedPtr<FStreamableHandle> Handle;
};
```

### 3.6 적용 sub-skill (Editor Sync 표준)

| sub-skill | 적용 시점 |
|-----------|----------|
| `Editor/PropertyEditor` | 디테일 패널 — Customize 안 Sync Load |
| `Editor/AssetEditorAPI` | 실행 중 에디터 접근 — Sync Load (도구 자동화) |
| `Editor/UnrealEd/Factories` | UFactory::FactoryCreateNew — Sync OK |
| `Editor/AssetTools` | IAssetTypeActions::OpenAssetEditor — Sync OK |
| `Editor/ToolMenus` | Editor 메뉴 콜백 — Sync OK |
| `Editor/LevelEditor` | LevelEditor 확장 도구 — Sync OK |
| `CoreUObject/Editor` | `PostEditChangeProperty` / `PostLoad` (Editor 분기) — Sync OK |
| `AssetClasses/*` | Editor Inspector / Importer / Cooker (Editor) — Sync OK |

### 3.7 함정 — Editor Sync Load 적용 시점 (5종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `UCustomAssetEditor` 안 `RequestAsyncLoad` 사용 — 콜백 지연 + UI race | Editor 도구 = `TryLoad` / `LoadSynchronous` 즉시 |
| 2 | `EWorldType::PIE` 도 Editor 모드로 취급 → Sync Load → PIE 첫 프레임 히칭 | PIE = Runtime 정책 (Async §5) |
| 3 | `IDetailCustomization::CustomizeDetails` 안 비동기 콜백 → Editor UI race | 디테일 패널 = Sync Load (즉시 표시) |
| 4 | `UThumbnailRenderer::Draw` 안 RequestAsyncLoad → 첫 호출 빈 썸네일 | 썸네일 = Sync Load |
| 5 | `GIsEditor` 만 보고 분기 — PIE 도 `GIsEditor==true` | `WorldType` 검증 의무 (`IsPureEditorMode`) |

> 🚨 **PIE 함정**: `GIsEditor==true` 는 PIE 도 포함 — `WorldType::PIE` 분기 의무. Editor Sync 정책은 **`WorldType::Editor` / `EditorPreview` 전용**.

---

## 4 ~ 5 깊이 자료 — [`references/AssetLoadingDeep.md`](./references/AssetLoadingDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 슬림화 + 깊이 자료 별도.

| § | 내용 | reference 위치 |
|---|------|----------------|
| 4 | **FStreamableManager API** — RequestAsyncLoad / RequestSyncLoad + FStreamableHandle 8 메소드 + Pin/Release 생명주기 + 우선순위 | [`§1`](./references/AssetLoadingDeep.md#1-fstreamablemanager--비동기-로드-표준-api) |
| 5 | **UAssetManager Primary Asset + Bundle** — UPrimaryDataAsset / FPrimaryAssetId / LoadPrimaryAsset / Bundle 시스템 / PreloadPrimaryAssets / DefaultEngine.ini 자동 스캔 | [`§2`](./references/AssetLoadingDeep.md#2-uassetmanager--primary-asset--bundle-시스템-preload-표준) |

---

## 6. SpawnActor 히칭 방지 — 4단 표준 패턴 ⭐

### 6.1 4단 흐름 (가장 중요)

```
[1] PreLoad        ── BeginPlay / Map 시작 / Bundle 변경 시 Pre-Load 시작 (비동기)
                   └─ 어셋이 메모리 + GPU 까지 모두 준비됨
[2] Wait           ── PreLoad 완료 대기 (UI 로 진척 표시 권장)
[3] Spawn Deferred ── 콜백 안 SpawnActorDeferred (라이프사이클 시작 — BeginPlay 아직)
[4] Init + Show    ── 추가 Property 셋업 → FinishSpawning (BeginPlay) → 가시화
```

### 6.2 표준 코드 패턴

```cpp
// MyGameMode.cpp — Match 시작 시 모든 무기 사전 로드
void AMyGameMode::HandleMatchHasStarted()
{
    Super::HandleMatchHasStarted();
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::HandleMatchHasStarted);

    // [1] PreLoad — 매치에 사용될 모든 Weapon Class + Asset 사전 로드
    TArray<FPrimaryAssetId> WeaponsToPreload;
    for (const auto& WeaponId : MatchWeaponIds)
    {
        WeaponsToPreload.Add(WeaponId);
    }

    PreloadHandle = UAssetManager::Get().PreloadPrimaryAssets(
        WeaponsToPreload,
        {TEXT("Visual"), TEXT("Audio")},
        /*bLoadRecursive=*/ true,
        FStreamableDelegate::CreateUObject(this, &AMyGameMode::OnWeaponsPreloaded),
        FStreamableManager::AsyncLoadHighPriority
    );
}

void AMyGameMode::OnWeaponsPreloaded()
{
    // [2] Wait 완료 — 모든 어셋 메모리 상주
    bWeaponsReady = true;
}

// [3] [4] Spawn — 비용 0 (모두 캐시됨)
AWeapon* AMyGameMode::SpawnWeaponForPlayer(APlayerController* PC, FPrimaryAssetId WeaponId)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::SpawnWeaponForPlayer);

    if (!bWeaponsReady)
    {
        // 폴백 — 동기 로드 (히칭 발생) 또는 대기
        UE_LOG(LogTemp, Warning, TEXT("Weapons not preloaded — fallback sync load"));
    }

    // Class + Asset 모두 메모리 상주 — 히칭 0
    UMyWeaponDataAsset* WeaponData = UAssetManager::Get().GetPrimaryAssetObject<UMyWeaponDataAsset>(WeaponId);
    TSubclassOf<AWeapon> WeaponClass = WeaponData->WeaponActorClass;   // 미리 로드됨

    // SpawnActorDeferred — 추가 셋업 후 BeginPlay
    AWeapon* NewWeapon = GetWorld()->SpawnActorDeferred<AWeapon>(
        WeaponClass,
        FTransform::Identity,
        PC->GetPawn(),                       // Owner
        Cast<APawn>(PC->GetPawn()),          // Instigator
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn
    );

    if (NewWeapon)
    {
        // [4] Init — UPROPERTY 셋업 (BeginPlay 가 보게 됨)
        NewWeapon->WeaponData = WeaponData;
        NewWeapon->Damage = WeaponData->Damage;
        NewWeapon->FinishSpawning(FTransform::Identity);   // BeginPlay 호출
    }

    return NewWeapon;
}
```

### 6.3 표준 패턴 변형 — Just-In-Time Async Load

```cpp
// 사전 로드 안 했지만 비동기로 로드 (히칭 회피)
void AMyActor::SpawnAsyncEnemy(TSoftClassPtr<AEnemy> SoftClass)
{
    FStreamableManager& SM = UAssetManager::GetStreamableManager();
    AsyncSpawnHandle = SM.RequestAsyncLoad(
        SoftClass.ToSoftObjectPath(),
        FStreamableDelegate::CreateUObject(this, &AMyActor::OnEnemyClassLoaded, SoftClass),
        FStreamableManager::AsyncLoadHighPriority
    );
}

void AMyActor::OnEnemyClassLoaded(TSoftClassPtr<AEnemy> SoftClass)
{
    UClass* LoadedClass = SoftClass.Get();
    if (!LoadedClass) return;

    AEnemy* Enemy = GetWorld()->SpawnActor<AEnemy>(LoadedClass, GetActorTransform());
}
```

> **핵심**: SoftClass 로딩 후 → SpawnActor 시 Class CDO 만 로드 (Subobject 는 함께 안 됨) — 첫 Spawn 시 §1.1 [2] 에서 다시 히칭. **PreloadPrimaryAssets + bLoadRecursive=true 가 모든 의존 어셋 함께 로드 — 가장 안전**.

---

## 7. PreLoadAsset 정책 — [`references/AssetLoadingDeep.md §3`](./references/AssetLoadingDeep.md#3-preloadasset-정책--5대-의무) ✂️

5대 의무 (각 코드 패턴은 reference 참조):
1. **Constructor 안 어셋 로드 절대 금지** — `ConstructorHelpers::FObjectFinder` deprecated
2. **BeginPlay 안 동기 LoadObject 금지** — Soft + Async 표준
3. **Map 전환 시 사전 PreLoad** — LoadingScreen + PreloadPrimaryAssets
4. **Bundle 단위 로드** — Equipped/Holstered 동적 변경
5. **Handle 생명주기 관리** — Pin / Release 명시

---

## 8. 결정 트리 — 어떤 패턴 사용?

```
어셋 멤버 보유?
├── 영구 (Constructor → Destroyed) → Hard Reference (TObjectPtr<UMesh>) — 단순, BP 지정
│
├── 가변 / 동적 / 조건부
│   ├── 사용 시점 미리 알 수 있음 (BeginPlay / Equip 등)
│   │   └── ✅ Soft Reference + UAssetManager Primary Asset + Bundle Pre-Load
│   │
│   └── 사용 시점 모름 (런타임 결정)
│       └── ✅ Soft Reference + FStreamableManager RequestAsyncLoad (사용 직전)
│
├── DLC / MOD / 사용자 Custom
│   └── ✅ FPrimaryAssetId + LoadPrimaryAsset + Bundle 동적 변경
│
└── Map 전환 시 함께 로드
    └── ✅ DefaultEngine.ini PrimaryAssetTypesToScan + LoadingScreen + PreloadPrimaryAssets
```

---

## 9. 함정 & 안티패턴 — [`references/AssetLoadingDeep.md §4`](./references/AssetLoadingDeep.md#4-함정--안티패턴-12종) (12종)

핵심 5종 요약:
- ConstructorHelpers::FObjectFinder (deprecated) / LoadObject 게임 중 / Soft Reference 후 Handle 미보관 / Editor PIE vs Cooked 차이 / 콜백 람다 IsValid 검사 누락
- 자세한 12종 + 정답은 reference 참조

---

## 10. 체크리스트 (어셋 멤버 추가 시)

- [ ] Constructor 안 `ConstructorHelpers::FObjectFinder` / `LoadObject` 사용 안 함
- [ ] BeginPlay 안 `LoadObject` / `StaticLoadObject` 사용 안 함
- [ ] 영구 보유 = `TObjectPtr<T>` (Hard) / 동적 = `TSoftObjectPtr<T>` (Soft) 결정
- [ ] DataAsset = `UPrimaryDataAsset` 자식 + `GetPrimaryAssetId()` override
- [ ] Soft Reference 어셋 = `meta=(AssetBundles="...")` Bundle 명시
- [ ] DefaultEngine.ini `PrimaryAssetTypesToScan` 등록 또는 `ScanPathForPrimaryAssets` 코드 호출
- [ ] PreLoad 시점 명확 (GameInstance Init / Match Start / Map 전환 / Equip 등)
- [ ] `FStreamableHandle` 멤버 보관 또는 `bManageActiveHandle=true`
- [ ] 콜백 람다 안 `TWeakObjectPtr<this>` + IsValid 검사
- [ ] EndPlay / Shutdown 안 Handle Release
- [ ] **Cooked Build (Development)** 에서 SpawnActor 첫 호출 stat unit 검증
- [ ] **Cooked Build (Shipping)** 에서 60fps 유지 검증
- [ ] ⭐ **Editor 도구 (디테일 패널 / Factory / AssetEditorAPI)** = `IsPureEditorMode` 검증 + `TryLoad` / `LoadSynchronous` 동기 로드 (§3)
- [ ] ⭐ **PIE / Cooked Game 분기 확실** — `GIsEditor` 가 아닌 `WorldType` 검증 (§3.7-1)
- [ ] 🚨 [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) — 콜백 첫 줄 프로파일링 스코프
- [ ] 🚨 6대 정책 만족 ([`10_ComponentPolicies.md`](./10_ComponentPolicies.md))

---

## 11. sub-skill 적용 매트릭스 — [`references/AssetLoadingDeep.md §5`](./references/AssetLoadingDeep.md#5-sub-skill-적용-매트릭스-14종) (14종)

GameFramework 6 + Components 4 + Plugin 2 (Niagara/GAS) + UI 2 (UMG/Slate) — 자세한 적용은 reference 참조.

---

## 12. 관련 문서

- [`CoreUObject/ObjectHandles`](../skills/CoreUObject/references/ObjectHandles.md) — TObjectPtr / TWeakObjectPtr / **TSoftObjectPtr / FSoftObjectPath / FPrimaryAssetId 깊이**
- [`CoreUObject/Package`](../skills/CoreUObject/references/Package.md) — UPackage / LoadPackageAsync 베이스
- [`CoreUObject/Cooking`](../skills/CoreUObject/references/Cooking.md) — Cooked Build 빌드 시 어셋 처리
- [`AssetRegistry`](../skills/Editor/references/AssetRegistry.md) — IAssetRegistry / FAssetData / FARFilter
- [`GameFramework/GameInstance`](../skills/GameFramework/references/GameInstance.md) — Subsystem 안 Pre-Load 패턴
- [`GameFramework/Actor`](../skills/GameFramework/references/Actor.md) — **§12 SpawnActor 히칭 방지** (이 문서의 4단 패턴 적용)
- 교차: 🚨 [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) (콜백 스코프) · 🚨 [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) (Subsystem 등록 패턴) · 🚨 [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) (6대 정책)

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **SpawnActor 히칭 4단 원인 분석** (Class CDO 로드 / Subobject CDO 로드 / 재귀 어셋 로드 / Material PSO 컴파일) + Editor PIE vs Cooked Build 차이. **Soft vs Hard Reference 6종 비교 표** + 결정 트리. **FStreamableManager API** + **UAssetManager Primary Asset + Bundle 시스템** + **🎯 SpawnActor 히칭 방지 4단 표준 패턴** + **PreLoadAsset 정책 5대**. 결정 트리 + 함정 12종 + 14단 체크리스트 + sub-skill 적용 매트릭스 14종. |
| 2026-05-12 | **§3 환경 모드별 로드 정책 신설** ⭐ — Editor Pure (`EWorldType::Editor` / `EditorPreview`) = **동기 로드 (TryLoad / LoadSynchronous) 표준** vs PIE / Cooked Game = §5 비동기 의무. `IsPureEditorMode` 헬퍼 + 환경별 로드 API 매트릭스 + 환경 분기 표준 코드 + 함정 5종 + 적용 sub-skill 8종 (Editor 카테고리 전체 + CoreUObject/Editor + AssetClasses). 후속 §4~§13 재번호. 체크리스트 2 항목 추가. |
