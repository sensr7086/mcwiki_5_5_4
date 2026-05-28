---
type: source
title: "UE Editor — AssetRegistry sub-skill 🛠 (메타 캐시 + 의존성)"
slug: ue-editor-assetregistry
source_path: raw/ue-wiki-llm/skills/Editor/references/AssetRegistry.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/IAssetRegistry]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
tags: [ue, editor, assetregistry, fassetdata, farfilter, dependencies, content-browser, runtime-capable]
---

# UE Editor — AssetRegistry sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/AssetRegistry.md]] · 12 KB raw · `Runtime/AssetRegistry/` 8 헤더

## 1. Summary

에셋 메타데이터 캐시. 디스크의 모든 `.uasset` 메타 (클래스 / 태그 / 의존성) 를 인메모리 인덱스로 보관 — 컨텐츠 브라우저 / 검색 박스 / `TSoftObjectPtr` 비동기 로딩 / 플러그인 검색 베이스. **런타임 사용 가능** (Runtime 모듈) — 다른 Editor 모듈과 달리 *4단 분리 의무 약함*, 게임 빌드에서도 활성 (쿠킹된 정보만). 핵심 5: `IAssetRegistry` (5.x 권장) / `UAssetRegistry` (UInterface BP) / `FAssetData` (단일 메타) / `FARFilter` (필터) / `IAssetDependencyGatherer`.

## 2. Key claims

### 2.1. 글로벌 접근

```cpp
IAssetRegistry& Reg = IAssetRegistry::GetChecked();   // 5.x 권장 — 모듈 로드 보장
// 또는 모듈 통해:
FAssetRegistryModule& Module = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
IAssetRegistry& Reg2 = Module.Get();
```

### 2.2. 검색 API 🟢

| API | 라인 | 의미 |
| -- | -- | -- |
| `HasAssets(FName Path, bool bRecursive)` | L284 | 존재 검사 |
| `GetAssetsByPath(FName, ..., bRecursive)` | L309 | 경로별 |
| `GetAssetsByClass(FTopLevelAssetPath, ..., bSearchSubClasses)` | L333 | 클래스별 |
| `GetAssetsByTags / GetAssetsByTagValues` | L341 / 349 | 태그별 |
| **`GetAssets(FARFilter&, TArray<FAssetData>&)`** ⭐ | L361 | 범용 필터 |
| `EnumerateAssets(FARFilter&, TFunctionRef<bool(FAssetData&)>)` | L392 | 콜백 (메모리 효율 — 대량 결과) |
| `GetAssetByObjectPath(FName)` / `GetAssetByObjectPath(FSoftObjectPath&)` | L399 / L423 | 단일 |
| `TryGetAssetByObjectPath(...)` → `EExists` | L433 | 존재 + 검색 진행 중 표시 |

### 2.3. EExists / 검색 진행 중 상태

```cpp
enum class UE::AssetRegistry::EExists : uint8 { Exists, DoesNotExist, Unknown };
// Unknown = AssetRegistry 가 아직 스캔 중 — IsLoadingAssets() 검사 후 재시도
```

### 2.4. 의존성 API (DLC / Cooked 그래프 검증) 🟢

- `GetDependencies(FName Package, TArray<FName>&, EAssetRegistryDependencyType)` — 이 패키지가 의존
- `GetReferencers(FName Package, ...)` — 이 패키지를 *참조* (Soft / Hard 분리)
- `GetAncestorClassNames(FTopLevelAssetPath, ...)` / `GetDerivedClassNames`

**`EAssetRegistryDependencyType`** 비트 플래그 (조합 가능):

| 값 | 의미 |
| -- | -- |
| `Soft` | `TSoftObjectPtr` / `TSoftClassPtr` 참조 |
| `Hard` | 직접 참조 (Cook 시 같이 포함) |
| `SearchableName` | `FAssetRegistrySearchable` 마크 프로퍼티 |
| `SoftManage` | AssetManager 관리 (PrimaryAsset) |
| `HardManage` | AssetManager 강제 |
| `All` | `Soft | Hard | SearchableName | SoftManage | HardManage` |
| `Packages` | `Soft | Hard` |

⭐ 활용: DLC 의존성 ([[synthesis/dlc-asset-migration-edge-cases]]) / Cooked 의존 그래프 / Reference Viewer.

### 2.5. 이벤트 콜백 (안전 시점)

`OnAssetAdded / Removed / Renamed / Updated / UpdatedOnDisk` (라이프사이클) · **`OnFilesLoaded()`** ⭐ — 모든 스캔 완료 안전 시점 · `OnPathAdded / Removed` / `OnAssetCollisionDetected`.

🚨 **중요**: AssetRegistry 완전 로드 전 검색 → 결과 누락. `IsLoadingAssets()` 검사 + `OnFilesLoaded` 후 안전.

