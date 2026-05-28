---
name: assetloadingdeep
description: 11_AssetLoadingPolicy 깊이 자료 — FStreamableManager API (RequestAsync/Sync + FStreamableHandle 8 메소드) + UAssetManager Primary Asset/Bundle (LoadPrimaryAsset / Bundle / DefaultEngine.ini) + PreLoadAsset 5대 정책 + 함정 12종 + sub-skill 적용 매트릭스 14종.
---

# 11_AssetLoadingPolicy — Deep Reference

> 본 문서는 [`11_AssetLoadingPolicy.md`](../11_AssetLoadingPolicy.md) 의 §3, §4, §6, §8, §10 깊이 자료. 메인 문서는 §0~§2 (적용 범위 + 4단 원인 분석 + Soft/Hard 매트릭스) + §5 (4단 표준 패턴) + §7 결정트리 + §9 체크리스트 + §11~§12. 본 reference 는 API 깊이 + 정책 + 함정.
>
> **트리거**: FStreamableManager / UAssetManager / PreloadPrimaryAssets / Bundle 시스템 / DefaultEngine.ini PrimaryAssetTypesToScan / 함정 12종 / sub-skill 적용 매트릭스 작업 시 로드.

---

## 1. FStreamableManager — 비동기 로드 표준 API

### 1.1 진입점 (UAssetManager 통해 접근)

```cpp
// AssetManager.h:105 — 글로벌 인스턴스 (Subsystem)
FStreamableManager& SM = UAssetManager::GetStreamableManager();

// 사용 — 어떤 영역에서든 호출 가능 (Game/Editor 모두)
TSharedPtr<FStreamableHandle> Handle = SM.RequestAsyncLoad(Path, Delegate);
```

### 1.2 RequestAsyncLoad (가장 흔함)

```cpp
// StreamableManager.h:730 — 표준 비동기 로드
TSharedPtr<FStreamableHandle> Handle = SM.RequestAsyncLoad(
    SoftObjectPath,                         // 또는 TArray<FSoftObjectPath>
    FStreamableDelegate::CreateUObject(this, &AMyActor::OnLoadComplete),
    FStreamableManager::DefaultAsyncLoadPriority,   // 0 = 기본
    /*bManageActiveHandle=*/ false           // true = 자동 Pin (Manager 가 보관)
);

void AMyActor::OnLoadComplete()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::OnLoadComplete);
    UStaticMesh* Mesh = SoftMesh.Get();
    MeshComp->SetStaticMesh(Mesh);
}
```

### 1.3 FStreamableHandle 생명주기 (가장 중요)

```cpp
// 핵심 — Handle 이 살아있는 동안만 어셋도 살아있음
// Handle 이 Destroy 되면 → 어셋 GC 가능 → 다음 Tick 에 unloaded

// 표준 패턴 1: 멤버로 Handle 보유 (Pin)
UCLASS()
class AMyActor : public AActor
{
    TSharedPtr<FStreamableHandle> LoadedHandle;   // Pin

    void StartLoad()
    {
        LoadedHandle = SM.RequestAsyncLoad(Path, ...);
    }

    void StopLoad()
    {
        LoadedHandle.Reset();   // 어셋 unload 가능
    }
};

// 표준 패턴 2: bManageActiveHandle = true — Manager 가 보관
SM.RequestAsyncLoad(Path, Delegate, Priority, /*bManageActiveHandle=*/ true);
// Handle 무시 가능 — Manager 가 자동 ReleaseHandle 까지 보관
// 단 명시적 Unload 불가 → 일회용
```

### 1.4 FStreamableHandle 핵심 API

| 메소드 | 위치 | 의미 |
|--------|------|------|
| `HasLoadCompleted()` | `StreamableManager.h:197` | 로드 완료 여부 |
| `IsLoadingInProgress()` | `StreamableManager.h:209` | 로딩 중 |
| `WasCanceled()` | `StreamableManager.h:203` | 취소됨 |
| `BindCompleteDelegate(Delegate)` | `StreamableManager.h:324` | 완료 콜백 (이미 완료면 즉시 호출) |
| `BindCancelDelegate(Delegate)` | `StreamableManager.h:328` | 취소 콜백 |
| `CancelHandle()` | `StreamableManager.h:309` | 로드 취소 |
| `ReleaseHandle()` | `StreamableManager.h:302` | 명시적 Pin 해제 |
| `GetRequestedAssets(OutList)` | `StreamableManager.h:349` | 요청한 어셋 목록 |

