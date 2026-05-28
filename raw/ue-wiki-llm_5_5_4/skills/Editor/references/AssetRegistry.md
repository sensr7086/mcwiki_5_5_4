---
name: assetregistry-main
description: 🛠 AssetRegistry 모듈 - IAssetRegistry::GetChecked + FAssetData + FARFilter + OnAssetAdded + OnFilesLoaded + IAssetDependencyGatherer + 에셋 메타 캐시.
---

# AssetRegistry Module 🛠

> **모듈**: `Engine/Source/Runtime/AssetRegistry/` (Runtime — 게임/에디터 양쪽 사용 가능, 단 컨텐츠 빌드 시점에 따라 차이)
> **사이즈**: Public 8 헤더
> **카테고리**: `[Slate]` 인하우스 툴 / `[Components]` (게임에서도 비동기 에셋 로딩에 사용)

---

## 1. 개요

UE 에디터의 **에셋 메타데이터 캐시**. 디스크에 있는 모든 `.uasset` 파일의 메타정보 (클래스·태그·의존성 등) 를 인메모리 인덱스로 보관 — 컨텐츠 브라우저·검색 박스·에셋 임포트가 모두 이 위에서 동작.

**런타임 사용 가능**: AssetRegistry는 게임 빌드에서도 활성 (단, 쿠킹된 에셋 정보만). `TSoftObjectPtr` 비동기 로딩·플러그인 검색 등에 사용.

핵심 객체:
- **`IAssetRegistry`** — 인터페이스 (UE 5.x 권장)
- **`UAssetRegistry`** — UInterface 형태 (BP 노출)
- **`FAssetData`** — 단일 에셋 메타정보
- **`FARFilter`** — 검색 필터 (클래스·경로·태그)
- **`FAssetDependencyGatherer`** — 의존성 수집

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `IAssetRegistry.h` | `IAssetRegistry` (L262) + `UAssetRegistry` (UInterface L234) | 메인 인터페이스 |
| `AssetRegistryModule.h` | `FAssetRegistryModule` (L26) | 모듈 진입 — `IAssetRegistry::GetChecked()` 글로벌 |
| `AssetRegistryHelpers.h` | `FAssetRegistryHelpers` | 헬퍼 (BP 노출) |
| `AssetRegistryState.h` | `FAssetRegistryState` | 직렬화/중간 상태 |
| `AssetDependencyGatherer.h` | `IAssetDependencyGatherer` | 사용자 정의 의존성 수집 |
| `AssetDataMap.h` | `FAssetDataMap` | 내부 데이터 구조 |
| `PathTree.h` | `FPathTree` | 경로 트리 |
| `AssetRegistryTelemetry.h` | 텔레메트리 |

---

## 3. IAssetRegistry — 메인 API

### 3.1 글로벌 접근

```cpp
// 권장 — IAssetRegistry 인터페이스 직접 (5.x)
IAssetRegistry& Reg = IAssetRegistry::GetChecked();

// 레거시 — 모듈 통해
FAssetRegistryModule& Module = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
IAssetRegistry& Reg2 = Module.Get();
```

### 3.2 검색 API (가장 자주)

| API | 라인 | 의미 |
|-----|------|------|
| `bool HasAssets(FName PackagePath, bool bRecursive=false) const` | L284 | 경로에 에셋 존재? |
| `bool GetAssetsByPackageName(FName, TArray<FAssetData>&, ...)` | L296 | 패키지 이름으로 |
| `bool GetAssetsByPath(FName PackagePath, TArray<FAssetData>&, bool bRecursive=false, ...)` | L309 | 경로별 (예: `/Game/Items/`) |
| `bool GetAssetsByPaths(TArray<FName>, TArray<FAssetData>&, bool bRecursive=false, ...)` | L322 | 복수 경로 |
| `bool GetAssetsByClass(FTopLevelAssetPath ClassPathName, TArray<FAssetData>&, bool bSearchSubClasses=false)` | L333 | 클래스별 |
| `bool GetAssetsByTags(const TArray<FName>&, TArray<FAssetData>&)` | L341 | 태그별 |
| `bool GetAssetsByTagValues(const TMultiMap<FName, FString>&, TArray<FAssetData>&)` | L349 | 태그 + 값 |
| `bool GetAssets(const FARFilter&, TArray<FAssetData>&, bool bSkipARFilteredAssets=true)` | L361 | **범용 필터** (가장 자주) |
| `bool GetInMemoryAssets(const FARFilter&, TArray<FAssetData>&, ...)` | L376 | 메모리 로드된 것만 |
| `bool EnumerateAssets(const FARFilter&, TFunctionRef<bool(const FAssetData&)>, EEnumerateAssetsFlags)` | L392 | 콜백 — 메모리 효율 |
| `FAssetData GetAssetByObjectPath(FName ObjectPath, bool bIncludeOnlyOnDiskAssets=false)` | L399 | 단일 에셋 |
| `FAssetData GetAssetByObjectPath(const FSoftObjectPath&, ...)` | L423 | FSoftObjectPath 버전 |
| `UE::AssetRegistry::EExists TryGetAssetByObjectPath(...)` | L433 | 존재 여부 (검색 진행 중 여부도 반환) |

