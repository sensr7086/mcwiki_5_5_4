---
name: coreuobject-editor
description: 🛠 에디터 전용 콜백 - PostEditChangeProperty + Modify (Undo/Redo) + PostEditUndo + IsDataValid + GetAssetRegistryTags + WITH_EDITOR / WITH_EDITORONLY_DATA.
---

# CoreUObject / Editor

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: **에디터 전용** UObject 콜백·트랜잭션·검증·디테일 패널 통합 (`PreEditChange`/`PostEditChangeProperty`/`Modify`/`PostEditUndo`/`IsDataValid`/`GetAssetRegistryTags`)
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`Property/`](../Property/SKILL.md), [`Cooking/`](../Cooking/SKILL.md), [`Serialization/`](../Serialization/SKILL.md)

> 🛠 **이 sub-skill 전체가 에디터 전용에 가깝다.** 모든 항목이 `WITH_EDITOR` 또는 `WITH_EDITORONLY_DATA` 가드 안에 있거나, 런타임 시그니처는 있어도 의미 있는 호출이 에디터 빌드에서만 일어난다. 게임 런타임 코드에서 의존하면 안 된다.

---

## 1. 개요

CoreUObject가 제공하는 에디터 통합은 다음 4개 묶음:

1. **디테일 패널 콜백** — 사용자가 디테일 패널·BP 디폴트 값을 바꿀 때 호출되는 가상 함수 사슬: `PreEditChange` → 값 변경 → `PostEditChangeProperty` → `PostEditChangeChainProperty`.
2. **트랜잭션(Undo/Redo)** — `Modify()` 로 객체 상태를 트랜잭션에 기록 후 변경. Undo 시 `PreEditUndo`/`PostEditUndo`/`PostTransacted` 호출.
3. **에셋 레지스트리 통합** — `GetAssetRegistryTags`, `IsDataValid` 로 에디터가 에셋을 검색·검증·표시.
4. **에디터 경로/주석/로드 가드** — `IEditorPathObjectInterface`, `WarnIfAssetsLoadedInScope`, `EditorPathHelper`.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/UnrealType.h` | `struct FPropertyChangedEvent` (L6864), `struct FPropertyChangedChainEvent`, `class FEditPropertyChain` | 디테일 패널 변경 이벤트. (전용 헤더 `EditPropertyChain.h`는 없음 — 클래스 정의는 `UnrealType.h`, 구현은 `Private/UObject/EditPropertyChain.cpp`.) |
| `Public/Misc/ITransactionObjectAnnotation.h` | `ITransactionObjectAnnotation` | 트랜잭션 직렬화에 끼우는 추가 데이터. |
| `Public/Misc/TransactionObjectEvent.h` | `FTransactionObjectEvent`, `ETransactionObjectEventType` | 트랜잭션 적용 시 객체에 통지되는 이벤트. |
| `Public/Misc/NotifyHook.h` | `FNotifyHook` 인터페이스 | 디테일 패널이 외부 위젯에 변경을 통지하는 hook. |
| `Public/UObject/AssetRegistryTagsContext.h` | `FAssetRegistryTagsContext` (L97), `FAssetRegistryTagsContextData` (L61), `enum class EAssetRegistryTagsCaller : uint8` (L31) | `GetAssetRegistryTags` 가 받는 컨텍스트 — 어떤 호출자가 왜 묻는지. |
| `Public/Misc/AssetRegistryInterface.h` | `IAssetRegistry` (L59), `UAssetRegistryImpl` (L60) | 에디터의 에셋 검색 인덱스 인터페이스. (실제 구현은 `AssetRegistry` 모듈.) |
| `Public/Misc/DataValidation.h` | `FDataValidationContext`, `EDataValidationResult` | "Validate Asset" 결과 누적. |
| `Public/Misc/DataValidation/Fixer.h` | `FDataValidationFixer` | 자동 수정 액션 컨테이너. |
| `Public/Misc/EditorPathHelper.h` | `FEditorPathHelper` | Level Instance·World Partition 경로 해석. |
| `Public/Misc/EditorPathObjectInterface.h` | `UEditorPathObjectInterface` (L14), `IEditorPathObjectInterface` (L27) | 객체가 외부 경로 해석에 참여하도록. |
| `Public/Misc/WarnIfAssetsLoadedInScope.h` | `FWarnIfAssetsLoadedInScope` | 어떤 스코프 내 에셋 로드 발생 시 경고 (에디터 도구·자동화 보조). |
| `Public/Misc/HotReloadInterface.h` | `IHotReloadInterface` (forward) | 핫 리로드 통합 진입점. |
| `Public/UObject/ObjectEditorOptionalSupport.h` | `FObjectEditorOptionalSupport` | 에디터-전용 객체의 선택적 지원. |
| `Public/Misc/UObjectTestUtils.h` | (테스트 보조) | 자동화 테스트용 도우미. |

---

## 3. 자주 쓰는 API

```cpp
#if WITH_EDITOR
// === 디테일 패널 변경 후 ===
void UMyAsset::PostEditChangeProperty(FPropertyChangedEvent& E)
{
    Super::PostEditChangeProperty(E);

    const FName ChangedName = E.GetPropertyName();      // FPropertyChangedEvent
    if (ChangedName == GET_MEMBER_NAME_CHECKED(UMyAsset, MaxHealth))
    {
        // 의존 캐시 갱신
        RebuildCache();
    }
}