### 2.6. FAssetData 구조

```cpp
struct FAssetData {
    FName ObjectPath;                  // 5.x: FSoftObjectPath GetSoftObjectPath()
    FName PackageName;                 // `/Game/Foo/Bar`
    FName PackagePath / AssetName;
    FTopLevelAssetPath AssetClassPath; // 5.x: `/Script/MyModule.MyClass`
    FAssetDataTagMap TagsAndValues;    // 임포트 시 채워진 메타
    FName GetSoftObjectPath() const;
    UObject* GetAsset() const;         // 동기 로드 — 의도적 사용 외 금지
};
```

`TagsAndValues` 가 **임포트 시 채워지는 메타** (예: SkeletalMesh 의 `Skeleton`, Material 의 `BlendMode`).

### 2.7. FARFilter 사용

```cpp
FARFilter Filter;
Filter.ClassPaths.Add(UMyAsset::StaticClass()->GetClassPathName());   // 5.x: ClassPaths (FTopLevelAssetPath)
Filter.PackagePaths.Add(TEXT("/Game/MyItems"));
Filter.bRecursivePaths = Filter.bRecursiveClasses = true;
Filter.TagsAndValues.Add(FName("MyTag"), FString("MyValue"));

TArray<FAssetData> Results;
IAssetRegistry::GetChecked().GetAssets(Filter, Results);
```

5.x 마이그레이션: `ClassNames` (4.x) → `ClassPaths` (5.x — `FTopLevelAssetPath`). 4.x `ClassNames` 호출 = deprecation warning.

### 2.8. 표준 사용 패턴

```cpp
IAssetRegistry& AR = IAssetRegistry::GetChecked();
if (AR.IsLoadingAssets())
{
    AR.OnFilesLoaded().AddLambda([this]
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_AssetRegistryReady);    // [[sources/ue-ref-07-profilingscopeRule]]
        // 안전 시점 — 검색
    });
}
else
{
    // 이미 로드 완료
}
```

### 2.9. 런타임 사용 — TSoftObjectPtr 베이스

`TSoftObjectPtr<T>` 비동기 로드 시 AssetRegistry 가 `FSoftObjectPath` → 패키지 / 의존성 해결. `UAssetManager::LoadPrimaryAssets` + `FStreamableManager` 모두 본 인덱스 활용. SpawnActor 4단 표준 → [[sources/ue-ref-11-assetloadingpolicy]] §6.

런타임 차이 (쿠킹 후):
- Editor-only 태그 (`FAssetRegistryTag::TT_Hidden` 일부) = strip
- `Soft / Hard` 의존성 정보 = 보존 (런타임 로딩 베이스)
- `IsLoadingAssets()` 는 항상 false (런타임은 쿠킹된 캐시 즉시 로드)

### 2.10. 함정 (8대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `IsLoadingAssets()` 검사 없이 검색 | 빈 결과 — `OnFilesLoaded` 후 |
| 2 | `FARFilter::ClassNames` (4.x deprecated) | 5.x `ClassPaths` (`FTopLevelAssetPath`) |
| 3 | `GetAssets` 후 `FAssetData::GetAsset()` 호출 | 동기 로드 트리거 — 의도 시만, 보통 `LoadAssetAsync` |
| 4 | `OnAssetAdded` 등록 후 해제 누락 | hot-reload dangling — Shutdown 의무 |
| 5 | 게임 빌드에서 Editor-only 메타 태그 기대 | 쿠킹 시 strip — Editor 한정 |
| 6 | `bRecursivePaths` / `bRecursiveClasses` 미설정 | 자손 누락 — 기본 false |
| 7 | `EAssetRegistryDependencyType::All` 만 사용 | Soft / Hard 구분 의무 (DLC 그래프 안전) |
| 8 | `TActorIterator` / `TObjectIterator` 로 자산 찾기 | AssetRegistry 사용 — [[sources/ue-ref-09-globaliteratorpolicy]] |

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어: [[sources/ue-editor-assettools]] (`IAssetTypeActions`) / [[sources/ue-coreuobject-package]] (`UPackage`) / [[sources/ue-coreuobject-objecthandles]] (TSoftObjectPtr) / [[sources/ue-editor-unrealed-factories]] (UFactory)
- 횡단: [[sources/ue-ref-11-assetloadingpolicy]] §6 / [[sources/ue-ref-deep-assetloading]] / [[sources/ue-ref-09-globaliteratorpolicy]] (AssetRegistry 가 TObjectIterator 대체) / [[sources/ue-ref-07-profilingscopeRule]]
- synthesis: [[synthesis/dlc-asset-migration-edge-cases]] · [[synthesis/cooked-first-frame-stability]] · [[synthesis/pso-streaming-livepatch-tools]]