### 3.3 의존성 API

| API | 의미 |
|-----|------|
| `bool GetDependencies(FName PackageName, TArray<FName>& OutDependencies, EAssetRegistryDependencyType=...)` | 의존하는 패키지들 |
| `bool GetReferencers(FName PackageName, TArray<FName>& OutReferencers, ...)` | 이 패키지를 참조하는 것들 |
| `bool GetAncestorClassNames(FTopLevelAssetPath ClassName, TArray<FTopLevelAssetPath>&)` | 부모 클래스들 |
| `bool GetDerivedClassNames(...)` | 자손 클래스들 |

### 3.4 이벤트 콜백

| 델리게이트 | 의미 |
|-----------|------|
| `FOnAssetAdded& OnAssetAdded()` | 에셋 추가 |
| `FOnAssetRemoved& OnAssetRemoved()` | 제거 |
| `FOnAssetRenamed& OnAssetRenamed()` | 이름 변경 |
| `FOnAssetUpdated& OnAssetUpdated()` | 갱신 |
| `FOnAssetUpdatedOnDisk& OnAssetUpdatedOnDisk()` | 디스크 갱신 |
| `FOnFilesLoaded& OnFilesLoaded()` | 모든 파일 스캔 완료 |
| `FOnPathAdded& OnPathAdded()` / `OnPathRemoved()` | 경로 추가/제거 |
| `FOnAssetCollisionDetected& OnAssetCollisionDetected()` | 충돌 |

---

## 4. FAssetData — 에셋 메타정보

```cpp
struct FAssetData
{
    FName ObjectPath;             // 5.x: FSoftObjectPath ToSoftObjectPath()
    FName PackageName;            // 패키지 (`/Game/Foo/Bar`)
    FName PackagePath;            // 경로
    FName AssetName;              // 파일명
    FTopLevelAssetPath AssetClassPath;   // 클래스
    FAssetDataTagMap TagsAndValues;      // 메타 태그
    FName GetSoftObjectPath() const;     // 변환 헬퍼
    UObject* GetAsset(...) const;        // 메모리 로드 (heavy)
    bool IsAssetLoaded() const;
    bool IsValid() const;
    bool IsInstanceOf(const UClass*) const;
    template<typename T> bool IsInstanceOf() const;
    bool GetTagValue(FName TagName, FString& OutValue) const;
    bool GetTagValue(FName TagName, FText& OutValue) const;
};
```

---

## 5. FARFilter — 범용 검색 필터

```cpp
struct FARFilter
{
    TArray<FName> PackageNames;         // 정확한 패키지 이름들
    TArray<FName> PackagePaths;         // 경로들 (예: /Game/Items)
    TArray<FName> SoftObjectPaths;      // 정확한 객체 경로들
    TArray<FTopLevelAssetPath> ClassPaths;  // 클래스들
    TSet<FTopLevelAssetPath> RecursiveClassPathsExclusionSet;
    TMultiMap<FName, TOptional<FString>> TagsAndValues;  // 태그 매칭
    
    bool bRecursivePaths = false;        // 하위 경로 포함?
    bool bRecursiveClasses = false;      // 자손 클래스 포함?
    bool bIncludeOnlyOnDiskAssets = false;  // 메모리 외 디스크만
    
    bool IsEmpty() const;
};
```

---

## 6. 사용 패턴

### 6.1 모든 BP 에셋 검색

```cpp
#if WITH_EDITOR
IAssetRegistry& Reg = IAssetRegistry::GetChecked();

FARFilter Filter;
Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
Filter.bRecursiveClasses = true;
Filter.PackagePaths.Add(FName("/Game"));
Filter.bRecursivePaths = true;

TArray<FAssetData> Assets;
Reg.GetAssets(Filter, Assets);
for (const FAssetData& Data : Assets) { /* 처리 */ }
#endif
```

### 6.2 EnumerateAssets — 메모리 효율

```cpp
Reg.EnumerateAssets(Filter,
    [](const FAssetData& Data) -> bool
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_EnumerateAssetsCallback);
        // ... 처리
        return true;     // continue
    });
```

### 6.3 의존성 추적

```cpp
TArray<FName> Dependencies;
Reg.GetDependencies(FName("/Game/MyAsset"), Dependencies, UE::AssetRegistry::EDependencyCategory::All);
for (FName Dep : Dependencies)
{
    UE_LOG(LogTemp, Display, TEXT("Depends on: %s"), *Dep.ToString());
}
```

### 6.4 이벤트 등록 (옵서버)

```cpp
Reg.OnAssetAdded().AddUObject(this, &UMyTool::HandleAssetAdded);
Reg.OnFilesLoaded().AddLambda([]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnAllFilesLoaded);
    // 초기 스캔 완료 — 사용자 정의 인덱스 빌드 등
});

void UMyTool::HandleAssetAdded(const FAssetData& NewAsset)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyTool_HandleAssetAdded);
    // ...
}
```

