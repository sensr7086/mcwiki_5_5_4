---
name: coreuobject-package
description: UPackage / FPackagePath - LoadPackage + SavePackage + LoadPackageAsync + StaticLoadObject + Mount Point + GetTransientPackage.
---

# CoreUObject / Package

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: `UPackage`, `FLinkerLoad`/`FLinkerSave`, `FPackageFileSummary`, `SavePackage`, `FPackagePath`/`FPackageName`
> 관련 sub-skill: [`Serialization/`](../Serialization/SKILL.md), [`UObject/`](../UObject/SKILL.md), [`Cooking/`](../Cooking/SKILL.md)

---

## 1. 개요

UPackage는 디스크의 `.uasset`/`.umap` 파일에 1:1 대응한다 (또는 5.x Iostore 컨테이너 안의 한 패키지). 모든 UObject는 어떤 UPackage를 최상위 Outer로 가진다 — 임시 객체는 `transient package` 가 그 Outer.

직렬화 흐름:

```
[저장] UPackage::SavePackage(...)
        → FSavePackageArgs/FSavePackageContext 구성
        → FLinkerSave 생성 (FArchive + Linker)
        → FPackageFileSummary 작성
        → 모든 export UObject::Serialize() 호출
        → BulkData 분리 영역에 기록

[로드] LoadPackage / LoadPackageAsync
        → FLinkerLoad 생성
        → FPackageFileSummary 읽음
        → import/export 테이블 구성
        → UObject 생성 + Serialize() 호출 → PostLoad()
```

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/Package.h` | `UPackage` (L215, `: public UObject`) | 디스크 파일에 대응되는 UObject 묶음. 더티 플래그·로드 상태·메타. |
| `Public/UObject/Package.h` | `FSavePackageResultStruct` (L129), `FPreloadDependency` (L117), `UPackage::FAdditionalInfo` (L382) | SavePackage 결과·로드 의존·추가 메타. |
| `Public/UObject/PackageFileSummary.h` | `FPackageFileSummary` (L56), `FGenerationInfo` (L31) | 패키지 헤더 — 매직·버전·이름 테이블 오프셋·import/export 카운트. |
| `Public/UObject/Linker.h` | `FLinker` (베이스) | LinkerLoad·LinkerSave 의 공통 베이스. |
| `Public/UObject/LinkerLoad.h` | `FLinkerLoad`, `FOpenPackageResult` (L54), `FUObjectSerializeContext` (L56) | 패키지 로딩 — import 해소·import map·export 테이블 채우기. |
| `Public/UObject/LinkerSave.h` | `FLinkerSave : public FLinker, public FArchiveUObject` (L47), `FSaveContext` (L34) | 패키지 저장 — UObject 직렬화 + summary 출력. |
| `Public/UObject/SavePackage.h` | `FSavePackageArgs` (L62), `FSavePackageSettings` (L186), `FSavePackageContext` (L225), `ISavePackageValidator` (L134) 🛠 | SavePackage 진입점·옵션·검증. |
| `Public/UObject/SavePackage.h` | `FArchiveSavePackageCollector : FArchiveUObject` (L365), `GetSavePackagePortFlags()` (L380) | 저장 시 참조 수집·플래그. |
| `Public/UObject/PackageResourceManager.h`, `PackageResourceManagerFile.h` | `IPackageResourceManager` (L119) | 패키지 위치 추상 (Iostore/디스크 파일). |
| `Public/UObject/PackageReload.h` | (Hot reload 통합) 🛠 | 에디터에서 패키지 다시 로드. |
| `Public/UObject/PackageTrailer.h` | `FPackageTrailer` | 패키지 끝에 붙는 BulkData 페이로드 트레일러. |
| `Public/UObject/PackedObjectRef.h` | `FPackedObjectRef` | 압축된 객체 참조. |
| `Public/UObject/LinkerInstancingContext.h` | `FLinkerInstancingContext` | World partition·sublevel 인스턴싱 시 이름 리매핑. |
| `Public/UObject/LinkerDiff.h` 🛠 | `FLinkerDiff` | 두 저장 결과 diff (결정론 검증). |
| `Public/Misc/PackagePath.h` | `FPackagePath` (L88) | 패키지 경로(`/Game/UI/Logo`) 정규화·해석. |
| `Public/Misc/PackageName.h` | `FPackageName` (L33) — 정적 헬퍼 모음 | 경로 ↔ 파일명 변환·Mount 포인트 관리. |

---

## 3. 자주 쓰는 API

```cpp
// === 패키지 검색·생성 ===
UPackage* Pkg = FindPackage(/*Outer=*/nullptr, TEXT("/Game/UI/Logo"));
UPackage* New = CreatePackage(TEXT("/Game/Generated/MyPkg"));

