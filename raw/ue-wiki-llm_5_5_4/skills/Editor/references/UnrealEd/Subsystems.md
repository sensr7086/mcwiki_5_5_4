---
name: unrealed-subsystems
description: 🛠 UEditorSubsystem + UEditorActorSubsystem + UEditorAssetSubsystem + UEditorLevelLibrary 자동 등록.
---

# UnrealEd · Subsystems sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: `Engine/Source/Editor/UnrealEd/Public/Subsystems/`
> **다루는 범위**: 에디터 서브시스템 12개 — `UEditorSubsystem` 베이스(`EditorSubsystem` 모듈)에서 파생, `GEditor->GetEditorSubsystem<T>()` 로 접근.

---

## 1. 개요

UE 에디터의 **싱글턴 헬퍼**. UMG의 `UGameInstanceSubsystem` 처럼 자동 인스턴스화·라이프사이클 관리. 에디터 시작 시 `Initialize`, 종료 시 `Deinitialize` 호출.

**특징**:
- `UEditorSubsystem` 베이스 (모듈: `EditorSubsystem`, 헤더: `EditorSubsystem.h`)
- `GEditor` (UEditorEngine 글로벌) 가 컬렉션 보유 → `GEditor->GetEditorSubsystem<T>()` 로 접근
- 일부는 `UFUNCTION(BlueprintCallable)` 노출 → Editor Utility Blueprint / Python 에서 호출 가능
- 거의 전부가 **에디터 빌드 전용** (`WITH_EDITOR`)

---

## 2. 12개 서브시스템 한 줄 요약

| # | 클래스 | 헤더 | 핵심 책임 |
|---|--------|------|-----------|
| 1 | `UAssetEditorSubsystem` | `AssetEditorSubsystem.h` | **에셋 더블클릭/오픈 라우팅** — `OpenEditorForAsset` / `CloseAllEditorsForAsset` / `FindEditorForAsset` (가장 자주 사용) |
| 2 | `UEditorActorSubsystem` | `EditorActorSubsystem.h` | 레벨 액터 일괄 조작 — Spawn / Destroy / Select / SetActorTransform / ConvertActor (Editor Scripting) |
| 3 | `UEditorAssetSubsystem` | `EditorAssetSubsystem.h` | Asset 파일 조작 — Save / Delete / Rename / Duplicate / GetAssetClass / 메타데이터 |
| 4 | `UImportSubsystem` | `ImportSubsystem.h` | Asset 임포트 라우팅 — `ImportFile` + Reimport 콜백 + Interchange 통합 |
| 5 | `UPanelExtensionSubsystem` | `PanelExtensionSubsystem.h` | 임의 위젯 패널에 외부 모듈이 항목 추가 (확장점 등록) |
| 6 | `UPropertyVisibilityOverrideSubsystem` | `PropertyVisibilityOverrideSubsystem.h` | UPROPERTY 가시성 동적 오버라이드 (디테일 패널) — ⚠ **5.5 에는 없음 (5.7+ 추가)** |
| 7 | `UBrowseToAssetOverrideSubsystem` | `BrowseToAssetOverrideSubsystem.h` | 컨텐츠 브라우저 "Browse to" 동작 오버라이드 |
| 8 | `UBrushEditingSubsystem` | `BrushEditingSubsystem.h` | BSP 브러시 편집 |
| 9 | `UCollectionManagerScriptingSubsystem` | `CollectionManagerScriptingSubsystem.h` | 컨텐츠 브라우저 컬렉션 (Editor Scripting) — ⚠ **5.5 에는 없음 (5.7+ 추가)** |
| 10 | `UActorEditorContextSubsystem` | `ActorEditorContextSubsystem.h` | 액터 배치 시 컨텍스트 (현재 폴더·레벨 등) |
| 11 | `UUnrealEditorSubsystem` | `UnrealEditorSubsystem.h` | 잡다한 에디터 헬퍼 (스크린샷·뷰포트 등) |
| 12 | `UEditorSubsystemBlueprintLibrary` | `EditorSubsystemBlueprintLibrary.h` | (서브시스템은 아니지만) UEditorSubsystem 의 BP 헬퍼 |

---

## 3. 가장 자주 쓰는 — UAssetEditorSubsystem

### 3.1 자주 쓰는 API (AssetEditorSubsystem.h)

| API | 라인 | 메모 |
|-----|------|------|
| `bool OpenEditorForAsset(UObject* Asset, EAssetTypeActivationOpenedMethod = Edit, EAssetEditorToolkitFocusOption = FocusIfOpen)` | L138 | **가장 자주 호출** — 에셋 에디터 열기 |
| `bool OpenEditorForAssets(const TArray<UObject*>& Assets, ...)` | L162 | 다중 에셋 |
| `void CloseAllEditorsForAsset(UObject* Asset)` | (헤더) | 닫기 |
| `void CloseAllAssetEditors()` | (헤더) | 모두 닫기 |
| `IAssetEditorInstance* FindEditorForAsset(UObject* Asset, bool bFocusIfOpen)` | (헤더) | 진행 중 인스턴스 찾기 (없으면 nullptr) |
| `TArray<IAssetEditorInstance*> FindEditorsForAsset(UObject* Asset)` | (헤더) | 다중 |
| `bool NotifyAssetClosed(UObject* Asset, IAssetEditorInstance* InInstance)` | (헤더) | 닫힘 통지 |

