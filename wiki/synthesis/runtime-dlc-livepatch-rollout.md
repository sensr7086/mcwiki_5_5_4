---
type: synthesis
title: "런타임 DLC + Live Patch + BP→C++ 마이그레이션 통합 — 자산 swap 안전 절차"
slug: runtime-dlc-livepatch-rollout
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-build-skill]]"
  - "[[sources/ue-coreuobject-cooking]]"
  - "[[sources/ue-blueprint-skill]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-editor-assetregistry]]"
entities:
  - "[[entities/UBlueprint]]"
  - "[[entities/UBlueprintGeneratedClass]]"
  - "[[entities/UPackage]]"
  - "[[entities/UClass]]"
  - "[[entities/IAssetRegistry]]"
concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/CPP-BP-Boundary]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Asset-Lifecycle]]"
status: living
tags: [synthesis, dlc, live-patch, bp-migration, runtime]
---

# 런타임 DLC + Live Patch + BP→C++ 마이그레이션 통합

## 1. Thesis

런타임 자산 갱신 — DLC (새 콘텐츠 추가) / Live Patch (기존 자산 hot swap) / BP→C++ 마이그레이션 (호환성 유지하며 BP 자손을 C++ 베이스로 이전) — 은 모두 **이미 메모리상에 있는 자산을 어떻게 안전하게 바꾸는가** 의 변형. 3 가지 근본 절차 — **(1) Pak Mount 순서 + AssetRegistry 재스캔 / (2) 메모리 상주 자산의 GC 보장 (Bundle release + Hard ref 추적) / (3) BP→C++ Class 변경 시 시리얼라이즈 호환 (`UPROPERTY(deprecated)` + `Serialize` override)**. 본 synthesis 는 [[synthesis/cooked-first-frame-stability]] §5 의 DLC 셋업 + §7 함정 #6 (BP→C++ 마이그레이션) + §7 함정 #7 (Live Patch) 을 통합 절차로 묶음.

## 2. 3 시나리오 매트릭스

| 시나리오 | 무엇이 바뀜 | 핵심 절차 | 함정 |
| -- | -- | -- | -- |
| DLC 추가 | 새 자산 / Class / Map | Pak mount + AR 재스캔 + Bundle 등록 | mount 순서, 의존 base asset 누락 |
| Live Patch | 기존 자산 새 버전 | Pak chunk 교체 + 메모리 상주 자산 reload | 게임 진행 중 swap 시 GC race |
| BP→C++ 마이그 | BP Class → C++ 베이스 | UPROPERTY deprecation + Serialize override | 기존 저장 게임 호환 |

## 3. (1) DLC 추가 절차

```cpp
// Pak mount (UE 5.x — IPlatformFilePak)
FString PakPath = FPaths::ProjectContentDir() / TEXT("DLC/MyDLC.pak");
const FCoreDelegates::FPakSigningKeysDelegate& Keys = FCoreDelegates::OnPakLoaded;

bool bMounted = FCoreDelegates::OnMountPak.Execute(PakPath, /*PakOrder=*/1000, /*MountPoint=*/TEXT(""));
MC_LOGRET_IF_FALSE(bMounted, "DLC pak mount failed");

// AssetRegistry 재스캔 (DLC 의 PrimaryAsset 발견)
IAssetRegistry& AR = IAssetRegistry::Get();
AR.ScanPathsSynchronous({TEXT("/MyDLC")}, /*bForceRescanExistingAssets=*/false);

// AssetManager 에 새 PrimaryAssetType 등록
UAssetManager& AM = UAssetManager::Get();
AM.ScanPathsForPrimaryAssets(
    FPrimaryAssetType(TEXT("Pawn.DLC")),
    {TEXT("/MyDLC/Pawns")},
    APawn::StaticClass(),
    /*bHasBlueprintClasses=*/true,
    /*bIsEditorOnly=*/false,
    /*bForceSynchronousScan=*/false);

// Bundle 로드 (게임 시작 PreLoad 패턴 같음 — [[synthesis/cooked-first-frame-stability]] §4)
TArray<FPrimaryAssetId> NewIds;
AM.GetPrimaryAssetIdList(FPrimaryAssetType(TEXT("Pawn.DLC")), NewIds);
AM.LoadPrimaryAssets(NewIds, {TEXT("Game")}, FStreamableDelegate::CreateLambda([](){
    UE_LOG(LogMCAsset, Log, TEXT("DLC Pawns loaded"));
}));
```

**Mount 순서 핵심**:
- Base pak (game) — order 0
- DLC pak — order > 0 (높을수록 우선) — 같은 path 자산 충돌 시 DLC 가 이김
- Patch pak — order > DLC

## 4. (2) Live Patch — 메모리 상주 자산 swap

가장 위험. 이미 spawn 된 액터의 메시 / AnimBP / Material 이 *바뀐 자산을 가리켜야 함*.

```cpp
// 게임 진행 중 — Player Mesh 의 새 버전 적용
USkeletalMesh* OldMesh = SoftMesh.Get();   // 메모리 상주
// 1. 새 자산 비동기 로드 (DLC 의 같은 path 의 새 버전 자산)
const TWeakObjectPtr<AMyChar> Self(this);
UAssetManager::GetStreamableManager().RequestAsyncLoad(
    SoftMesh.ToSoftObjectPath(),  // 같은 SoftObjectPath — DLC mount 후 새 .uasset 가리킴
    FStreamableDelegate::CreateLambda([Self, OldMesh]() {
        if (auto* C = Self.Get()) {
            USkeletalMesh* NewMesh = SoftMesh.Get();   // 새 버전
            if (NewMesh != OldMesh) {
                C->GetMesh()->SetSkeletalMeshAsset(NewMesh);
                // OldMesh 는 다른 hard ref 없으면 GC 대상
            }
        }
    }));
```

