---
type: source
title: "UE Editor — EditorSubsystem sub-skill 🛠 (UEditorSubsystem 베이스)"
slug: ue-editor-editorsubsystem
source_path: raw/ue-wiki-llm/skills/Editor/references/EditorSubsystem.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-12
related_entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UEngineSubsystem]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, editor, editorsubsystem, ueditorsubsystem, udynamicsubsystem, dependency]
---

# UE Editor — EditorSubsystem sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/EditorSubsystem.md]] · 7.5 KB raw · `Editor/EditorSubsystem/` 2 Public 헤더 (가장 작은 모듈)

## 1. Summary

**`UEditorSubsystem` 베이스 클래스 1개** 만을 위한 작은 모듈. 게임 런타임의 `UGameInstanceSubsystem` / `UWorldSubsystem` 처럼 자동 인스턴스화 + 라이프사이클 관리를 에디터에서도 동일하게. 베이스 사슬: `USubsystem` → `UDynamicSubsystem` → `UEditorSubsystem` → 사용자 자손. [[sources/ue-editor-unrealed-subsystems]] 의 12개 빌트인 서브시스템 (UAssetEditorSubsystem 등) 이 모두 본 베이스 자손. **모듈 분리 이점**: 사용자가 자손 작성 시 *EditorSubsystem 모듈만 의존* 하면 됨 (UnrealEd 전체 X).

## 2. Key claims

### 2.1. 베이스 사슬

```
USubsystem
└── UDynamicSubsystem        // 동적 인스턴스화
    └── UEditorSubsystem     // 에디터 전용 마커
        └── (사용자 자손 — UMyEditorSubsystem 등)
```

선언 (`EditorSubsystem.h` L27):

```cpp
class EDITORSUBSYSTEM_API UEditorSubsystem : public UDynamicSubsystem { GENERATED_BODY() };
```

### 2.2. 자동 인스턴스화

`UEditorSubsystem` 자손 + `UCLASS()` + 모듈 로드 → **자동 인스턴스 1개 생성**. `GEditor->GetEditorSubsystem<T>()` 로 접근.

### 2.3. 핵심 virtual (Super 호출 의무)

| 시그니처 | Super | 의미 |
| -- | -- | -- |
| `Initialize(FSubsystemCollectionBase& Collection)` | **FIRST** | 인스턴스 초기화 — 외부 구독 / 캐시 |
| `Deinitialize()` | **LAST** | 정리 (사용자 cleanup 후 Super) |
| `ShouldCreateSubsystem(UObject* Outer) const` | (선택) | 생성 조건 동적 결정 (false → 생성 안 됨) |

→ [[sources/ue-ref-04-overrideindex]] §6.1

### 2.4. EditorSubsystem 모듈 vs UnrealEd/Subsystems

| 항목 | EditorSubsystem 모듈 | UnrealEd/Subsystems sub-skill |
| -- | -- | -- |
| 정의 | `UEditorSubsystem` 베이스 1개 | 자손 12개 + 사용 패턴 |
| 위치 | `Editor/EditorSubsystem/` | `Editor/UnrealEd/Public/Subsystems/` |
| 자손 작성 시 | **EditorSubsystem 의존만** | (UnrealEd 전체 의존) |
| 빌트인 사용 시 | (불가) | UnrealEd 의존 필요 |

→ [[sources/ue-editor-unrealed-subsystems]] (12 자손 매트릭스)

### 2.5. 작성 패턴

```cpp
#if WITH_EDITOR
UCLASS()
class MYGAMEEDITOR_API UMyEditorSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);                            // ← Super FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorSubsystem_Init);
        // 외부 시스템 구독 / 캐시 초기화
    }
    virtual void Deinitialize() override
    {
        // 사용자 cleanup
        Super::Deinitialize();                                    // ← Super LAST
    }
    UFUNCTION(BlueprintCallable, Category="My Game Tool")
    void DoSomething();
};
#endif
```

사용:

```cpp
if (UMyEditorSubsystem* My = GEditor->GetEditorSubsystem<UMyEditorSubsystem>())
    My->DoSomething();
```

Build.cs: `"EditorSubsystem"` (UnrealEd 빌트인 서브시스템 사용 안 할 때).

### 2.6. ShouldCreateSubsystem — 조건부 생성

```cpp
virtual bool ShouldCreateSubsystem(UObject* Outer) const override
{
    if (!FModuleManager::Get().IsModuleLoaded("MyOptionalModule"))
        return false;     // 인스턴스 생성 X
    return Super::ShouldCreateSubsystem(Outer);
}
```

### 2.7. 의존성 명시 — InitializeDependency

`Initialize` 안 다른 서브시스템 호출 시 *생성 순서* 보장 필요:

```cpp
virtual void Initialize(FSubsystemCollectionBase& Collection) override
{
    Super::Initialize(Collection);
    Collection.InitializeDependency<UAssetEditorSubsystem>();   // 의존성 명시
    UAssetEditorSubsystem* AES = Collection.InitializeDependency<UAssetEditorSubsystem>();
}
```

직접 `GEditor->GetEditorSubsystem<U>()` 호출 시 다른 서브시스템 미초기화 위험.

### 2.8. Tick 필요 시

`UEditorSubsystem` 자체는 Tick X. Tick 필요 시 → **`UTickableEditorSubsystem`** (이 베이스가 `FTickableEditorObject` 도 상속). 또는 사용자 자손이 `FTickableEditorObject` 직접 상속.

### 2.9. BP 접근

`UEditorSubsystemBlueprintLibrary::GetEditorSubsystem(TSubclassOf<UEditorSubsystem>)` — Editor Utility BP / Python 에서 호출.

### 2.10. 빌트인 자손 14종 분포

- **UnrealEd 모듈** (12): UAssetEditorSubsystem / UEditorActorSubsystem / UEditorAssetSubsystem / UImportSubsystem / UPanelExtensionSubsystem / UPropertyVisibilityOverrideSubsystem / UBrowseToAssetOverrideSubsystem / UBrushEditingSubsystem / UCollectionManagerScriptingSubsystem / UActorEditorContextSubsystem / UUnrealEditorSubsystem / **ULayersSubsystem**
- **EditorFramework 모듈** (2): `UEditorElementSubsystem` / `UPlacementSubsystem`

### 2.11. 함정

- `Initialize` 안 다른 서브시스템 직접 호출 (미초기화) → `Collection.InitializeDependency<T>()` 사용
- `Initialize` Super 누락 → 의무
- `Deinitialize` Super 먼저 호출 → Super **LAST** (사용자 cleanup 후)
- Tick 필요한데 `UEditorSubsystem` 자손 → `UTickableEditorSubsystem` 사용 (`FTickableEditorObject` 의존)
- 게임 모듈에서 직접 의존 → `WITH_EDITOR` 가드 + Build.cs 분리
- `ShouldCreateSubsystem` false 후 사용 → `GetEditorSubsystem<T>()` nullptr 검사 의무
- BP 에서 직접 접근 시도 → `UEditorSubsystemBlueprintLibrary` 헬퍼 사용

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어: [[sources/ue-editor-unrealed-subsystems]] (12 빌트인 자손) / [[sources/ue-editor-editorframework]] (UEditorElementSubsystem / UPlacementSubsystem 페어) / [[sources/ue-subsystem-skill]] (5 Subsystem 통합)
- 베이스: [[sources/ue-coreuobject-uobject]] (UObject 베이스)
- 횡단: [[sources/ue-ref-04-overrideindex]] §6.1 (Super 규약) · [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]]