### 3.2 이벤트 델리게이트 (콜백)

| 델리게이트 | 라인 | 의미 |
|-----------|------|------|
| `FAssetEditorRequestCloseEvent& OnAssetEditorRequestClose()` | L176 | 닫기 요청 (브로드캐스트) |
| `FOnAssetOpenedInEditorEvent& OnAssetOpenedInEditor()` | L190 | 에셋 열림 |
| `FOnAssetsOpenedInEditorEvent& OnEditorOpeningPreWidgets()` | L197 | 열리기 직전 (위젯 생성 전) |
| `FOnAssetClosedInEditorEvent& OnAssetClosedInEditor()` | L204 | 닫힘 |
| `FAssetEditorRequestOpenEvent& OnAssetEditorRequestedOpen()` | L214 | 열기 요청 (가로채기 가능) |

### 3.3 사용 패턴

```cpp
#if WITH_EDITOR
if (UAssetEditorSubsystem* Sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
{
    // 에셋 열기
    Sub->OpenEditorForAsset(MyAsset);

    // 모든 에디터 인스턴스 찾기
    TArray<IAssetEditorInstance*> Editors = Sub->FindEditorsForAsset(MyAsset);

    // 닫기
    Sub->CloseAllEditorsForAsset(MyAsset);

    // 옵서버 등록
    Sub->OnAssetOpenedInEditor().AddUObject(this, &UMyEditorTool::HandleAssetOpened);
}
#endif
```

---

## 4. UEditorActorSubsystem (자주 사용 — Editor Scripting)

`UFUNCTION(BlueprintCallable)` 노출된 메서드가 다수 — Editor Utility Blueprint / Python 에서 액터 일괄 조작.

| API 카테고리 | 메서드 |
|-------------|--------|
| 스폰 | `SpawnActorFromObject` · `SpawnActorFromClass` |
| 파괴 | `DestroyActor` · `DestroyActors` |
| 선택 | `GetSelectedLevelActors` · `SetSelectedLevelActors` · `SelectNothing` · `SetActorSelectionState` |
| 변환 | `SetActorTransform` · `SetActorLocation` · `SetActorRotation` |
| 변환 컨버터 | `ConvertActorWith` · `ConvertActors` |
| 일괄 | `GetAllLevelActors` · `GetAllLevelActorsComponents` |
| 가시성 | `SetActorVisibility` · `SetActorTemporarilyHiddenInEditor` |

```cpp
// C++ 에서
if (UEditorActorSubsystem* Actor = GEditor->GetEditorSubsystem<UEditorActorSubsystem>())
{
    TArray<AActor*> Selected = Actor->GetSelectedLevelActors();
    for (AActor* A : Selected) { Actor->SetActorTransform(A, FTransform::Identity); }
}
```

---

## 5. UEditorAssetSubsystem (Asset 파일 조작)

| API | 메모 |
|-----|------|
| `bool SaveAsset(FString AssetPathToSave, bool bOnlyIfIsDirty)` | 단일 저장 |
| `bool SaveLoadedAsset(UObject* AssetToSave, bool bOnlyIfIsDirty)` | 로드된 객체 저장 |
| `bool DeleteAsset(FString AssetPathToDelete)` | 삭제 |
| `bool DuplicateAsset(FString SourceAssetPath, FString DestinationAssetPath)` | 복제 |
| `bool RenameAsset(FString SourceAssetPath, FString DestinationAssetPath)` | 이름 변경 |
| `UClass* GetAssetClass(FString AssetPath)` | 메타데이터 |
| `bool DoesAssetExist(FString AssetPath)` | 존재 검사 |

---

## 6. UImportSubsystem (Asset 임포트)

5.x Interchange 시스템의 게이트웨이. 외부 파일 → UObject 변환 라우팅.

| API | 메모 |
|-----|------|
| `void ImportFile(FString InFilePath)` | 단일 파일 임포트 |
| `void ImportNextTick(...)` | 다음 틱에 임포트 (재귀 방지) |
| 콜백 | `OnAssetPostImport` / `OnAssetReimport` / `OnAssetPreImport` (브로드캐스트) |

---

## 7. UEditorSubsystem 베이스 — 새 서브시스템 작성

```cpp
#if WITH_EDITOR
UCLASS()
class MYGAMEEDITOR_API UMyEditorSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);                          // ← Super FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorSubsystem_Init);  // ← 프로파일링 스코프
        // 외부 시스템 구독·캐시 초기화
    }
    virtual void Deinitialize() override
    {
        // 정리 (구독 해제 등)
        Super::Deinitialize();                                  // ← Super LAST
    }

    UFUNCTION(BlueprintCallable, Category="My Tool")
    void DoSomething();
};
#endif
```

