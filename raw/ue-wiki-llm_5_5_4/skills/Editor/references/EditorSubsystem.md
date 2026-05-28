---
name: editorsubsystem-main
description: 🛠 EditorSubsystem 모듈 - UEditorSubsystem 베이스 (UDynamicSubsystem 자손) - 사용자 정의 에디터 서브시스템.
---

# EditorSubsystem Module 🛠

> **모듈**: `Engine/Source/Editor/EditorSubsystem/` (Editor 전용)
> **사이즈**: Public 2 헤더 (가장 작음 — 베이스 클래스만 제공)
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UE 에디터의 **서브시스템 베이스 클래스 1개** 만을 위한 작은 모듈. 게임 런타임의 `UGameInstanceSubsystem` / `UWorldSubsystem` 처럼 자동 인스턴스화 + 라이프사이클 관리 패턴을 에디터에서도 동일하게 사용 가능하게 함.

```cpp
// 헤더 EditorSubsystem.h L27
class EDITORSUBSYSTEM_API UEditorSubsystem : public UDynamicSubsystem
{
    GENERATED_BODY()
};
```

**`UDynamicSubsystem`** 자손 — 서브시스템 시스템 (`USubsystem` 베이스) 의 동적 변형. UnrealEd/Subsystems sub-skill에서 다루는 12개 서브시스템들이 모두 본 `UEditorSubsystem` 자손.

---

## 2. UnrealEd/Subsystems vs EditorSubsystem 모듈

| 항목 | EditorSubsystem 모듈 | UnrealEd/Subsystems sub-skill |
|------|---------------------|------------------------------|
| 정의 | `UEditorSubsystem` 베이스 1개 | 베이스의 자손 12개 + 사용 패턴 |
| 의존 모듈 | Core·CoreUObject·Engine·Slate·SlateCore·UnrealEd·EditorSubsystem | EditorSubsystem 의존 |
| 위치 | `Engine/Source/Editor/EditorSubsystem/` | `Engine/Source/Editor/UnrealEd/Public/Subsystems/` |
| 작성 시 | (자손 작성 시 본 모듈 의존만 추가) | (UnrealEd 전체 의존) |

**의미**: 사용자가 인하우스 `UEditorSubsystem` 자손 작성 시 **EditorSubsystem 모듈만 의존하면 됨** (UnrealEd 전체 X). 대신 12개 빌트인 서브시스템(UAssetEditorSubsystem 등) 사용 시는 UnrealEd 의존 필요.

---

## 3. UEditorSubsystem 베이스 핵심

### 3.1 베이스 사슬

```
USubsystem
└── UDynamicSubsystem        // 동적 인스턴스화 (vs UStaticSubsystem)
    └── UEditorSubsystem     // 에디터 전용 마커
        └── (사용자 자손 — UAssetEditorSubsystem · UEditorActorSubsystem 등)
```

### 3.2 자동 인스턴스화 조건

`UEditorSubsystem` 자손 + `UCLASS()` + 모듈 로드 시 → 자동으로 인스턴스 1개 생성. `GEditor->GetEditorSubsystem<T>()` 로 접근.

### 3.3 USubsystem virtual (베이스)

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `virtual void Initialize(FSubsystemCollectionBase& Collection)` | **FIRST** | 인스턴스 초기화 — 외부 구독·캐시 |
| `virtual void Deinitialize()` | **LAST** | 정리 |
| `virtual bool ShouldCreateSubsystem(UObject* Outer) const` | (선택) | 생성 조건 동적 결정 (false 반환 시 생성 안 됨) |

자세한 Super 호출 — [`04_OverrideIndex.md §6.1`](../../references/04_OverrideIndex.md).

---

## 4. 작성 패턴

### 4.1 가장 단순한 자손

```cpp
#if WITH_EDITOR
UCLASS()
class MYGAMEEDITOR_API UMyEditorSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);              // ← Super FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorSubsystem_Init);   // ← 프로파일링 스코프
        // 외부 시스템 구독 / 캐시 초기화
    }

    virtual void Deinitialize() override
    {
        // 사용자 cleanup
        Super::Deinitialize();                      // ← Super LAST
    }

    UFUNCTION(BlueprintCallable, Category="My Game Tool")
    void DoSomething();
};
#endif
```

