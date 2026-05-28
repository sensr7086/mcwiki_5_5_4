---
type: synthesis
title: "MC Validation Policy 일괄 적용 — 다른 MC 컴포넌트 / BP lib / Subsystem + MC_VALIDATE_SKELETON_COMPATIBILITY 헬퍼"
slug: mc-validation-policy-rollout
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/ue-blueprint-skill]]"
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-components-skill]]"
entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/UBlueprint]]"
  - "[[entities/USubsystem]]"
  - "[[entities/USkeletalMeshComponent]]"
concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/CPP-BP-Boundary]]"
status: living
tags: [synthesis, validation, rollout, policy, kmcproject]
---

# MC Validation Policy 일괄 적용

## 1. Thesis

[[concepts/MC-Asset-Validation-Policy]] 가 `UMCSoftSkeletalMeshComponent` 1개에 적용된 상태 — 본 synthesis 는 *전체 KMCProject 모든 모듈* 로 일괄 확장하는 절차 + 새 헬퍼 매크로 (`MC_VALIDATE_SKELETON_COMPATIBILITY`) + 모듈 별 적용 매트릭스. 6 카테고리 — **(1) MC 컴포넌트 6개 (Bouyancy/Move/PartsLoader/CharacterMove/WaterPlane/Camera) + (2) BP-callable lib 2개 (MCActorBlueprintLibrary / MCWaterBlueprintLibrary) + (3) Subsystem 2개 (MCStorySubSystem / MCCameraSubSystem) + (4) Editor module (MCEditorModule) + (5) Asset class (MCStoryAsset / MCPartsAsset) + (6) Helper 신규**.

## 2. 모듈별 적용 매트릭스

| # | 모듈 / 클래스 | 위치 | 적용 우선순위 | 예상 LOG | 예상 ensure |
| -- | -- | -- | -- | -- | -- |
| 1 | `UMCBouyancyComponent` | `Actor/Component/MCBouyancyComponent.h` | 중 | 5~7 (Mesh / Owner / Volume null) | 0~1 (BeginPlay 전 호출) |
| 2 | `UMCMoveComponent` / `UMCCharacterMoveComponent` | `Actor/Component/` | **고** (자주 호출) | 8~12 (CMC / Owner / Velocity) | 1 (Possess 전 호출) |
| 3 | `UMCWaterPlaneComponent` | `Actor/Component/` | 중 | 4~6 (Mesh / Material null) | 0 |
| 4 | `UMCPartsLoaderComponent` | `Actor/Component/` | **고** (자산 로드) | 10~15 (Soft 자산 다수) | 1 (BeginPlay 전 LoadAsync) |
| 5 | `UMCCameraComponent` (custom) | `Actor/Camera/` | 저 | 3~5 | 0 |
| 6 | `UMCActorBlueprintLibrary` | `BlueprintLib/` | **고** (BP 노출) | BP 호출 사이트 마다 | 0 |
| 7 | `UMCWaterBlueprintLibrary` | `BlueprintLib/` | 중 | 5~10 | 0 |
| 8 | `UMCStorySubSystem` | `MCStory/` | **고** (UTickableWorldSubsystem) | 8~12 | 1 (Tickable 진입 전 World null) |
| 9 | `UMCCameraSubSystem` | `Actor/Camera/MCCameraSubSystem.h` | 중 | 5~8 | 0 |
| 10 | `UMCStoryAsset` / `UMCPartsAsset` | `MCStory/` / `MCParts/` | 저 (자주 호출 X) | 3~5 | 1 (Cooked 자산 결손) |

총 예상 — LOG 사이트 ~70 / ensure 사이트 ~5. 본 synthesis 가 끝나면 KMCProject 전체 silent return 0.

## 3. 신규 헬퍼 매크로 — `MC_VALIDATE_SKELETON_COMPATIBILITY`

