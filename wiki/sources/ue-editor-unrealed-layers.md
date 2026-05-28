---
type: source
title: "UE Editor — UnrealEd / Layers sub-skill 🛠 (레이어 + 북마크 + WorldPartition Builder)"
slug: ue-editor-unrealed-layers
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Layers.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/UWorld]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, unrealed, layers, datalayer, bookmark, worldpartition, builder]
---

# UE Editor — UnrealEd / Layers sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Layers.md]] · `UnrealEd/Public/Layers/` + `Public/Bookmarks/` + `Public/WorldPartition/`

## 1. Summary

레벨 에디팅 시각화·관리 도구 묶음. 3 영역: **Layers** (`ULayersSubsystem` — 액터 가시성·잠금 토글) · **Bookmarks** (카메라 위치 슬롯 0~9 — `Ctrl+1~9` 저장 / `1~9` 복원) · **WorldPartition Builder** (5.x — 동적 로드 영역 분할 + HLOD / 폴리지 / 미니맵 빌더). 🛠 **Editor 전용**. 5.x **DataLayer** (런타임 영향) 는 별도 — 본 sub-skill 의 Layer 는 Editor 시각 grouping 전용.

## 2. Key claims

### 2.1. ULayersSubsystem (Editor Subsystem) 🟢

```cpp
class ULayersSubsystem : public UEditorSubsystem
```

| API | 의미 |
| -- | -- |
| `bool TryGetLayer(FName LayerName, ULayer*& OutLayer)` | 레이어 조회 |
| `ULayer* CreateLayer(FName LayerName)` | 새 레이어 |
| `void DeleteLayer(FName)` / `DeleteLayers(TArray<FName>&)` | 삭제 / 일괄 |
| `void RenameLayer(FName Old, FName New)` | 이름 변경 |
| `void AddActorToLayer(AActor*, FName)` / `AddActorsToLayer` | 액터 → 레이어 |
| `void RemoveActorFromLayer(AActor*, FName)` | 제거 |
| `bool IsLayerVisible(FName)` / `SetLayerVisibility(FName, bool)` | 가시성 |
| `bool IsLayerLocked(FName)` / `SetLayerLocked(FName, bool)` | 잠금 |
| `void SelectActorsInLayer(FName, bool bSelect, bool bNotify)` | 일괄 선택 |
| `TArray<FName> GetLayerNames()` | 전체 |

### 2.2. 사용 패턴

```cpp
#if WITH_EDITOR
if (ULayersSubsystem* Layers = GEditor->GetEditorSubsystem<ULayersSubsystem>())
{
    Layers->CreateLayer(FName("Enemies"));
    for (AActor* A : EnemyActors)
        Layers->AddActorToLayer(A, FName("Enemies"));
    Layers->SetLayerVisibility(FName("Enemies"), false);   // 일괄 숨김
}
#endif
```

### 2.3. Layer vs DataLayer (5.x 차이) ⚠

| 측면 | Layer (`ULayersSubsystem`) | DataLayer (5.x) |
| -- | -- | -- |
| 영향 | Editor 시각만 (그룹화 / 가시성 / 잠금) | **런타임 영향** (Active 시만 spawn / 유지) |
| 액터 멤버 | `AActor::Layers` (TArray<FName>) | DataLayer Asset (`UDataLayerAsset`) 참조 |
| WorldPartition | 통합 X | **통합 ✅** — WP cell 의 활성 상태 |
| Multiplayer | (Editor 만) | Server-side activation (5.x) |

신규 = **DataLayer 권장** (런타임 시 / WP 통합). 기존 Layer = 디자이너 grouping.

### 2.4. Bookmarks (`Public/Bookmarks/`)

| 헤더 | 의미 |
| -- | -- |
| `IBookmarkTypeActions.h` | 인터페이스 — 북마크 타입별 동작 |
| `IBookmarkTypeTools.h` | 툴 인터페이스 |
| `BookMarkTypeActions.h` | 기본 구현 |
| `BookmarkSingleViewportActions.h` | 단일 뷰포트 |
| `BookmarkScoped.h` | RAII scope |