### 4.2 사용 (어디서든)

```cpp
#if WITH_EDITOR
if (UMyEditorSubsystem* My = GEditor->GetEditorSubsystem<UMyEditorSubsystem>())
{
    My->DoSomething();
}
#endif
```

### 4.3 Build.cs 의존

```csharp
// MyGameEditor.Build.cs
PrivateDependencyModuleNames.AddRange(new string[] {
    "Core", "CoreUObject", "Engine", "Slate", "SlateCore",
    "EditorSubsystem"     // ← 본 모듈만 의존하면 충분 (단, UnrealEd 빌트인 서브시스템 사용 X)
});
```

---

## 5. ShouldCreateSubsystem (조건부 생성)

```cpp
virtual bool ShouldCreateSubsystem(UObject* Outer) const override
{
    // 특정 프로젝트/플러그인 활성 시에만 생성
    if (!FModuleManager::Get().IsModuleLoaded("MyOptionalModule"))
    {
        return false;     // 인스턴스 생성 X
    }
    return Super::ShouldCreateSubsystem(Outer);
}
```

---

## 6. 빌트인 서브시스템 12개

UnrealEd 모듈에 정의됨 — 자세한 사용은 [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md). 한 줄 요약:

| 서브시스템 | 의미 |
|-----------|------|
| `UAssetEditorSubsystem` | 에셋 에디터 라우팅 (가장 자주) |
| `UEditorActorSubsystem` | 액터 일괄 조작 |
| `UEditorAssetSubsystem` | Asset 파일 조작 |
| `UImportSubsystem` | 임포트 라우팅 |
| `UPanelExtensionSubsystem` | 패널 확장점 |
| `UPropertyVisibilityOverrideSubsystem` | 가시성 오버라이드 |
| `UBrowseToAssetOverrideSubsystem` | 브라우즈 오버라이드 |
| `UBrushEditingSubsystem` | BSP 브러시 |
| `UCollectionManagerScriptingSubsystem` | 컬렉션 |
| `UActorEditorContextSubsystem` | 액터 컨텍스트 |
| `UUnrealEditorSubsystem` | 잡다 헬퍼 |
| `UEditorElementSubsystem` (`EditorFramework` 모듈) | Element System |

추가:
| `ULayersSubsystem` (`UnrealEd` 모듈) | 레이어 |
| `UPlacementSubsystem` (`EditorFramework` 모듈) | 배치 |

---

## 7. 함정

| 함정 | 회피 |
|------|------|
| `Initialize` 안에서 `GEditor->GetEditorSubsystem<U>()` 호출 — 다른 서브시스템이 아직 미초기화 | `FSubsystemCollectionBase::InitializeDependency<U>(Collection)` 사용 (의존성 명시) |
| `Initialize` Super 누락 | Super FIRST 의무 |
| `Deinitialize` 가 Super 먼저 호출 | Super LAST — 사용자 cleanup 후 |
| `Tick` 처리 안 함 | `UTickableEditorSubsystem` 의존성 (TickableEditorObject) — UEditorSubsystem 자체는 Tick X |
| 게임 모듈에서 직접 의존 | `WITH_EDITOR` 가드 + Build.cs 분리 |
| 매 프레임 작업 시 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| `ShouldCreateSubsystem` false 반환 후 사용 시도 | `GetEditorSubsystem<T>()` 가 nullptr 반환 — 검사 의무 |
| BP에서 서브시스템 접근 | `UEditorSubsystemBlueprintLibrary::GetEditorSubsystem(Class)` 헬퍼 사용 |

---

## 8. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 9. 관련 sub-skill

- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — 12개 빌트인 자손 + 사용 패턴 + IAssetEditorInstance 인터페이스
- [`EditorFramework`](../EditorFramework/SKILL.md) — `UPlacementSubsystem` · `UEditorElementSubsystem` (UEditorSubsystem 자손)
- [`UnrealEd/Layers`](../UnrealEd/Layers/SKILL.md) — `ULayersSubsystem` (UEditorSubsystem 자손)
- [`CoreUObject/UObject`](../CoreUObject/references/UObject.md) — UObject 베이스
- 교차: [`04_OverrideIndex.md §6.1`](../../references/04_OverrideIndex.md) (Initialize/Deinitialize Super) · [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)