### 6.5 비동기 로드 (런타임 / 에디터 공통)

```cpp
FSoftObjectPath SoftPath("/Game/MyAsset.MyAsset");
FStreamableManager& Streamable = UAssetManager::GetStreamableManager();
Streamable.RequestAsyncLoad(SoftPath, FStreamableDelegate::CreateLambda([SoftPath]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyAsset_OnAsyncLoaded);
    if (UObject* Loaded = SoftPath.ResolveObject()) { /* 사용 */ }
}));
```

`AssetRegistry` 가 `FStreamableManager` 의 메타데이터 베이스. 자세한 — [`CoreUObject/ObjectHandles`](../CoreUObject/references/ObjectHandles.md).

---

## 7. 게임 빌드 vs 에디터 빌드

| 측면 | 에디터 빌드 | 게임 빌드 |
|------|------------|----------|
| 데이터 소스 | 디스크 스캔 (.uasset 헤더) | 쿠킹된 `AssetRegistry.bin` |
| 갱신 | 실시간 (FileSystem watch) | 빌드 시점 고정 |
| `GetAssets` | 모든 에셋 | 쿠킹에 포함된 것만 |
| 사용 시점 | 에디터·인하우스 툴 | `TSoftObjectPtr` 비동기 로드 / 플러그인 검색 |

**게임 빌드 사용 시**: `IAssetRegistry::GetChecked()` 호출 가능. 단, 인하우스 에디터 도구라면 `WITH_EDITOR` 가드.

---

## 8. 가상 함수 / Super 호출

`IAssetRegistry::*` 는 인터페이스 — 사용자가 직접 구현 안 함. 사용자 정의 는 `IAssetDependencyGatherer` (사용자 정의 의존성 수집):

```cpp
class FMyAssetDependencyGatherer : public IAssetDependencyGatherer
{
    virtual void GatherDependencies(const FAssetData& AssetData,
        const FAssetRegistryState& AssetRegistryState,
        TFunctionRef<FARCompiledFilter(const FARFilter&)> CompileFilterFunc,
        TArray<IAssetDependencyGatherer::FGathereredDependency>& OutDependencies,
        TArray<FString>& OutDependencyDirectories) const override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetDependencyGatherer_Gather);
        // 사용자 정의 의존성 추가
    }
};
```

---

## 9. 함정

| 함정 | 회피 |
|------|------|
| `GetAssets` 가 `bSearchSubClasses=false` 라 자손 미포함 | `Filter.bRecursiveClasses = true` |
| 경로에 `.uasset` 확장자 포함 | 패키지 경로는 `/Game/Foo/Bar` (확장자 없음) |
| `FAssetData::GetAsset()` 호출 시 동기 로드 (heavy) | `TSoftObjectPtr` + `FStreamableManager::RequestAsyncLoad` |
| 모든 에셋 스캔 완료 전 검색 | `OnFilesLoaded` 콜백 후 검색 |
| `OnAssetAdded` 콜백에서 무거운 작업 | 빈도 폭증 — 디바운스 + 스코프 |
| `EnumerateAssets` 콜백에 강한 객체 캡처 | 람다 캡처 weak |
| 이벤트 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| 게임 빌드에서 에디터 메타 태그 사용 | 쿠킹 시 일부 태그 빠짐 — `bIncludeMetaDataInTags` 검사 |
| Plugin 에셋이 검색 안 됨 | Plugin 의 PackagePath 가 `/<PluginName>/...` — 직접 추가 |

---

## 10. 에디터 전용? 🛠

**부분적**. 인터페이스 자체는 런타임에서도 사용 가능. 단:
- 디스크 실시간 스캔 / `OnAssetAdded` 같은 에디터 전용 콜백
- 사용자 정의 `IAssetDependencyGatherer` 등록 (에디터 전용 매크로)
- `bIncludeOnlyOnDiskAssets=false` 옵션의 메모리 검색

게임 빌드에서 사용 시 — 쿠킹된 데이터만 접근 가능. 자세한 4단 분리는 [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 11. 관련 sub-skill

- [`AssetTools`](../AssetTools/SKILL.md) — `IAssetTypeActions::GetCategories` / `GetTypeColor` 가 AssetRegistry 의 메타와 통합
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — `UEditorAssetSubsystem` (Asset 파일 조작 헬퍼)
- [`UnrealEd/Factories`](../UnrealEd/Factories/SKILL.md) — Import 후 AssetRegistry 자동 갱신
- [`CoreUObject/Package`](../CoreUObject/references/Package.md) — UPackage / FPackagePath
- [`CoreUObject/ObjectHandles`](../CoreUObject/references/ObjectHandles.md) — TSoftObjectPtr·FSoftObjectPath
- [`CoreUObject/Cooking`](../CoreUObject/references/Cooking.md) — 쿠킹 시점 처리
- [`EditorWidgets`](../EditorWidgets/SKILL.md) — SAssetSearchBox 의 자동완성 베이스
- 교차: [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (이벤트 콜백·Enumerate 람다 스코프)