레벨 에디터 `Ctrl+1~9` 저장 / `1~9` 복원. 커스텀 뷰포트 도구 시 `IBookmarkTypeActions` 자손:

```cpp
class FMyBookmarkActions : public IBookmarkTypeActions
{
    virtual TSubclassOf<UBookmarkBase> GetBookmarkClass() override;
    virtual void InitFromViewport(UBookmarkBase*, FEditorViewportClient&) override;
    virtual void JumpToBookmark(UBookmarkBase*, const TSharedPtr<FBookmarkBaseJumpToSettings>&, FEditorViewportClient&) override;
};
```

### 2.5. WorldPartition Builder (5.x — `Public/WorldPartition/`)

| 클래스 | 의미 |
| -- | -- |
| **`UWorldPartitionBuilder`** ⭐ | 베이스 |
| `UWorldPartitionFoliageBuilder` | 폴리지 |
| `UWorldPartitionHLODsBuilder` | HLOD |
| `UWorldPartitionLandscapeBuilder` | 랜드스케이프 |
| `UWorldPartitionMiniMapBuilder` | 미니맵 |
| `UWorldPartitionNavigationDataBuilder` | 네비메시 |
| `SWorldPartitionBuildNavigationDialog` | 빌드 다이얼로그 |

작성 패턴:

```cpp
UCLASS()
class MYGAMEEDITOR_API UMyWorldPartitionBuilder : public UWorldPartitionBuilder
{
    GENERATED_BODY()
public:
    virtual bool RequiresCommandletRendering() const override { return false; }
    virtual bool RequiresEntireWorldLoading() const override { return true; }
    virtual bool PreRun(UWorld* W, FPackageSourceControlHelper& H) override;
    virtual bool RunInternal(UWorld* W, const FCellInfo& Cell, FPackageSourceControlHelper& H) override;
    virtual bool PostRun(UWorld* W, FPackageSourceControlHelper& H) override;
};
```

Commandlet 호출: `-run=WorldPartitionBuilderCommandlet -Builder=MyWorldPartitionBuilder`.

### 2.6. Super 호출

| virtual | Super | 의미 |
| -- | -- | -- |
| `ULayersSubsystem::Initialize` | **FIRST** | UEditorSubsystem 베이스 |
| `ULayersSubsystem::Deinitialize` | **LAST** | |
| `UWorldPartitionBuilder::PreRun / RunInternal / PostRun` | (override 시 자체 처리) | 빌더 페이즈 |

→ [[sources/ue-ref-04-overrideindex]] (Super 통합).

### 2.7. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | 매 프레임 `IsLayerVisible` 호출 | 캐싱 + 변경 옵서버 |
| 2 | 액터 레이어에서 제거 안 하고 파괴 | `DeleteLayer` 자동 정리 — 액터 별도 (`UEditorActorSubsystem::DestroyActor`) |
| 3 | `SetLayerVisibility` 호출 후 즉시 가시 안 변함 | 에디터 뷰포트 리프레시 트리거 |
| 4 | WP Builder 무거운 작업 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 5 | Layer 와 DataLayer 혼동 | Layer = Editor 시각 / DataLayer = 런타임 영향 |

### 2.8. Build.cs (Editor 모듈만) 🛠

`UnrealEd` + `WorldPartition` (5.x) + `EditorSubsystem`.

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-unrealed-subsystems]] (UEditorSubsystem 베이스) / [[sources/ue-editor-unrealed-elements]] (선택 + 가시성 통합) / [[sources/ue-editor-leveleditor]]
- 5.x WorldPartition 페어: [[sources/ue-spatialpartition-worldpartitionruntime]] (런타임 streaming) · [[synthesis/toctree2-worldpartition-pair-pattern]] (페어 표준)
- 횡단: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]] (Builder 무거운 작업)