// === 패키지 로드 ===
UPackage* Loaded = LoadPackage(/*Outer=*/nullptr, TEXT("/Game/UI/Logo"), LOAD_None);
// 비동기:
LoadPackageAsync(TEXT("/Game/UI/Logo"),
    FLoadPackageAsyncDelegate::CreateLambda([](const FName&, UPackage* P, EAsyncLoadingResult::Type R){ /* ... */ }));

// === 패키지 메타·상태 ===
Pkg->SetDirtyFlag(true);                        // Package.h L651 — 에디터에서만 의미
bool bDirty = Pkg->IsDirty();
bool bFull  = Pkg->IsFullyLoaded();             // L697
Pkg->FullyLoad();                               // L702 — 모든 export 강제 로드
Pkg->SetLoadedPath(FPackagePath::FromPackageName(TEXT("/Game/...")));  // L713

// === SavePackage (에디터/쿠킹) ===
FSavePackageArgs Args;
Args.TopLevelFlags = RF_Public | RF_Standalone;
Args.SaveFlags = SAVE_NoError;
Args.bForceByteSwapping = false;
const FString FileName = FPackageName::LongPackageNameToFilename(TEXT("/Game/UI/Logo"), FPackageName::GetAssetPackageExtension());
FSavePackageResultStruct Result = UPackage::Save(Pkg, /*Asset=*/MyAsset, *FileName, Args);

// === 경로 변환 (FPackageName 정적) ===
FString File = FPackageName::LongPackageNameToFilename(TEXT("/Game/UI/Logo"), FPackageName::GetMapPackageExtension());
FString Long; FPackageName::TryConvertFilenameToLongPackageName(File, Long);
bool bExists = FPackageName::DoesPackageExist(TEXT("/Game/UI/Logo"));
FName Mount  = FPackageName::GetPackageMountPoint(TEXT("/Game/UI/Logo"));
```

---

## 4. 가상 함수 (오버라이드 포인트)

UPackage 자체는 게임 코드에서 직접 상속하지 않는다 (엔진이 만든다). 패키지 라이프사이클의 게임-측 hook은 **UObject 의 PreSave/PostSaveRoot/Serialize/PostLoad/GetPreloadDependencies**에서 잡는다 — [`Serialization/`](../Serialization/SKILL.md) 참조.

`ISavePackageValidator` (`SavePackage.h:134`) 🛠 은 외부 검증을 꽂는 인터페이스로, 5.2에서 `FSavePackageContext::ExternalValidationFunc` 로 대체 권장 (deprecated 표시). 일반 게임 코드는 보통 만지지 않는다.

---

## 5. 예제

### 5.1 비동기 로드 + 콜백

```cpp
void UMyLoader::LoadLogoAsync()
{
    LoadPackageAsync(TEXT("/Game/UI/Logo"),
        FLoadPackageAsyncDelegate::CreateUObject(this, &UMyLoader::OnLogoLoaded),
        /*PackagePriority=*/0);
}