**함정**:
- *진행 중 AnimMontage* — Old AnimBP 가 사용하던 Montage — 새 Mesh 의 호환 Skeleton 인지 검증 ([[synthesis/mc-validation-policy-rollout]] `MC_ENSURE_SKELETON_COMPAT`)
- *Replication* — Server 만 swap 하면 Client 는 옛 자산 사용. Multicast RPC 로 모든 Client 가 동시 swap 트리거

## 5. (3) BP→C++ 마이그레이션

기존 BP Class `BP_MyEnemy` 를 C++ `AMyEnemy` 로 옮기면서 *기존 저장 게임 / placed level instance* 호환:

```cpp
// 옛 BP 의 UPROPERTY — C++ 로 옮기되 deprecated 마킹
UCLASS()
class AMyEnemy : public ACharacter
{
    // 새 이름 + 기능
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MaxHealth = 100;

    // 옛 이름 — 저장 호환만
    UPROPERTY(meta=(DeprecatedProperty, DeprecationMessage="Use MaxHealth"))
    int32 HP_DEPRECATED;

    virtual void Serialize(FArchive& Ar) override
    {
        Super::Serialize(Ar);
        // 옛 저장 → 새 필드로 마이그레이션
        if (Ar.IsLoading() && Ar.UEVer() < EUnrealEngineVersion::VER_MIGRATE_HP_TO_MAXHEALTH) {
            MaxHealth = HP_DEPRECATED;
        }
    }
};
```

또는 `PostLoad` 에서 마이그레이션:

```cpp
virtual void PostLoad() override
{
    Super::PostLoad();
    if (HP_DEPRECATED != 0) {
        MaxHealth = HP_DEPRECATED;
        HP_DEPRECATED = 0;
    }
}
```

**Reparent 절차** (Editor):
1. C++ `AMyEnemy` 작성 + 컴파일
2. Editor — `BP_MyEnemy` 의 *Class Settings → Parent Class* 를 `AMyEnemy` 로
3. BP 안 *변수 재참조* — 기존 BP UPROPERTY 가 C++ 멤버와 이름 충돌 시 BP 변수 삭제 (C++ 가 우선)
4. 모든 placed instance 재컴파일

## 6. 함정 / 열린 질문

- [ ] **DLC pak 의 같은 path 충돌** — Base 의 `/Game/Player.uasset` vs DLC 의 같은 path → mount order 가 결정. 의도된 swap 인지 vs 실수인지 검증
- [ ] **AssetRegistry 의 Editor only 데이터** — `Tags` 같은 메타가 cooked 안 strip — DLC 의 PrimaryAssetType 은 cooker 에 명시
- [ ] **Live Patch 중 진행 중 AnimNotify** — Notify 가 옛 자산의 Niagara 참조하면 swap 후 nullptr. AnimNotify 자체도 Soft ref 검토 (열린)
- [ ] **메모리 절감 vs 호환성 trade-off** — `bForceRescanExistingAssets=true` 면 모든 자산 재스캔 — CPU 비용 큼. false 면 새 자산만 — 기존 자산 메타 갱신 안 됨
- [ ] **BP→C++ 의 BP function** — BP 만의 함수 (Event Graph) 를 C++ `BlueprintImplementableEvent` 로 변환 — 기존 BP 자손이 그 함수 override 한 게 동작 검증
- [ ] **Save Game 의 SoftObjectPath** — 저장된 SoftObjectPath 가 옛 자산 가리킬 때 — DLC 가 새 path 로 이전한 자산을 redirect 처리 (`UObjectRedirector` 사용)
- [ ] **동시성 — DLC mount 와 Spawn race** — DLC mount 도중 SpawnActor 가 새 자산 path 사용. Mount 완료 까지 Match Start 차단 (열린)
- [ ] **Cooker 의 DLC chunk 분리** — `[/Script/UnrealEd.ProjectPackagingSettings] +AssetChunks=` 설정. Base / DLC chunk 분리 검증 (열린)

## 7. 관련

### Sources

[[sources/ue-build-skill]] · [[sources/ue-coreuobject-cooking]] · [[sources/ue-blueprint-skill]] · [[sources/ue-coreuobject-serialization]] · [[sources/mc-asset-validation-policy]] · [[sources/ue-editor-assetregistry]]

### Entities

[[entities/UBlueprint]] · [[entities/UBlueprintGeneratedClass]] · [[entities/UPackage]] · [[entities/UClass]] · [[entities/IAssetRegistry]]

### Concepts

[[concepts/Cooked-vs-Uncooked]] · [[concepts/Asset-Loading-Policy]] · [[concepts/CPP-BP-Boundary]] · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/Asset-Lifecycle]]

### Related synthesis

[[synthesis/cooked-first-frame-stability]] (DLC Bundle 등록 절차 베이스) · [[synthesis/mc-soft-asset-component-pattern]] (Soft 자산 swap 패턴) · [[synthesis/late-join-reconnect-state-sync]] (DLC 적용 후 합류 state 동기) · [[synthesis/dlc-asset-migration-edge-cases]] (Redirector + Chunk + Mount race + BP override — 본 노트 미해결 해소)