**자동 인스턴스화 조건**: `UCLASS()` + `UEditorSubsystem` 자손 + 모듈 로딩. 사용:

```cpp
if (UMyEditorSubsystem* My = GEditor->GetEditorSubsystem<UMyEditorSubsystem>())
{
    My->DoSomething();
}
```

`Initialize` / `Deinitialize` Super 호출 규약 — [`04_OverrideIndex.md §6.1`](../../../references/04_OverrideIndex.md).

---

## 8. 가상 함수 / 콜백 표

### 8.1 UEditorSubsystem 베이스 virtual

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `virtual void Initialize(FSubsystemCollectionBase&)` | **FIRST** | 인스턴스 초기화 — 외부 구독 / 캐시 |
| `virtual void Deinitialize()` | **LAST** | 정리 |
| `virtual TStatId GetStatId() const` (`FTickableEditorObject` 통합 시) | (override) | Stat 식별 |
| `virtual bool ShouldCreateSubsystem(UObject* Outer) const { return true; }` | (선택) | 생성 조건 동적 결정 |

### 8.2 IAssetEditorInstance 인터페이스 (UAssetEditorSubsystem이 관리)

(`AssetEditorSubsystem.h` L59~L91 — `IAssetEditorInstance` 인터페이스)

| 시그니처 | 라인 | PURE | 의미 |
|----------|------|------|------|
| `virtual FName GetEditorName() const = 0` | L59 | ✅ | 에디터 이름 |
| `virtual void FocusWindow(UObject* ObjectToFocusOn = nullptr) = 0` | L60 | ✅ | 포커스 |
| `virtual bool CloseWindow() { return true; }` | L63 | | 닫기 |
| `virtual bool CloseWindow(EAssetEditorCloseReason InCloseReason)` | L65 | | 이유 명시 닫기 |
| `virtual bool IsPrimaryEditor() const = 0` | L83 | ✅ | 주 에디터인지 |
| `virtual void InvokeTab(const FTabId& TabId) = 0` | L84 | ✅ | 탭 활성화 |
| `virtual TSharedPtr<FTabManager> GetAssociatedTabManager() = 0` | L88 | ✅ | TabManager |
| `virtual double GetLastActivationTime() = 0` | L89 | ✅ | 마지막 활성 시각 |
| `virtual void RemoveEditingAsset(UObject* Asset) = 0` | L90 | ✅ | 편집 객체 제거 |

`FAssetEditorToolkit` 이 이 인터페이스를 구현 — 사용자 정의 에셋 에디터는 자동으로 `IAssetEditorInstance` 가 됨.

---

## 9. 함정 / 안티패턴

| 함정 | 회피 |
|------|------|
| 게임 모듈에서 `GEditor` 접근 | `#if WITH_EDITOR` 가드 + Editor 모듈로 분리 |
| `Initialize` Super 누락 | Super FIRST 의무 |
| `Deinitialize` 에서 Super 먼저 호출 | Super LAST — 사용자 cleanup 후 |
| 서브시스템에서 `Tick` 안 함 → 매 프레임 작업 | `FTickableEditorObject` 다중 상속 또는 Timer 사용 + 스코프 |
| `OpenEditorForAsset` 결과 nullptr 검사 누락 | 에셋 종류·플러그인에 따라 실패 가능 |
| Singleton이라 가정해 캐싱 | 매 사용시 `GEditor->GetEditorSubsystem<T>()` 호출 권장 (모듈 리로드 대응) |
| BP 노출 후 빈 메서드 | `UFUNCTION(BlueprintCallable)` 만 있고 구현 안 하면 BP에서 빈 호출 |
| 옵서버 콜백 스코프 누락 | `OnAssetOpenedInEditor` 등 모든 핸들러에 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 스코프 부착 |

---

## 10. 에디터 전용 표기 🛠

본 sub-skill의 모든 클래스는 **에디터 빌드 전용** (`WITH_EDITOR`). Module 의존: `EditorSubsystem` + `UnrealEd`. uplugin Type Editor.

자세한 4단 분리 — [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 11. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — UnrealEd 메인
- [`UnrealEd/AssetEditorToolkit`](../AssetEditorToolkit/SKILL.md) — `OpenEditorForAsset` 가 호출하는 것 (FAssetEditorToolkit 자손)
- [`UnrealEd/Factories`](../Factories/SKILL.md) — `UImportSubsystem` 의 임포트 파이프라인 베이스
- [`UnrealEd/Elements`](../Elements/SKILL.md) — `UEditorActorSubsystem` 의 5.x 선택은 Element System
- [`CoreUObject/Editor`](../../CoreUObject/references/Editor.md) — PostEditChange (서브시스템에서 옵서버)
- 교차 인덱스: [`04_OverrideIndex.md §6.1`](../../../references/04_OverrideIndex.md) (Initialize/Deinitialize Super) · [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) (4단 분리) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Subsystem 콜백 스코프)
