---
type: synthesis
title: "Cooked Build 첫 프레임 안정성 — DefaultPawnClass/GameMode Soft + Bundle DLC 갱신 + PSO Precache 5.x 통합"
slug: cooked-first-frame-stability
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-build-skill]]"
  - "[[sources/ue-coreuobject-cooking]]"
  - "[[sources/ue-gameframework-gamemode]]"
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-material]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/AGameModeBase]]"
  - "[[entities/UnrealBuildTool]]"
  - "[[entities/UnrealAutomationTool]]"
  - "[[entities/UMaterial]]"
  - "[[entities/UClass]]"
concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Build-Configurations]]"
  - "[[concepts/Match-State]]"
status: living
tags: [synthesis, cooked, dlc, pso, gamemode, soft]
---

# Cooked Build 첫 프레임 안정성

## 1. Thesis

Cooked Build (Shipping / Test / Development cooked) 의 *첫 프레임* 은 5 가지 동시 비용으로 폭발 가능 — **(1) GameMode + DefaultPawnClass hard 참조 → BP CDO 동기 로드 / (2) Map 안 자산 chain hard 로드 / (3) Material PSO 미컴파일 → render thread stall / (4) DLC / Patch 의 새 자산이 PreLoad 안 됨 / (5) BP 컴파일 캐시 미스**. [[synthesis/spawnactor-hitching-4-step-pattern]] 의 SpawnActor 한 호출 단위 4단을 *맵 시작 시점* 으로 확장한 5축 매트릭스. 핵심은 **GameMode 가 모든 hard 참조의 진입점이라는 점** — 거기서 시작해 *Soft 화 + Bundle PreLoad + PSO Precache* 3 종 무기로 첫 프레임을 분산 / 사전 처리.

## 2. 5 축 매트릭스

| 축 | 무엇이 비싼가 | 회피 |
| -- | -- | -- |
| 1 GameMode hard | `AGameMode::DefaultPawnClass = TSubclassOf<>` (hard) → Map 시작 시 Pawn BP 동기 로드 + 그 안 자산 chain | `TSoftClassPtr<>` 로 전환 + Match Start 비동기 로드 |
| 2 Map 자산 chain | LevelStreaming / Sub-level 안 hard `TObjectPtr<>` 멤버들 — 모두 .pak 로드 후 instantiate | LevelStreaming Async + Sub-level 단위 Bundle |
| 3 Material PSO | 첫 draw call 의 shader pipeline 컴파일 — render thread 100~500 ms stall | **PSO Precache 5.x** — `r.PSOPrecaching=1` + `BatchPSO` 자동 |
| 4 DLC / Patch 새 자산 | `UAssetManager::PreloadPrimaryAssets` 가 base asset list 만 — DLC 가 새 PrimaryAssetId 추가해도 안 따라옴 | DLC 마다 `AssetManager::ScanPathsForPrimaryAssets` 후 Bundle 재로드 |
| 5 BP 컴파일 캐시 | BP CDO 첫 access 시 `UBlueprintGeneratedClass::PostLoad` — Function thunk 빌드 | C++ 베이스 + BP 자손 패턴 (BP 가 변경 적은 곳만) |

## 3. PSO Precache 5.x 표준

[[sources/ue-render-shader]] §PSO Precache + [[sources/ue-render-material]] 의 5.x 신기능. Project Settings:

```
[/Script/Engine.RendererSettings]
r.PSOPrecaching=1
r.PSOPrecaching.GlobalShaders=1
r.PSOPrecaching.UseBackgroundThreadForPSOCreation=1
```

빌드 시점에 *cooker 가 모든 사용 Material × Vertex Factory 조합* 을 collect → 게임 시작 시 worker thread 가 사전 컴파일. 첫 draw stall 0.

수동 대상 PSO Precache (Player Character / 핵심 적):

```cpp
// Match Start
USkeletalMeshComponent* PlayerMesh = ...;
PlayerMesh->PrecachePSOs();  // 모든 Material × LOD 조합 큐
```

## 4. GameMode Soft 전환 절차

기존 (히칭 원인):
```cpp
class AMyGameMode : public AGameModeBase
{
    UPROPERTY(EditAnywhere) TSubclassOf<APawn> DefaultPawnClass;  // hard 참조
};
```

변경:
```cpp
class AMyGameMode : public AGameModeBase
{
    UPROPERTY(EditAnywhere) TSoftClassPtr<APawn> SoftPawnClass;
    UPROPERTY(EditAnywhere) FPrimaryAssetType PlayerAssetType{TEXT("Pawn.Player")};

    virtual void BeginPlay() override
    {
        Super::BeginPlay();
        UAssetManager& AM = UAssetManager::Get();
        AM.LoadPrimaryAssetsWithType(PlayerAssetType,
            {TEXT("Game")},  // Bundle name
            FStreamableDelegate::CreateUObject(this, &AMyGameMode::OnPlayerAssetsLoaded));
    }

    void OnPlayerAssetsLoaded()
    {
        // 이제 SoftPawnClass.Get() 즉시 동작
        SetDefaultPawnClass(SoftPawnClass.LoadSynchronous());  // 이미 메모리 — sync 로 OK
    }
};
```