// === 트랜잭션 등록 (Undo 가능 변경) ===
Modify(/*bAlwaysMarkDirty=*/true);   // Object.h L308 — 트랜잭션에 스냅샷
this->Field = NewValue;              // 여기서 변경
PostEditChange();                    // 의존 갱신 트리거 (옵션)

// === Undo/Redo 후처리 ===
void UMyAsset::PostEditUndo()
{
    Super::PostEditUndo();
    // Undo 후 캐시 무효화
    Cache.Empty();
}

// === 에셋 레지스트리 태그 노출 ===
void UMyAsset::GetAssetRegistryTags(FAssetRegistryTagsContext Ctx) const
{
    Super::GetAssetRegistryTags(Ctx);
    Ctx.AddTag(FAssetRegistryTag(TEXT("Version"), FString::FromInt(Version),
                                 FAssetRegistryTag::TT_Numerical));
}

// === 검증 ===
EDataValidationResult UMyAsset::IsDataValid(FDataValidationContext& Ctx) const
{
    EDataValidationResult R = Super::IsDataValid(Ctx);
    if (Tags.Num() == 0)
    {
        Ctx.AddError(NSLOCTEXT("MyAsset", "NoTags", "Tags must not be empty"));
        R = EDataValidationResult::Invalid;
    }
    return CombineDataValidationResults(R, EDataValidationResult::Valid);
}
#endif // WITH_EDITOR
```

### 3.1 FPropertyChangedEvent 자주 쓰는 멤버 (`UnrealType.h:6864~`)

```cpp
FName Property      = E.GetPropertyName();           // 변경된 프로퍼티 이름
FProperty* P        = E.Property;                    // 변경된 프로퍼티 객체
FProperty* MemberP  = E.MemberProperty;              // 부모 (struct) 프로퍼티
EPropertyChangeType::Type T = E.ChangeType;          // 인터랙티브/저장됨/이동/추가/제거
int32 ArrayIndex    = E.GetArrayIndex(TEXT("Tags")); // 배열 변경 시 인덱스
```

`EPropertyChangeType::Interactive` (드래그 중) vs `ValueSet` (놓아진 후) 를 구분하면 비싼 작업을 한 번만 돌릴 수 있다.

---

## 4. 가상 함수 (오버라이드 포인트) 🛠

### 4.1 디테일 패널 콜백 (`Public/UObject/Object.h`)

| 시그니처 | 위치 | 가드 | 호출 시점 / 용도 |
|----------|------|------|------------------|
| `virtual void PreEditChange(FProperty* PropertyAboutToChange)` 🛠 | Object.h L431 | `WITH_EDITOR` | 디테일 패널 변경 직전. |
| `virtual void PreEditChange(FEditPropertyChain&)` 🛠 | Object.h L439 | `WITH_EDITOR` | 중첩 멤버 변경 직전(체인 버전). |
| `virtual bool CanEditChange(const FProperty*) const` 🛠 | Object.h L450 | `WITH_EDITOR` | 디테일 패널에서 편집 가능 여부. |
| `virtual bool CanEditChange(const FEditPropertyChain&) const` 🛠 | Object.h L461 | `WITH_EDITOR` | 체인 버전. |
| `virtual void PostEditChangeProperty(FPropertyChangedEvent&)` 🛠 | Object.h L473 | `WITH_EDITOR` | **가장 자주 override** — 값 변경 후 파생 상태 갱신. |
| `virtual void PostEditChangeChainProperty(FPropertyChangedChainEvent&)` 🛠 | Object.h L479 | `WITH_EDITOR` | 중첩 구조 변경 시 사슬 정보까지. |

### 4.2 트랜잭션 (Undo/Redo)

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual bool Modify(bool bAlwaysMarkDirty = true)` 🛠 (실효) | Object.h L308 | (런타임 시그니처 존재, 의미는 에디터) | 트랜잭션에 상태 스냅샷 등록. **변경 직전에 호출**. |
| `virtual bool IsCapturingAsRootObjectForTransaction() const` 🛠 | Object.h L311 | `WITH_EDITOR` | 트랜잭션 캡처 루트인지. |
| `virtual void PreEditUndo()` 🛠 | Object.h L485 | `WITH_EDITOR` | Undo 직전 정리. |
| `virtual void PostEditUndo()` 🛠 | Object.h L488 | `WITH_EDITOR` | Undo 완료 후. |
| `virtual void PostEditUndo(TSharedPtr<ITransactionObjectAnnotation>)` 🛠 | Object.h L491 | `WITH_EDITOR` | 어노테이션 동반 버전. |
| `virtual void PostTransacted(const FTransactionObjectEvent&)` 🛠 | Object.h L498 | `WITH_EDITOR` | 트랜잭션 적용 후 통합 콜백. |
| `virtual TSharedPtr<ITransactionObjectAnnotation> FactoryTransactionAnnotation(...) const` 🛠 | Object.h L509 | `WITH_EDITOR` | 트랜잭션에 추가 데이터를 끼우는 팩토리. |

