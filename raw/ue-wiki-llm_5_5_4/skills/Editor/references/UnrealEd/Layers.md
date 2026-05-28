---
name: unrealed-layers
description: 🛠 ULayersSubsystem + ULayer + 5.x DataLayer 시스템.
---

# UnrealEd · Layers sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: `Engine/Source/Editor/UnrealEd/Public/Layers/` + `Public/Bookmarks/` + `Public/WorldPartition/`
> **다루는 범위**: 레이어 가시성/잠금 + 카메라 북마크 + WorldPartition 빌더 통합.

---

## 1. 개요

레벨 에디팅 시각화·관리 도구 묶음:

- **Layers** — 액터를 레이어로 묶어 가시성·잠금 토글 (`ULayersSubsystem`)
- **Bookmarks** — 카메라 위치 저장/복원 (BookMark Slot 0~9)
- **WorldPartition** — 5.x 신규 — 동적 로드 영역 분할 + Builder 도구

---

## 2. Layers (`Public/Layers/LayersSubsystem.h`)

### 2.1 ULayersSubsystem (UEditorSubsystem)

```cpp
class ULayersSubsystem : public UEditorSubsystem
```

핵심 API:

| API | 의미 |
|-----|------|
| `bool TryGetLayer(FName LayerName, ULayer*& OutLayer)` | 레이어 조회 |
| `ULayer* CreateLayer(FName LayerName)` | 새 레이어 |
| `void DeleteLayer(FName LayerName)` | 삭제 |
| `void DeleteLayers(const TArray<FName>&)` | 일괄 |
| `void RenameLayer(FName OldName, FName NewName)` | 이름 변경 |
| `void AddActorToLayer(AActor*, FName)` / `AddActorsToLayer` | 액터 → 레이어 |
| `void RemoveActorFromLayer(AActor*, FName)` | 제거 |
| `bool IsLayerVisible(FName)` / `SetLayerVisibility(FName, bool)` | 가시성 |
| `bool IsLayerLocked(FName)` / `SetLayerLocked(FName, bool)` | 잠금 |
| `void SelectActorsInLayer(FName, bool bSelect, bool bNotify)` | 일괄 선택 |
| `TArray<FName> GetLayerNames()` | 전체 레이어 |

### 2.2 사용 패턴

```cpp
#if WITH_EDITOR
if (ULayersSubsystem* Layers = GEditor->GetEditorSubsystem<ULayersSubsystem>())
{
    Layers->CreateLayer(FName("Enemies"));
    for (AActor* A : EnemyActors)
    {
        Layers->AddActorToLayer(A, FName("Enemies"));
    }
    Layers->SetLayerVisibility(FName("Enemies"), false);    // 일괄 숨김
}
#endif
```

---

## 3. Bookmarks (`Public/Bookmarks/`)

### 3.1 핵심 헤더

| 헤더 | 의미 |
|------|------|
| `IBookmarkTypeActions.h` | 인터페이스 — 북마크 타입 별 동작 |
| `IBookmarkTypeTools.h` | 툴 인터페이스 |
| `BookMarkTypeActions.h` | 기본 구현 |
| `BookmarkSingleViewportActions.h` | 단일 뷰포트 북마크 |
| `BookmarkScoped.h` | RAII scope |
| `BookmarkUI.h` | UI 헬퍼 |

### 3.2 사용

레벨 에디터에서 `Ctrl+1~9` 으로 카메라 위치 저장, `1~9` 로 복원. 사용자가 직접 다룰 일은 드물고, 커스텀 뷰포트 도구를 만들 때 `IBookmarkTypeActions` 자손 작성:

```cpp
class FMyBookmarkActions : public IBookmarkTypeActions
{
    virtual TSubclassOf<UBookmarkBase> GetBookmarkClass() override;
    virtual void InitFromViewport(UBookmarkBase* InBookmark, FEditorViewportClient& InViewport) override;
    virtual void JumpToBookmark(UBookmarkBase* InBookmark, const TSharedPtr<struct FBookmarkBaseJumpToSettings>& InSettings, FEditorViewportClient& InViewport) override;
};
```

---

## 4. WorldPartition Builder (`Public/WorldPartition/`)

### 4.1 핵심 클래스

| 클래스 | 헤더 | 의미 |
|--------|------|------|
| `UWorldPartitionBuilder` (베이스) | `WorldPartitionBuilder.h` | 5.x 신규 빌더 베이스 |
| `UWorldPartitionFoliageBuilder` | `WorldPartitionFoliageBuilder.h` | 폴리지 빌더 |
| `UWorldPartitionHLODsBuilder` | `WorldPartitionHLODsBuilder.h` | HLOD 빌더 |
| `UWorldPartitionLandscapeBuilder` | `WorldPartitionLandscapeBuilder.h` | 랜드스케이프 |
| `UWorldPartitionMiniMapBuilder` | `WorldPartitionMiniMapBuilder.h` | 미니맵 |
| `UWorldPartitionNavigationDataBuilder` | `WorldPartitionNavigationDataBuilder.h` | 네비메시 |
| `SWorldPartitionBuildNavigationDialog` | `SWorldPartitionBuildNavigationDialog.h` | 빌드 다이얼로그 |

### 4.2 작성 패턴

```cpp
UCLASS()
class MYGAMEEDITOR_API UMyWorldPartitionBuilder : public UWorldPartitionBuilder
{
    GENERATED_BODY()
public:
    virtual bool RequiresCommandletRendering() const override { return false; }
    virtual bool RequiresEntireWorldLoading() const override { return true; }
    virtual bool PreRun(UWorld* World, FPackageSourceControlHelper& PackageHelper) override;
    virtual bool RunInternal(UWorld* World, const FCellInfo& InCellInfo, FPackageSourceControlHelper& PackageHelper) override;
    virtual bool PostRun(UWorld* World, FPackageSourceControlHelper& PackageHelper) override;
};
```

Commandlet 으로 호출 가능 (`-run=WorldPartitionBuilderCommandlet -Builder=MyWorldPartitionBuilder`).

---

## 5. Super 호출

| virtual | Super | 의미 |
|---------|-------|------|
| `ULayersSubsystem::Initialize` | **FIRST** | UEditorSubsystem 베이스 |
| `ULayersSubsystem::Deinitialize` | **LAST** | |
| `UWorldPartitionBuilder::PreRun` / `RunInternal` / `PostRun` | (override 시 자체 처리) | 빌더 페이즈 |

---

## 6. 함정

| 함정 | 회피 |
|------|------|
| 매 프레임 `IsLayerVisible` 호출 | 캐싱 + 변경 옵서버 |
| 액터를 레이어에서 제거 안 하고 파괴 | `DeleteLayer` 가 자동 정리 — 액터는 별도 (`UEditorActorSubsystem::DestroyActor`) |
| `SetLayerVisibility` 호출 후 즉시 가시 안 변함 | 에디터 뷰포트 리프레시 트리거 |
| WorldPartition Builder 에 스코프 누락 | 무거운 빌드 작업에 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |

---

## 7. 에디터 전용 🛠

전체 에디터 빌드 전용.

---

## 8. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — 메인
- [`UnrealEd/Subsystems`](../Subsystems/SKILL.md) — UEditorSubsystem 베이스
- [`UnrealEd/Elements`](../Elements/SKILL.md) — Element System (선택과 통합)
- 교차: [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