void UMyLoader::OnLogoLoaded(const FName& PackageName, UPackage* Package, EAsyncLoadingResult::Type Result)
{
    if (Result == EAsyncLoadingResult::Succeeded && Package)
    {
        UTexture2D* Tex = FindObject<UTexture2D>(Package, TEXT("Logo"));
        // 사용
    }
}
```

### 5.2 패키지 안의 모든 에셋 순회

```cpp
TArray<UObject*> Objs;
GetObjectsWithPackage(Pkg, Objs);                // UObjectHash.h
for (UObject* O : Objs)
{
    if (UTexture2D* T = Cast<UTexture2D>(O)) { /* ... */ }
}
```

### 5.3 경로 정규화

```cpp
// "C:/.../Project/Content/UI/Logo.uasset" → "/Game/UI/Logo"
FString Long;
if (FPackageName::TryConvertFilenameToLongPackageName(FilePath, Long))
{
    UPackage* P = LoadPackage(nullptr, *Long, LOAD_None);
}
```

### 5.4 SavePackage (에디터 빌드만 안전)

```cpp
#if WITH_EDITOR
bool SaveAssetToDisk(UObject* Asset)
{
    UPackage* Pkg = Asset->GetPackage();
    Pkg->SetDirtyFlag(true);

    FSavePackageArgs Args;
    Args.TopLevelFlags = RF_Public | RF_Standalone;
    Args.SaveFlags = SAVE_NoError;

    const FString File = FPackageName::LongPackageNameToFilename(
        Pkg->GetName(),
        Asset->IsA<UWorld>() ? FPackageName::GetMapPackageExtension()
                             : FPackageName::GetAssetPackageExtension());

    FSavePackageResultStruct R = UPackage::Save(Pkg, Asset, *File, Args);
    return R.Result == ESavePackageResult::Success;
}
#endif
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UPackage::SetDirtyFlag(bool)` 🛠 (실용) | Package.h L651 | (런타임에도 시그니처 존재) | 더티 플래그는 에디터 저장 흐름의 핵심 — 런타임 의미 없음. |
| `UPackage::Save(...)` 🛠 (실용) | Package.h | 쿠킹·에디터 저장 | 런타임에서 호출하면 비정상. |
| `FSavePackageArgs`, `FSavePackageSettings`, `FSavePackageContext` 🛠 | SavePackage.h L62, L186, L225 | 쿠킹·에디터 | 패키지 저장 옵션 묶음. |
| `ISavePackageValidator` 🛠 | SavePackage.h L134 | 쿠킹 검증 | 5.2에서 `ExternalValidationFunc` 로 대체. |
| `FArchiveSavePackageCollector` 🛠 | SavePackage.h L365 | 저장 시 | `FArchiveUObject` 자손, 저장 중 참조 수집. |
| `FLinkerSave`, `FSaveContext` 🛠 | LinkerSave.h L47, L34 | 저장 시 | 게임 코드에서 직접 만지지 않음. |
| `PackageReload.h` 🛠 | (전체) | `WITH_EDITOR` | Hot reload 통합. |
| `LinkerDiff.h` 🛠 | (전체) | `WITH_EDITOR` | 결정론 검증 — 두 저장 결과 비교. |
| `FPackageTrailer` (실용) 🛠 | PackageTrailer.h | (쿠킹·에디터) | EditorBulkData payload 위치 — 게임 런타임은 BulkData 직접 사용. |

> 게임 런타임에서 안전한 패키지 API는 `LoadPackage`/`LoadPackageAsync`/`FindPackage`/`CreatePackage`(런타임 동적) 와 `FPackageName` 정적 변환 정도. 저장·검증 계열은 에디터·쿠킹 전용.

---

## 7. 관련 sub-skill

- [`Serialization/`](../Serialization/SKILL.md) — `Serialize`/`PreSave`/`BulkData` 등 직렬화 본체
- [`UObject/`](../UObject/SKILL.md) — `Outer == nullptr` 인 경우는 패키지 자체뿐
- [`Cooking/`](../Cooking/SKILL.md) — 쿠킹 시 `IPackageWriter`·`UObjectRedirector` 처리
- [`ObjectHandles/`](../ObjectHandles/SKILL.md) — `FSoftObjectPath`/`FTopLevelAssetPath` 가 패키지 경로를 표현