### 1.5 RequestSyncLoad — 동기 (히칭 발생 — 사용 신중)

```cpp
// ⚠️ 동기 로드 — 게임 스레드 멈춤. 게임 중 사용 금지
TSharedPtr<FStreamableHandle> Handle = SM.RequestSyncLoad(Path);

// 허용 케이스: Editor 만 / 로딩 화면 중 / Map 전환 중
#if WITH_EDITOR
    SM.RequestSyncLoad(Path);
#endif
```

### 1.6 우선순위 (Priority)

```cpp
const TAsyncLoadPriority AsyncLoadHighPriority = 100;
const TAsyncLoadPriority DefaultAsyncLoadPriority = 0;

SM.RequestAsyncLoad(Path, Delegate, AsyncLoadHighPriority);   // UI / 게임플레이 핵심
SM.RequestAsyncLoad(Path, Delegate, DefaultAsyncLoadPriority); // 백그라운드 사전 로드
```

---

## 2. UAssetManager — Primary Asset + Bundle 시스템 (PreLoad 표준)

### 2.1 PrimaryAsset 개념

> **Primary Asset** = 게임이 명시적으로 추적하는 최상위 어셋 (Map / DataAsset / Character 등). **Secondary Asset** = Primary Asset 이 의존하는 어셋 (Mesh / Material / Texture).

```cpp
FPrimaryAssetId Id(TEXT("Weapon"), TEXT("Sword_Excalibur"));
// Path: /Game/Weapons/Sword_Excalibur.Sword_Excalibur

// 표준 Primary Asset Type
const FPrimaryAssetType MapType = TEXT("Map");
const FPrimaryAssetType WeaponType = TEXT("Weapon");
const FPrimaryAssetType CharacterType = TEXT("Character");
```

### 2.2 UPrimaryDataAsset 자식 (Primary Asset 표준)

```cpp
#include "Engine/DataAsset.h"

UCLASS(BlueprintType)
class UMyWeaponDataAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UStaticMesh> MeshAsset;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<USoundCue> FireSound;

    UPROPERTY(EditAnywhere)
    TSubclassOf<AProjectile> ProjectileClass;

    UPROPERTY(EditAnywhere)
    int32 Damage = 10;

    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId(TEXT("Weapon"), GetFName());
    }
};
```

### 2.3 LoadPrimaryAsset (PreLoad 표준 API)

```cpp
// AssetManager.h:308 — 단일 Primary Asset 비동기 로드
TSharedPtr<FStreamableHandle> Handle = UAssetManager::Get().LoadPrimaryAsset(
    FPrimaryAssetId(TEXT("Weapon"), TEXT("Sword_Excalibur")),
    /*LoadBundles=*/ {TEXT("Visual"), TEXT("Audio")},
    FStreamableDelegate::CreateUObject(this, &AMyActor::OnWeaponLoaded),
    /*Priority=*/ FStreamableManager::AsyncLoadHighPriority
);

// AssetManager.h:283 — 다중
TArray<FPrimaryAssetId> Ids = { Id1, Id2, Id3 };
UAssetManager::Get().LoadPrimaryAssets(Ids, {TEXT("Visual")}, Delegate);
```

### 2.4 Bundle 시스템 (어셋 그룹 묶음)

> **Bundle** = Primary Asset 안 어셋들을 그룹화 (`Visual` / `Audio` / `LowQuality` 등). Bundle 단위로 Load/Unload — 메모리 효율.

