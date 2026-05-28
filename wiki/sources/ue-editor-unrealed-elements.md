---
type: source
title: "UE Editor — UnrealEd / Elements sub-skill 🛠 (5.x Element System)"
slug: ue-editor-unrealed-elements
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Elements.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/UActorComponent]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, unrealed, elements, ftypedelementhandle, selection, 5x]
---

# UE Editor — UnrealEd / Elements sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Elements.md]] · `UnrealEd/Public/Elements/` + `TypedElementFramework` / `TypedElementRuntime` 모듈 · UE 5.x **Element Selection System**

## 1. Summary

UE 5.x 부터 `Edit > Select All` / `Outliner` 의 선택 대상이 액터뿐 아니라 **컴포넌트·오브젝트·인스턴스 메시** 도 가능. 이를 통합 추상화한 게 **Element Selection System**. 핵심 5: **`FTypedElementHandle`** (추상 핸들) · **`FTypedElementId`** (가벼운 정수 ID) · **`UTypedElementSelectionSet`** (UCLASS 선택 집합) · **`UTypedElementCommonActions`** (Delete/Copy/Paste 공통 액션) · **`FTypedElementOwnerStore<T>`** (라이프사이클). 5.x 이전 (4.x) = 액터만 가능 (`USelection*`) — 4.x 코드는 5.x에서도 동작하지만 **신규 코드는 Element System 권장**. 🛠 **Editor 전용**.

## 2. Key claims

### 2.1. 디렉토리 (UnrealEd/Public/Elements/)

```
Elements/
├── Actor/         ← Actor Element (FActorElementHandle 등)
├── Component/     ← Component Element
├── Framework/     ← 프레임워크 베이스 (Type Registry)
├── Object/        ← 일반 UObject Element
├── SMInstance/    ← Instanced Static Mesh 인스턴스 Element
└── TypedElementEditorLog.{h,cpp}
```

### 2.2. 핵심 클래스

| 클래스 | 모듈 | 의미 |
| -- | -- | -- |
| **`FTypedElementHandle`** ⭐ | TypedElementFramework | 모든 Element 의 추상 핸들 |
| `FTypedElementId` | TypedElementFramework | 정수 ID (가벼운 비교) |
| **`UTypedElementSelectionSet`** ⭐ | TypedElementFramework | 선택 집합 (UCLASS) |
| `UTypedElementCommonActions` | TypedElementRuntime | 공통 액션 (Delete / Copy / Paste / Cut / Move) |
| `FTypedElementOwnerStore<T>` | TypedElementFramework | Element 라이프사이클 관리 |

### 2.3. 인터페이스 (Element 별 능력) 🟢

| 인터페이스 | 의미 |
| -- | -- |
| `ITypedElementWorldInterface` | World 변환 (Transform / Visibility) |
| `ITypedElementHierarchyInterface` | 계층 (부모 / 자식) |
| `ITypedElementSelectionInterface` | 선택 가능 검사 |
| `ITypedElementObjectInterface` | UObject 접근 |
| `ITypedElementAssetDataInterface` | Asset 데이터 |
| `ITypedElementPrimitiveCustomDataInterface` | 커스텀 데이터 |

각 Element 카테고리 (Actor / Component / Object / SMInstance) 가 위 인터페이스 중 일부를 구현.

### 2.4. 글로벌 선택 셋 접근

```cpp
#if WITH_EDITOR
if (UTypedElementSelectionSet* Sel = GEditor->GetSelectedActors()->GetElementSelectionSet())
{
    // 전체 선택된 Element 핸들
    TArray<FTypedElementHandle> Selected = Sel->GetSelectedElementHandles();

    // 특정 인터페이스로 필터링 — World 변환 가능한 것만
    Sel->ForEachSelectedElement<ITypedElementWorldInterface>(
        [](const TTypedElement<ITypedElementWorldInterface>& Element) -> bool
        {
            FTransform T;
            Element.GetWorldTransform(T);
            return true;   // continue
        });
}
#endif
```

### 2.5. Element 변환 (액터 / 컴포넌트 통합)

```cpp
Sel->ForEachSelectedElement<ITypedElementWorldInterface>(
    [DeltaLocation](const TTypedElement<ITypedElementWorldInterface>& Element) -> bool
    {
        FTransform T;
        if (Element.GetWorldTransform(T))
        {
            T.AddToTranslation(DeltaLocation);
            Element.SetWorldTransform(T);
        }
        return true;
    });
```

### 2.6. 새 Element 핸들 생성

```cpp
// Actor → FTypedElementHandle
FTypedElementHandle Handle = UEngineElementsLibrary::AcquireEditorActorElementHandle(MyActor);

// Component → handle
FTypedElementHandle CompHandle = UEngineElementsLibrary::AcquireEditorComponentElementHandle(MyComponent);
```

### 2.7. UEditorActorSubsystem 통합

`UEditorActorSubsystem` 의 선택 API 는 내부적으로 Element System 사용:
- `GetSelectedLevelActors()` — Actor Element 만 추출
- `SelectNothing()` — 모든 Element 선택 해제
- `SetActorSelectionState(AActor*, bool)` — Actor Element 토글

신규 코드에서 컴포넌트도 선택 처리하려면 `UTypedElementSelectionSet` 직접 사용.

### 2.8. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | 4.x 스타일 (`GEditor->GetSelectedActors()->Iterator`) 만 사용 | 컴포넌트 / SMInstance 누락 → Element System |
| 2 | `FTypedElementHandle` 직접 캐스팅 시도 | 인터페이스 (`ITypedElementWorldInterface` 등) 통한 접근 |
| 3 | Element 라이프사이클 무시 | `FTypedElementOwnerStore` 가 라이프사이클 — 핸들 보관 일시적 |
| 4 | 매 프레임 `GetSelectedElementHandles` 호출 | 캐싱 + 변경 옵서버 (`UTypedElementSelectionSet::OnChanged`) |
| 5 | `ForEach*` 람다 안 스코프 누락 | [[sources/ue-ref-07-profilingscopeRule]] 의무 |

### 2.9. Build.cs (Editor 모듈만) 🛠

`UnrealEd` + `TypedElementFramework` + `TypedElementRuntime`. 게임 모듈에서 의존 금지.

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-leveleditor]] (5.x `FTypedElementSelectionSet` 마이그레이션 — `OnActorSelectionChanged` 대체) / [[sources/ue-editor-unrealed-subsystems]] (`UEditorActorSubsystem` 가 Element System 위에서 동작) / [[sources/ue-editor-unrealed-layers]] (레이어 가시성 ↔ Element 통합)
- 횡단: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] (Element 등록 패턴 — TActorIterator 대안)
- Element 베이스: TypedElementFramework / TypedElementRuntime 모듈 (별도, 미마운트)
