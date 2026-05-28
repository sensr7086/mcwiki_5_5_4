---
name: unrealed-elements
description: 🛠 5.x Element System - FTypedElementHandle + UTypedElementSelectionSet + UTypedElementCommonActions.
---

# UnrealEd · Elements sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용) — UE 5.x **Element Selection System**
> **위치**: `Engine/Source/Editor/UnrealEd/Public/Elements/` + `TypedElementFramework`/`TypedElementRuntime` 모듈
> **다루는 범위**: 5.x 신규 선택 시스템 — 액터/컴포넌트/오브젝트/SMInstance를 **하나의 추상 핸들** (`FTypedElementHandle`) 로 통합 처리.

---

## 1. 개요

UE 5.x 부터 `Edit > Select All` / `Outliner` 의 선택 대상이 액터뿐 아니라 **컴포넌트·오브젝트·인스턴스 메시**도 가능. 이를 통합 추상화한 게 **Element Selection System**.

**구성**:
- `FTypedElementHandle` — 추상 핸들 (액터/컴포넌트/오브젝트/SMInstance 모두 대응)
- `UTypedElementSelectionSet` — 선택 집합
- `ITypedElementWorldInterface` 등 — Element 별 인터페이스 (변환·가시성 등)
- `FTypedElementOwnerStore<T>` — Element 라이프사이클 관리

**5.x 이전 (4.x)**: 액터만 선택 가능 (`USelection*` 글로벌). 4.x 코드는 5.x에서도 동작하지만 신규 코드는 Element System 권장.

---

## 2. 디렉토리 (UnrealEd/Public/Elements/)

```
Elements/
├── Actor/         ← Actor Element (FActorElementHandle 등)
├── Component/     ← Component Element
├── Framework/     ← 프레임워크 베이스 (Type Registry 등)
├── Object/        ← 일반 UObject Element
├── SMInstance/    ← Instanced Static Mesh 인스턴스 Element
└── TypedElementEditorLog.{h,cpp}
```

---

## 3. 핵심 클래스

### 3.1 핸들 / 셀렉션 셋

| 클래스 | 모듈 | 의미 |
|--------|------|------|
| `FTypedElementHandle` | TypedElementFramework | 모든 Element의 추상 핸들 |
| `FTypedElementId` | TypedElementFramework | 정수 ID (가벼운 비교) |
| `UTypedElementSelectionSet` | TypedElementFramework | 선택 집합 (UCLASS) |
| `UTypedElementCommonActions` | TypedElementRuntime | 공통 액션 (Delete/Copy/Paste 등) |
| `FTypedElementOwnerStore<T>` | TypedElementFramework | Element 라이프사이클 |

### 3.2 인터페이스 (Element 별 능력)

| 인터페이스 | 의미 |
|-----------|------|
| `ITypedElementWorldInterface` | World 변환 (Transform / Visibility) |
| `ITypedElementHierarchyInterface` | 계층 (부모/자식) |
| `ITypedElementSelectionInterface` | 선택 가능 |
| `ITypedElementObjectInterface` | UObject 접근 |
| `ITypedElementAssetDataInterface` | Asset 데이터 |
| `ITypedElementPrimitiveCustomDataInterface` | 커스텀 데이터 |

각 Element 카테고리(Actor/Component/Object/SMInstance) 가 위 인터페이스 중 일부를 구현.

---

## 4. 자주 쓰는 API

### 4.1 선택 셋 접근

```cpp
#if WITH_EDITOR
// 글로벌 선택 셋
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
            // ...
            return true;    // continue
        });
}
#endif
```

### 4.2 Element 변환 (액터/컴포넌트 통합)

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

### 4.3 새 Element 생성

```cpp
// Actor → FTypedElementHandle 변환
FTypedElementHandle Handle = UEngineElementsLibrary::AcquireEditorActorElementHandle(MyActor);

// Component → handle
FTypedElementHandle CompHandle = UEngineElementsLibrary::AcquireEditorComponentElementHandle(MyComponent);
```

---

## 5. UEditorActorSubsystem 통합

`UEditorActorSubsystem`(Subsystems sub-skill) 의 선택 API는 내부적으로 Element System 사용:
- `GetSelectedLevelActors()` — Actor Element 만 추출
- `SelectNothing()` — 모든 Element 선택 해제
- `SetActorSelectionState(AActor*, bool)` — Actor Element 선택 토글

신규 코드에서 컴포넌트도 선택 처리하려면 `UTypedElementSelectionSet` 직접 사용.

---

## 6. Super 호출 / virtual

본 sub-skill의 클래스 대다수는 **인터페이스** — UCLASS Subsystem 자손에서 구현. 자세한 인터페이스 메서드는 `Engine/Source/Runtime/TypedElementFramework/` 참조 (별도 모듈, 미마운트).

| 인터페이스 메서드 (예시) | 의미 |
|-------------------------|------|
| `ITypedElementWorldInterface::GetWorldTransform(FTransform& OutTransform)` | 변환 가져오기 |
| `ITypedElementWorldInterface::SetWorldTransform(const FTransform&)` | 설정 |
| `ITypedElementHierarchyInterface::GetParentElement()` | 부모 |
| `ITypedElementSelectionInterface::CanSelectElement()` | 선택 가능? |

---

## 7. 함정

| 함정 | 회피 |
|------|------|
| 4.x 스타일 (`GEditor->GetSelectedActors()->Iterator`) 만 사용 | 컴포넌트/SMInstance 누락 — Element System 권장 |
| `FTypedElementHandle` 직접 캐스팅 시도 | 인터페이스 (`ITypedElementWorldInterface` 등) 통한 접근 |
| Element 라이프사이클 무시 | `FTypedElementOwnerStore` 가 라이프사이클 관리 — 핸들 보관은 일시적 |
| 매 프레임 `GetSelectedElementHandles` 호출 | 캐싱 + 변경 옵서버 (`UTypedElementSelectionSet::OnChanged`) 사용 |
| `ForEach*` 람다 안 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 의무 |

---

## 8. 에디터 전용 🛠

전체 에디터 빌드 전용. Module 의존: `UnrealEd` + `TypedElementFramework` + `TypedElementRuntime`.

---

## 9. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — 메인
- [`UnrealEd/Subsystems`](../Subsystems/SKILL.md) — `UEditorActorSubsystem` 가 Element System 위에서 동작
- [`UnrealEd/Layers`](../Layers/SKILL.md) — 레이어 가시성 (Element 변환과 통합)
- [`Slate/GraphEditor`](../../Slate/references/GraphEditor.md) — 노드 그래프의 선택 (Element System과 별개)
- 향후: `TypedElementFramework` / `TypedElementRuntime` (별도 모듈)
- 교차: [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