```cpp
UPROPERTY(EditAnywhere, meta=(AssetBundles="Visual"))
TSoftObjectPtr<UStaticMesh> MeshAsset;

UPROPERTY(EditAnywhere, meta=(AssetBundles="Audio"))
TSoftObjectPtr<USoundCue> FireSound;

UPROPERTY(EditAnywhere, meta=(AssetBundles="LowQuality"))
TSoftObjectPtr<UStaticMesh> LowQualityMesh;
```

```cpp
// 사용 — Visual + Audio 만 로드 (LowQuality 제외)
UAssetManager::Get().LoadPrimaryAsset(WeaponId, {TEXT("Visual"), TEXT("Audio")}, Delegate);

// AssetManager.h:365 — Bundle 상태 동적 변경
UAssetManager::Get().ChangeBundleStateForPrimaryAssets(
    {WeaponId},
    /*AddBundles=*/ {TEXT("LowQuality")},
    /*RemoveBundles=*/ {TEXT("Visual")},
    /*bRemoveAllBundles=*/ false,
    Delegate
);
```

### 2.5 PreloadPrimaryAssets — 메모리 상주 (사전 로드)

```cpp
// AssetManager.h:492 — 메모리 보유 (Pin) — 명시적 Unload 까지
TSharedPtr<FStreamableHandle> Handle = UAssetManager::Get().PreloadPrimaryAssets(
    {WeaponId},
    {TEXT("Visual"), TEXT("Audio")},
    /*bLoadRecursive=*/ true,
    Delegate
);

Handle->ReleaseHandle();   // Unload 가능
```

### 2.6 GameInstance Init 에서 Primary Asset 사전 등록

```cpp
void UMyGameInstance::Init()
{
    Super::Init();
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyGameInstance::Init);

    UAssetManager::Get().ScanPathForPrimaryAssets(
        TEXT("Weapon"),
        TEXT("/Game/Weapons"),
        UMyWeaponDataAsset::StaticClass(),
        /*bHasBlueprintClasses=*/ false
    );

    TArray<FPrimaryAssetId> CommonAssets = {
        FPrimaryAssetId(TEXT("Weapon"), TEXT("DefaultSword")),
        FPrimaryAssetId(TEXT("Character"), TEXT("Player_Hero")),
    };

    UAssetManager::Get().LoadPrimaryAssets(
        CommonAssets,
        {TEXT("Visual"), TEXT("Audio")},
        FStreamableDelegate::CreateUObject(this, &UMyGameInstance::OnCommonAssetsLoaded),
        FStreamableManager::AsyncLoadHighPriority
    );
}
```

### 2.7 DefaultEngine.ini Primary Asset 등록 (자동 스캔)

```ini
; DefaultEngine.ini
[/Script/Engine.AssetManagerSettings]
PrimaryAssetTypesToScan=(
    PrimaryAssetType="Weapon",
    AssetBaseClassLoaded=/Script/MyGame.MyWeaponDataAsset,
    bHasBlueprintClasses=False,
    bIsEditorOnly=False,
    Directories=((Path="/Game/Weapons")),
    SpecificAssets=(),
    Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook)
)

PrimaryAssetTypesToScan=(
    PrimaryAssetType="Character",
    AssetBaseClassLoaded=/Script/MyGame.MyCharacterDataAsset,
    bHasBlueprintClasses=False,
    Directories=((Path="/Game/Characters")),
    Rules=(Priority=-1,bApplyRecursively=True,CookRule=AlwaysCook)
)
```

> **자동 스캔** — Engine 시작 시 PrimaryAssetTypesToScan 모든 Path 스캔 → ID 등록.

---

## 3. PreLoadAsset 정책 — 5대 의무

### 3.1 정책 1: Constructor 안 어셋 로드 절대 금지

```cpp
// ❌ 안티패턴 — Constructor 안 동기 로드
AMyActor::AMyActor()
{
    static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshFinder(TEXT("/Game/.../MyMesh"));
    if (MeshFinder.Succeeded()) { Mesh->SetStaticMesh(MeshFinder.Object); }   // ⚠️ Editor 시작 시 동기 로드
}

// ✅ 정답 — UPROPERTY EditAnywhere 으로 BP 에서 지정 (또는 Soft + Async)
AMyActor::AMyActor()
{
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    // Mesh 자산은 BP 에서 지정 또는 BeginPlay 안 SoftPtr Async Load
}
```

