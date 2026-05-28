---
type: synthesis
title: "DLC 자산 마이그레이션 엣지 케이스 — SoftObjectPath Redirector + Cooker chunk + DLC mount race + BP function override"
slug: dlc-asset-migration-edge-cases
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-build-skill]]"
  - "[[sources/ue-coreuobject-cooking]]"
  - "[[sources/ue-coreuobject-package]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[sources/ue-blueprint-skill]]"
  - "[[sources/ue-editor-assetregistry]]"
entities:
  - "[[entities/UBlueprint]]"
  - "[[entities/UBlueprintGeneratedClass]]"
  - "[[entities/UPackage]]"
  - "[[entities/IAssetRegistry]]"
concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/CPP-BP-Boundary]]"
status: living
tags: [synthesis, dlc, redirector, cooker-chunk, bp-override, edge-cases]
---

# DLC 자산 마이그레이션 엣지 케이스

## 1. Thesis

[[synthesis/runtime-dlc-livepatch-rollout]] 의 미해결 — *SoftObjectPath redirector* / *Cooker chunk 분리* / *DLC mount 와 Spawn race* / *BP→C++ 마이그 시 function override* — 4 가지 엣지 케이스. 각각 별개의 문제처럼 보이지만 **모두 "기존 path/class 가 어딘가에서 살아있는 채 새 path/class 가 들어옴"** 의 변형. 본 synthesis 는 4 케이스의 *공통 메커니즘* (`UObjectRedirector` / `FCoreDelegates::OnPakLoaded` / `UClass::ClassGeneratedBy`) + 각각의 표준 패턴 + 함정.

## 2. 4 케이스 매트릭스

| 케이스 | 무엇이 살아있는가 | 무엇이 새로 들어오는가 | 메커니즘 |
| -- | -- | -- | -- |
| SoftObjectPath redirector | 옛 path 의 Save Game | 새 path (자산 이동) | `UObjectRedirector` — 옛 path 가 새 path 로 redirect |
| Cooker chunk 분리 | Base pak 의 자산 | DLC pak 의 같은 자산 새 버전 | `+AssetChunks` 설정 + Pak Mount Priority |
| DLC mount 와 Spawn race | DLC pak mount 진행 중 | 게임 코드 의 SpawnActor 호출 | Mount 완료 기다림 (FCoreDelegates::OnPakFileMounted) |
| BP→C++ function override | BP 자손의 BlueprintImplementableEvent | C++ 부모의 같은 함수 (재정의) | `UFUNCTION(BlueprintNativeEvent)` 의 _Implementation 검증 |

## 3. (1) SoftObjectPath Redirector

자산을 폴더 이동하면 옛 path 의 Save 게임 / 다른 자산의 hard ref 가 깨짐. UE 가 *redirector* 자동 생성 — 옛 path 에 `UObjectRedirector` 가 새 path 지시:

```cpp
// 옛 path 의 .uasset = UObjectRedirector instance
class UObjectRedirector : public UObject
{
    UPROPERTY()
    TObjectPtr<UObject> DestinationObject;  // 새 path 가리킴
};

// 런타임 — SoftObjectPath.LoadSynchronous() 가 자동 redirect 따라감
TSoftObjectPtr<UStaticMesh> OldPath(FSoftObjectPath("/Game/OldFolder/Asset.Asset"));
UStaticMesh* Mesh = OldPath.LoadSynchronous();  // 새 path 의 자산 반환
```

**Cooker 측** — `[/Script/UnrealEd.ProjectPackagingSettings] +DirectoriesToAlwaysCook` 또는 fix-up redirectors (Editor: Asset menu → Fix up redirectors) 로 영구 해결. DLC 가 옛 path 자산을 *완전 제거* 하려면 redirector 도 함께 cook.

## 4. (2) Cooker chunk 분리

Base + DLC 빌드 시 자산이 *어느 chunk 에 들어가는가* 결정:

```ini
[/Script/UnrealEd.ProjectPackagingSettings]
+AssetChunks=(ChunkId=0, Paths=("/Game/Base/"))      ; chunk 0 = base pak
+AssetChunks=(ChunkId=1, Paths=("/Game/DLC1/"))      ; chunk 1 = DLC1 pak
+AssetChunks=(ChunkId=2, Paths=("/Game/DLC2/"))      ; chunk 2 = DLC2 pak
```

빌드 결과 — `<Project>-WindowsNoEditor-Base.pak` + `-DLC1.pak` + `-DLC2.pak`.

**의존 cascade**: DLC1 의 자산이 Base 의 자산을 hard 참조 → 자동으로 Base 도 함께 cook. DLC 별도 빌드 시 `IsDLCAssetAlreadyInBase` 검증 — base pak 가 이미 들어있으면 DLC chunk 에서 제외.

## 5. (3) DLC Mount 와 Spawn Race

DLC pak mount 가 진행 중 게임 코드가 SpawnActor → 자산 미로드. Mount 완료 기다림:

```cpp
// GameInstance::OnStart
FString DLCPath = FPaths::ProjectContentDir() / TEXT("DLC/MyDLC.pak");
TSharedPtr<FFutureMountResult> MountFuture = MakeShared<FFutureMountResult>();

FCoreDelegates::OnPakFileMounted2.AddLambda([MountFuture, DLCPath](const IPakFile& Pak) {
    if (Pak.PakGetPakFilename() == DLCPath) {
        MountFuture->bComplete = true;
    }
});

FCoreDelegates::OnMountPak.Execute(DLCPath, /*Order=*/1000, /*MountPoint=*/TEXT(""));

// Match Start 차단 — Mount 완료까지 대기
while (!MountFuture->bComplete) {
    FPlatformProcess::Sleep(0.01f);  // 또는 비동기 Task
}
// 이제 안전하게 DLC 자산 SpawnActor
```

또는 [[synthesis/cooked-first-frame-stability]] §4 의 Match State `WaitingToStart` 단계에서 Mount + Bundle PreLoad 끝나기 *전* 에 `StartMatch` 안 함.

## 6. (4) BP→C++ Function Override

C++ 부모에 새 함수 추가 → 옛 BP 자손이 같은 이름 함수 가지면 충돌:

```cpp
// C++ 새 부모
class AMyEnemy : public ACharacter
{
    // 새 함수 — BP 가 override 가능
    UFUNCTION(BlueprintNativeEvent, Category="Combat")
    void OnDamaged(float Damage);

    void OnDamaged_Implementation(float Damage)
    {
        // C++ 기본 구현
        HP -= Damage;
    }
};

// 옛 BP 자손 — "OnDamaged" 함수가 *BP Event Graph 안에* 같은 이름 존재 가능
// → BP 컴파일러가 자동 override 인식 + _Implementation 호출 안 함 (BP 가 우선)
//   단, BP 가 Parent: Call to OnDamaged 노드를 두면 C++ Implementation 도 호출
```

**검증** (Editor):
1. Recompile 시 BP 컴파일러가 "BlueprintNativeEvent override" 표시 — BP Event Graph 에 *Override* 메뉴로 자동 추가
2. BP 가 Parent 호출 안 하면 C++ Implementation 무시 → 의도 안 한 동작
3. 검증 — Editor Output Log 의 *Blueprint Compilation* warning 모니터

## 7. 함정 / 열린 질문

- [ ] **Redirector 의 *recursive redirect*** — A → B → C chain 이면 LoadSynchronous 가 모두 따라감. 4단계 넘으면 경고. fix-up redirectors 권장
- [ ] **Cooker chunk 의 *cross-DLC 의존*** — DLC2 가 DLC1 자산 참조 → DLC2 가 *DLC1 mount 보장 못 함*. DLC 의존성 명시 (manifest) 또는 cross-DLC 차단
- [ ] **DLC Mount 의 *Loading Screen* 동기화** — Mount 진행 중 UI Loading Screen 표시 (FCoreDelegates::OnPakFileMounted progress callback 사용)
- [ ] **BP→C++ 마이그 시 *_DEPRECATED 멤버 cleanup*** — 일정 버전 후 `HP_DEPRECATED` 제거 — Save Game 마이그레이션 끝난 것 확인 후
- [ ] **BP 가 *parent 호출 없이* override 한 경우** — C++ 부모의 새 로직 안 돌아감. *반드시 Parent 호출* 코드 컨벤션 추가 + clang-tidy / Editor warning
- [ ] **Cooker chunk + Live Patch** — Live Patch 가 새 chunk 추가 시 옛 mount 와 충돌. Mount Priority 재정렬 필요
- [ ] **SoftObjectPath 의 *DLC 전용 path*** — DLC 만의 path (`/MyDLC/Pawns/...`) — Base 빌드는 `IsNull()` 반환. 조건부 spawn 패턴 (`if (!Path.IsNull() && Path.LoadSynchronous())`)
- [ ] **Editor 의 *Fix up redirectors* 자동화** — CI 빌드 단계에 포함 — `UnrealEditor-Cmd.exe -run=ResavePackages -FixupRedirects` (열린)

## 8. 관련

### Sources

[[sources/ue-build-skill]] · [[sources/ue-coreuobject-cooking]] · [[sources/ue-coreuobject-package]] · [[sources/ue-coreuobject-serialization]] · [[sources/ue-blueprint-skill]] · [[sources/ue-editor-assetregistry]]

### Entities

[[entities/UBlueprint]] · [[entities/UBlueprintGeneratedClass]] · [[entities/UPackage]] · [[entities/IAssetRegistry]]

### Concepts

[[concepts/Cooked-vs-Uncooked]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/CPP-BP-Boundary]]

### Related synthesis

[[synthesis/runtime-dlc-livepatch-rollout]] (베이스 — DLC + Live Patch + BP→C++) · [[synthesis/cooked-first-frame-stability]] (Mount Race 와 Match Start 결합) · [[synthesis/spawnactor-hitching-4-step-pattern]] (DLC Class load)