### 4.3 선택·이름변경·복제 (에디터 의미가 강한)

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual bool IsSelectedInEditor() const` 🛠 | Object.h L517 | `WITH_EDITOR` | 에디터 선택 상태. |
| `virtual void PostRename(UObject* OldOuter, FName OldName)` 🛠 (실효) | Object.h L523 | (런타임 시그니처) | Outer/Name 변경 후. 주 사용은 에디터 워크플로우. |
| `virtual void PreDuplicate(FObjectDuplicationParameters&)` 🛠 | Object.h L532 | `WITH_EDITOR` | 복제 직전. |
| `virtual void PostDuplicate(EDuplicateMode::Type)` 🛠 | Object.h L539 | (런타임 시그니처, PIE도 사용) | 복제 직후. |
| `virtual void LoadedFromAnotherClass(const FName&)` 🛠 | Object.h L325 | `WITH_EDITOR` | 옛 클래스 이동 호환. |

### 4.4 에셋 메타·검증

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual void GetAssetRegistryTags(FAssetRegistryTagsContext) const` 🛠 | Object.h L898 | `WITH_EDITORONLY_DATA` 영향 | 에셋 검색용 태그·값. |
| `virtual void GetAssetRegistryTags(TArray<FAssetRegistryTag>&) const` 🛠 (구) | Object.h L900 | 동상 | 옛 시그니처 — 점진적 deprecate. |
| `virtual void GetAdditionalAssetDataObjectsForCook(FArchiveCookContext&, ...) const` 🛠 | Object.h L907 | `WITH_EDITOR` | 쿠킹 시 함께 묶일 추가 객체 보고. |
| `virtual void GetExtendedAssetRegistryTagsForSave(const ITargetPlatform*, TArray<FAssetRegistryTag>&) const` 🛠 | Object.h L915 | `WITH_EDITOR` | 저장 시 추가 태그. |
| `virtual void GetAssetRegistryTagMetadata(TMap<FName, FAssetRegistryTagMetadata>&) const` 🛠 | Object.h L1015 | `WITH_EDITOR` | 태그별 표시·정렬 메타. |
| `virtual EDataValidationResult IsDataValid(FDataValidationContext&) const` 🛠 | Object.h L1098 | `WITH_EDITOR` | "Validate Asset" 메뉴와 자동 검증. |
| `virtual EDataValidationResult IsDataValid(FDataValidationContext&)` 🛠 (non-const) | Object.h L1101 | `WITH_EDITOR` | 자동 수정이 가능한 변형. |

### 4.5 BP·자동화 보조

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual void PostInterpChange(FProperty*)` 🛠 | Object.h L423 | `WITH_EDITOR` | Sequencer/Matinee 보간 적용 후. |
| `virtual UClass* RegenerateClass(UClass*, UObject*)` 🛠 | Object.h L1560 | `WITH_EDITOR` | BP 클래스 재생성 hook. |
| `virtual void MarkAsEditorOnlySubobject()` 🛠 | Object.h L1573 | `WITH_EDITOR` | 서브오브젝트를 에디터 전용으로 표시 (쿠킹에서 제외). |

---

## 5. 예제

### 5.1 의존 캐시가 있는 데이터 에셋

```cpp
UCLASS()
class UMySkillAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere) TArray<FName> Names;
    UPROPERTY(EditAnywhere) TArray<int32> Costs;

    TMap<FName, int32> CostByName;        // 캐시 (UPROPERTY 아님)

    virtual void PostInitProperties() override
    {
        Super::PostInitProperties();
        RebuildCache();
    }