> **ConstructorHelpers::FObjectFinder** = Editor 시작 시 모든 어셋 동기 로드 + Cooked 빌드 안 동작 + 순환 참조 위험 — 5.x 에서 deprecated 추세.

### 3.2 정책 2: BeginPlay 안 동기 LoadObject 금지

```cpp
// ❌ 안티패턴
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Game/.../MyMesh"));   // 동기 — 첫 Spawn 히칭
}

// ✅ 정답 — Soft + Async
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    if (!SoftMesh.IsNull())
    {
        FStreamableManager& SM = UAssetManager::GetStreamableManager();
        LoadHandle = SM.RequestAsyncLoad(SoftMesh.ToSoftObjectPath(),
            FStreamableDelegate::CreateUObject(this, &AMyActor::OnMeshLoaded));
    }
}
```

### 3.3 정책 3: Map 전환 시 사전 PreLoad (Loading Screen 활용)

```cpp
void UMyGameInstance::StartLevelTransition(const FString& MapName)
{
    // [1] LoadingScreen 표시
    GetSubsystem<ULoadingScreenSubsystem>()->Show();

    // [2] 다음 Map 의 모든 Primary Asset 사전 로드
    TArray<FPrimaryAssetId> NextMapAssets = GetMapPrimaryAssets(MapName);
    PendingLoadHandle = UAssetManager::Get().PreloadPrimaryAssets(
        NextMapAssets,
        {TEXT("Visual"), TEXT("Audio")},
        true,
        FStreamableDelegate::CreateLambda([this, MapName]()
        {
            // [3] 사전 로드 완료 → ClientTravel
            UGameplayStatics::OpenLevel(this, *MapName);
        })
    );
}
```

### 3.4 정책 4: Bundle 단위 로드 — 메모리 효율

```cpp
// 캐릭터의 무기 Equip — Equipped Bundle 만 로드
void AMyCharacter::EquipWeapon(FPrimaryAssetId WeaponId)
{
    UAssetManager::Get().LoadPrimaryAsset(
        WeaponId,
        {TEXT("Equipped")},
        FStreamableDelegate::CreateUObject(this, &AMyCharacter::OnWeaponEquipped, WeaponId)
    );
}

// 무기 Holster — Holstered Bundle 로 변경
void AMyCharacter::HolsterWeapon()
{
    UAssetManager::Get().ChangeBundleStateForPrimaryAssets(
        {EquippedWeaponId},
        /*AddBundles=*/ {TEXT("Holstered")},
        /*RemoveBundles=*/ {TEXT("Equipped")},
        false,
        FStreamableDelegate()
    );
}
```

### 3.5 정책 5: Handle 생명주기 관리 (Pin / Release 명시)

```cpp
UCLASS()
class AMyActor : public AActor
{
    TSharedPtr<FStreamableHandle> LoadHandle;

    virtual void EndPlay(EEndPlayReason::Type Reason) override
    {
        if (LoadHandle.IsValid())
        {
            LoadHandle.Reset();
        }
        Super::EndPlay(Reason);
    }
};
```

> **함정**: Handle 을 멤버로 보관 안 하면 즉시 Destroy → 어셋 unload → 다음 호출 시 nullptr.

---