[[sources/ue-assetclasses-mesh]] §7 함정 #3 — Skeleton 미호환 SkeletalMesh swap 시 AnimInstance 깨짐. KMCProject 의 ensure 사이트:

```cpp
// MCAssetValidation.h 추가
/**
 * Skeleton 호환 검증 — 새 SkeletalMesh 가 기존 Skeleton (또는 Compatible 등록) 과 호환?
 * 호환 안 되면 ensure 발화 + return.
 *
 * vault: [[sources/ue-assetclasses-mesh]] §2.2 (Compatible Skeleton 5.x), §7 #3 (함정)
 */
#define MC_ENSURE_SKELETON_COMPAT(MeshComp, NewMesh) \
    do { \
        const USkeletalMesh* CurMesh = (MeshComp)->GetSkeletalMeshAsset(); \
        if (CurMesh && (NewMesh)) { \
            const USkeleton* CurSkel = CurMesh->GetSkeleton(); \
            const USkeleton* NewSkel = (NewMesh)->GetSkeleton(); \
            const bool bSame = (CurSkel == NewSkel); \
            const bool bCompat = bSame || (CurSkel && CurSkel->IsCompatibleForEditor(NewSkel)); \
            if (!ensureMsgf(bCompat, \
                TEXT("[%s::%hs] Skeleton mismatch — '%s' (current) vs '%s' (new)"), \
                *GetNameSafe(this), __FUNCTION__, \
                *GetNameSafe(CurSkel), *GetNameSafe(NewSkel))) \
            { \
                return; \
            } \
        } \
    } while (0)

// 사용 예 — UMCSoftSkeletalMeshComponent::ApplyLoadedAssets
void UMCSoftSkeletalMeshComponent::ApplyLoadedAssets()
{
    USkeletalMesh* LoadedMesh = SoftSkeletalMesh.Get();
    MC_LOGRET_IF_NULL(LoadedMesh, "Cooked asset missing");
    MC_ENSURE_SKELETON_COMPAT(this, LoadedMesh);   // 신규
    SetSkeletalMeshAsset(LoadedMesh);
    // ...
}
```

## 4. BP-callable lib 통합 패턴

[[sources/mc-asset-validation-policy]] §9 의 미해결 — BP 측 디버그 메시지. BP 노출 함수의 LOG 매크로:

```cpp
// MCActorBlueprintLibrary.cpp — BP 호출 진입점에 의무
UFUNCTION(BlueprintCallable)
static void GetActorByTag(UObject* WorldContext, FName Tag, AActor*& OutActor)
{
    OutActor = nullptr;
    UWorld* W = GEngine->GetWorldFromContextObjectChecked(WorldContext);
    MC_LOGRET_IF_NULL(W, "WorldContext invalid");
    MC_LOGRET_IF_FALSE(!Tag.IsNone(), "Tag is NAME_None");
    // ... 검색
}
```

추가 — BP 측 *Print String* 으로 디버그 출력 (Editor / Development 만):

```cpp
#if !UE_BUILD_SHIPPING
#define MC_LOGRET_IF_NULL_BP(Ptr, Reason) \
    do { \
        if ((Ptr) == nullptr) { \
            UE_LOG(LogMCAsset, Warning, ...); \
            UKismetSystemLibrary::PrintString(this, FString::Printf(TEXT("[MC] %s"), TEXT(Reason)), \
                /*bPrintToScreen=*/true, /*bPrintToLog=*/false, FLinearColor::Red, 5.f); \
            return; \
        } \
    } while (0)
#else
#define MC_LOGRET_IF_NULL_BP(Ptr, Reason) MC_LOGRET_IF_NULL(Ptr, Reason)
#endif
```

## 5. Subsystem 적용 — `UMCStorySubSystem` 사례

`UTickableWorldSubsystem` 자손 — Tick 안 silent return 가드 다수:

```cpp
// before
void UMCStorySubSystem::Tick(float Dt)
{
    if (!CurrentAsset) return;
    if (!CurrentNode) return;
    CurrentNode->Tick(Dt);
}

// after — 정책 적용
void UMCStorySubSystem::Tick(float Dt)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMCStorySubSystem::Tick);
    MC_LOGRET_IF_NULL(CurrentAsset, "No story asset registered — RegisterStory first");
    MC_LOGRET_IF_NULL(CurrentNode, "Story state invalid — CurrentNode null mid-execution");
    CurrentNode->Tick(Dt);
}
```

WITH_EDITOR 경로의 ensure (`UnsafeDuringActorConstruction` 같은 케이스):

```cpp
#if WITH_EDITOR
void UMCStorySubSystem::SetRuntimeBreakPointNode(UMCStory_Node* Node)
{
    MC_ENSURE_AND_RETURN(IsValid(Node), "Cannot set breakpoint on invalid node");
    MC_ENSURE_AND_RETURN(GIsEditor, "WITH_EDITOR API called outside editor");
    BreakPointNode = Node;
}
#endif
```

## 6. 적용 절차 (per 모듈)

1. `#include "KMCProject/MCPlayModule/Core/MCAssetValidation.h"`
2. silent return 사이트 식별 — `grep "if .* return;"` 으로 후보 수집
3. 매크로로 갈아끼움 — Reason 문자열에 *왜* 명시
4. ensure 후보 식별 — Constructor 안 / 초기화 단계 호출 / 정책 위반
5. 빌드 + Editor 실행 → 로그 검증 (예상 LOG 가 발화하는가)
6. (선택) 단위 테스트 — 각 LOG 사이트가 의도대로 발화하는지

## 7. 함정 / 열린 질문

- [ ] **매크로 남용** — 모든 nullptr 검사를 LOG 로 만들면 노이즈. Verbose 등급 활용 + *이 케이스가 디버깅 가치 있는가* 결정 (열린 — gut feeling)
- [ ] **Critical 영역 (Render thread / Physics tick)** 의 LOG 비용 — 본 정책은 GameThread 만. RHI / Physics tick 안 LOG 는 별도 고려
- [ ] **`check`** 사용 결정 — 데이터 손상 / 보안 critical 케이스. 본 정책은 ensure 만 — 추후 `MC_CHECK_*` 매크로 추가 시점 (열린)
- [ ] **로그 카테고리 다중화** — `LogMCAsset` 외에 `LogMCStory` / `LogMCParts` 별도? 또는 한 카테고리에 prefix 로 구분 — 후자 권장 (필터링 단순)
- [ ] **자동 적용 도구** — Python script / IDE plugin 으로 silent return → MC_LOGRET 자동 변환. 현재는 수동 (열린)
- [ ] **Eval Plugin (`ue-wiki-llm:evaluate`)** 으로 적용 후 코드 채점 — 정책 준수도 측정 (열린)

## 8. 관련

### Sources

[[sources/mc-asset-validation-policy]] · [[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/ue-blueprint-skill]] · [[sources/ue-subsystem-skill]] · [[sources/ue-components-skill]]

### Entities

[[entities/UActorComponent]] · [[entities/UBlueprint]] · [[entities/USubsystem]] · [[entities/USkeletalMeshComponent]]

### Concepts

[[concepts/MC-Asset-Validation-Policy]] · [[concepts/Component-Policies-6]] · [[concepts/Asset-Loading-Policy]] · [[concepts/CPP-BP-Boundary]]

### Related synthesis

[[synthesis/mc-soft-asset-component-pattern]] (Soft 컴포넌트 검증 표준) · [[synthesis/actor-lifecycle-edge-cases]] (idempotent 가드 매크로 사용처) · [[synthesis/mc-character-hit-reaction-pipeline]] (적용 1차 사례) · [[synthesis/lint-2026-05-10-mcsoft-components]] (1차 적용 후 audit — 16 결함 식별 / 14 fix)