#if WITH_EDITOR
    virtual void PostEditChangeProperty(FPropertyChangedEvent& E) override
    {
        Super::PostEditChangeProperty(E);
        if (E.ChangeType != EPropertyChangeType::Interactive)  // 드래그 중엔 스킵
            RebuildCache();
    }

    virtual EDataValidationResult IsDataValid(FDataValidationContext& Ctx) const override
    {
        EDataValidationResult R = Super::IsDataValid(Ctx);
        if (Names.Num() != Costs.Num())
        {
            Ctx.AddError(NSLOCTEXT("Skill","SizeMismatch","Names/Costs size mismatch"));
            R = EDataValidationResult::Invalid;
        }
        return CombineDataValidationResults(R, EDataValidationResult::Valid);
    }

    virtual void GetAssetRegistryTags(FAssetRegistryTagsContext Ctx) const override
    {
        Super::GetAssetRegistryTags(Ctx);
        Ctx.AddTag(FAssetRegistryTag(TEXT("NameCount"),
                                     FString::FromInt(Names.Num()),
                                     FAssetRegistryTag::TT_Numerical));
    }
#endif

private:
    void RebuildCache();
};
```

### 5.3 Modify + 외부 도구에서 객체 수정

```cpp
#if WITH_EDITOR
void Tool_AddTag(UMyAsset* A, FName NewTag)
{
    if (!A) return;
    A->Modify();                           // Undo 트랜잭션 등록
    A->Tags.Add(NewTag);
    A->PostEditChange();                   // 디테일 패널 갱신·캐시 재계산 트리거
}
#endif
```

`Modify()` 누락 시 변경이 Undo 스택에 안 들어가 사용자가 되돌릴 수 없다.

### 5.3 ChainProperty 다루기 (중첩 USTRUCT 변경)

```cpp
#if WITH_EDITOR
void UMyComp::PostEditChangeChainProperty(FPropertyChangedChainEvent& E)
{
    Super::PostEditChangeChainProperty(E);
    if (E.PropertyChain.GetActiveMemberNode())
    {
        FName Member = E.PropertyChain.GetActiveMemberNode()->GetValue()->GetFName();
        if (Member == GET_MEMBER_NAME_CHECKED(UMyComp, NestedConfig))
            RebuildFromNested();
    }
}
#endif
```

---

## 6. 다른 sub-skill의 에디터 전용 cross-reference 🛠

본 sub-skill에 모인 항목 외에도 다른 영역에 흩어져 있는 에디터 전용 기능들:

| sub-skill | 에디터 전용 항목 |
|-----------|------------------|
| [`UObject/`](../UObject/SKILL.md) §6 | `LoadedFromAnotherClass`, `IsSelectedInEditor` (cross-link) |
| [`Reflection/`](../Reflection/SKILL.md) §6 | `SetMetaData/RemoveMetaData/GetAuthoredName/FormatNativeToolTip/GetBoolMetaDataHierarchical` |
| [`Property/`](../Property/SKILL.md) §6 | `UPropertyWrapper`/`UMulticastDelegatePropertyWrapper`, `ExportText/ImportText` 의 실제 사용처 |
| [`GC/`](../GC/SKILL.md) §6 | `EnableFrankenGCMode`, `FReferenceChainSearch`, `GarbageCollectionHistory`, `DumpClusterToLog` |
| [`Serialization/`](../Serialization/SKILL.md) §6 | `FEditorBulkData`, `DerivedData`, `FBaseCookedPackageWriter`, `FArchiveStackTrace` |
| [`Package/`](../Package/SKILL.md) §6 | `SavePackage` 전체 흐름·`FSavePackageArgs`/`FSavePackageContext`, `LinkerDiff`, `PackageReload` |
| [`Cooking/`](../Cooking/SKILL.md) | `BeginCacheForCookedPlatformData`, `IsCachedCookedPlatformDataLoaded`, `U{Class,Struct,Enum}CookedMetaData`, `UObjectRedirector` |

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — 디테일 패널 콜백이 결국 UObject 가상 함수
- [`Property/`](../Property/SKILL.md) — `FPropertyChangedEvent` 가 들고 다니는 `FProperty`
- [`Cooking/`](../Cooking/SKILL.md) — `IsDataValid` 의 검증이 자동화 빌드 단계와 짝
- [`Serialization/`](../Serialization/SKILL.md) — `Modify` → 변경 → 직렬화의 흐름