## 4. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `ConstructorHelpers::FObjectFinder` 으로 Constructor 어셋 로드 | UPROPERTY EditAnywhere + BP 지정 또는 Soft + Async |
| 2 | `LoadObject<T>()` / `StaticLoadObject` 게임 중 호출 | 동기 — 첫 호출 히칭. `RequestAsyncLoad` 사용 |
| 3 | Soft Reference 후 Handle 보관 안 함 | 즉시 unload — 멤버 또는 `bManageActiveHandle=true` |
| 4 | `Hard Reference` 가 모든 어셋 보유 (Database) | 메모리 + 첫 로드 폭발. Soft + LoadPrimaryAsset |
| 5 | Editor PIE 에서 잘 동작 → Cooked 에서 히칭 | Editor 는 모든 어셋 캐시됨. Standalone Game 또는 Cooked 빌드 검증 의무 |
| 6 | Primary Asset Type 스캔 안 등록 | DefaultEngine.ini `PrimaryAssetTypesToScan` 또는 `ScanPathForPrimaryAssets` |
| 7 | `LoadPrimaryAsset` 안 Bundle 누락 | LoadBundles 안 명시 → Bundle 안 어셋 로드 안 됨. `{}` 빈 배열 = Default Bundle |
| 8 | `bLoadRecursive = false` — 의존 어셋 누락 | 자식 어셋 로드 안 됨 → SpawnActor 히칭. true 표준 |
| 9 | RequestAsyncLoad Handle 의 콜백 람다 안 `this` 캡처 | Actor Destroy 후 콜백 호출 시 crash. `TWeakObjectPtr<this>` 캡처 + IsValid 검사 |
| 10 | Soft Reference 변경 후 SaveGame 안 함 | 메타 변경 안 됨. EditAnywhere 후 BP 저장 의무 |
| 11 | 🚨 `RequestSyncLoad` 게임 중 사용 | Editor 만 / 로딩 화면 중. 게임 중 = 히칭 |
| 12 | 🚨 `RequestAsyncLoad` 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../07_ProfilingScopeRule.md)) |

---

## 5. sub-skill 적용 매트릭스 (14종)

| sub-skill | 적용 대상 |
|-----------|---------|
| [`GameFramework/Actor`](../../skills/GameFramework/references/Actor.md) | **§12 SpawnActor 히칭 방지 4단** + 클래스 슬롯 SoftClassPtr |
| [`GameFramework/PawnCharacter`](../../skills/GameFramework/references/PawnCharacter.md) | Mesh / AnimBP / SkeletalMesh = Soft + Pre-Load. Modular Character Bundle |
| [`GameFramework/Controller`](../../skills/GameFramework/references/Controller.md) | PlayerCameraManagerClass / HUDClass = Hard (작음) |
| [`GameFramework/GameMode`](../../skills/GameFramework/references/GameMode.md) | DefaultPawnClass / PlayerControllerClass = Hard / Match 시작 시 모든 Weapon PreLoad |
| [`GameFramework/GameInstance`](../../skills/GameFramework/references/GameInstance.md) | Init 안 Primary Asset Type 스캔 + 글로벌 Pre-Load |
| [`GameFramework/World`](../../skills/GameFramework/references/World.md) | LoadStreamLevel / WorldPartition + LoadingScreen 페어 |
| [`Components/MeshComponents`](../../skills/Components/references/MeshComponents.md) | StaticMesh / SkeletalMesh = 가변 시 Soft + Stream-In |
| [`Components/MovementComponents`](../../skills/Components/references/MovementComponents.md) | NavData / RVO 자산 — 일반적으로 Hard (작음) |
| [`Components/AudioComponent`](../../skills/Components/references/AudioComponent.md) | SoundCue / SoundWave = Soft + Pre-Load (큰 SFX) |
| [`Components/ParticleComponents`](../../skills/Components/references/ParticleComponents.md) | NiagaraSystem / VectorField = Soft + Pre-Load |
| [`Niagara`](../../skills/Niagara/SKILL.md) | NiagaraSystem 어셋 = Soft + Pre-Load (큰 VFX) |
| [`GAS`](../../skills/GAS/SKILL.md) | GameplayAbility / GameplayEffect = 표준 Hard (작은 BP). Cosmetic = Soft |
| [`UMG/UWidget`](../../skills/UMG/references/UWidget.md) | WidgetClass = SoftClassPtr (큰 Widget). Texture / Brush = Soft |
| [`Slate`](../../skills/Slate/SKILL.md) | SlateBrush Resource = Soft + 첫 Show 직전 PreLoad |

---

## 6. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | 11_AssetLoadingPolicy.md §3, §4, §6, §8, §10 에서 분리. 메인 8.7K → ~4K / reference ~9K. |