[[concepts/Match-State]] 와 결합 — `WaitingToStart` 단계에서 PreLoad 끝낸 후 `StartMatch`.

## 5. DLC / Patch Bundle 갱신

DLC 설치 시 새 Map / Pawn / Effect 가 들어옴. Cooker 설정 (`DefaultGame.ini`):

```
[/Script/Engine.AssetManagerSettings]
+PrimaryAssetTypesToScan=(PrimaryAssetType="Pawn.DLC", AssetBaseClass="/Script/Engine.Pawn", bHasBlueprintClasses=True, bIsEditorOnly=False, Directories=((Path="/MyDLC/Pawns")))
```

런타임에 DLC pak 마운트 후:

```cpp
UAssetManager& AM = UAssetManager::Get();
AM.ScanPathsForPrimaryAssets(
    FPrimaryAssetType(TEXT("Pawn.DLC")),
    {TEXT("/MyDLC/Pawns")},
    APawn::StaticClass(),
    /*bHasBlueprintClasses=*/true,
    /*bIsEditorOnly=*/false,
    /*bForceSynchronousScan=*/false);
// 이후 LoadPrimaryAssetsWithType 으로 새 PrimaryAssetId 들 로드
```

## 6. 측정 절차

[[synthesis/spawnactor-hitching-4-step-pattern]] §4 의 SpawnActor 측정과 같은 패턴 — Match Start 시점:

```cpp
// 디버그
const double T0 = FPlatformTime::Seconds();
GetWorld()->ServerTravel(TEXT("/Game/Maps/MainMap"));
// OnPostLoadMap 콜백에서 측정
GEngine->OnPostLoadMapWithWorld().AddLambda([T0](UWorld* World) {
    UE_LOG(LogMCAsset, Warning, TEXT("Map load + first frame = %.2f ms"),
        (FPlatformTime::Seconds() - T0) * 1000.0);
});
```

`stat unit` + `stat startfile/stopfile` 로 첫 5 프레임 분석 — `LoadObject` / `Compile Shader` / `BulkSerialize` 가 stack 에 보이면 §2 매트릭스의 어느 축인지 식별.

## 7. 함정 / 열린 질문

- [ ] **PSO Precache 의 cooker 시간 폭발** — Material × Vertex Factory 조합 N×M 컴파일. Cooker 빌드 시간 증가 — CI 시간 trade-off
- [ ] **DLC pak 마운트 순서** — base pak 먼저 / DLC pak 후. ScanPathsForPrimaryAssets 는 후자에 의존
- [ ] **GameMode Soft 전환 시 Login 흐름** — `RestartPlayer` 가 `DefaultPawnClass` 의존 — Match Start 에서 PreLoad 끝나기 *전* 에 Login 들어오면 race. `WaitingToStart` 차단 필요 ([[sources/ue-gameframework-controller]])
- [ ] **PrimaryAsset Bundle 의 Editor only data** — Editor 만 의도된 자산이 PrimaryAsset 으로 등록되면 Cooked 빌드 missing. `bIsEditorOnly=true` 명시
- [ ] **PSO Precache + Mobile** — Mobile (iOS / Android) 은 PSO 대신 *Vulkan Pipeline* / *Metal* 의 별도 캐시. 5.x 표준이지만 플랫폼별 검증 필요 ([[sources/ue-render-mobile]])
- [ ] **BP 컴파일 캐시 (`bCompileBlueprintToCpp`)** — 5.x 부터 deprecated. 대신 BP 자손을 C++ 베이스로 wrap 후 BP 는 데이터만 (열린)
- [ ] **Live Patch (런타임 자산 교체)** — 게임 실행 중 패치 적용 시 메모리상 자산을 새 버전으로 swap. 안전 절차 (열린)

## 8. 관련

### Sources

[[sources/ue-build-skill]] · [[sources/ue-coreuobject-cooking]] · [[sources/ue-gameframework-gamemode]] · [[sources/ue-render-shader]] · [[sources/ue-render-material]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/AGameModeBase]] · [[entities/UnrealBuildTool]] · [[entities/UnrealAutomationTool]] · [[entities/UMaterial]] · [[entities/UClass]]

### Concepts

[[concepts/Cooked-vs-Uncooked]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/Build-Configurations]] · [[concepts/Match-State]]

### Related synthesis

[[synthesis/spawnactor-hitching-4-step-pattern]] (단일 SpawnActor 의 4단 → Map 단위 5축 확장) · [[synthesis/mc-soft-asset-component-pattern]] (컴포넌트 단위 Soft 골격) · [[synthesis/vfx-audio-soft-pool-significance]] (Bundle PreLoad 사례) · [[synthesis/pso-precache-platform-matrix]] (PSO Precache 플랫폼별 상세) · [[synthesis/runtime-dlc-livepatch-rollout]] (DLC 시 PSO 무효화) · [[synthesis/actor-pool-reset-pattern]] (Pool 사전 spawn 으로 첫 프레임 분산)
