---
name: coreuobject-serialization
description: FArchive 직렬화 - Serialize 오버라이드 + FBulkData + LoadPackageAsync + PreSave/PostLoad + FObjectAndNameAsStringProxyArchive + Custom Version.
---

# CoreUObject / Serialization

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: `FArchive`의 UObject 확장, `BulkData`, `AsyncLoading2`(Iostore), 직렬화 관련 UObject virtual
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`Package/`](../Package/SKILL.md), [`Property/`](../Property/SKILL.md)

---

## 1. 개요

직렬화의 베이스인 `FArchive`는 `Core` 모듈에 있고, CoreUObject는 그 위에 **UObject·UPROPERTY·BulkData·비동기 로더** 확장을 얹는다. 핵심 구분:

1. **표준 직렬화** — `UObject::Serialize(FArchive&)` 가상 함수. UPROPERTY 자동 직렬화 + 사용자 추가 데이터.
2. **메모리 직렬화** — `FObjectReader`/`FObjectWriter` (메모리 버퍼 ↔ UObject).
3. **BulkData** — 텍스처·오디오 같은 큰 페이로드를 본 직렬화 스트림과 분리. 지연 로드/메모리 매핑.
4. **AsyncLoading2 (Iostore)** — 5.x 표준 비동기 패키지 로더. Zen 패키지 포맷.
5. **EditorBulkData / DerivedData** — 에디터·쿠킹 빌드 전용. DDC 키 관리.

---

## 2. 핵심 헤더와 클래스

### 2.1 UObject용 FArchive 확장

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/ArchiveUObjectBase.h` | (`FArchive` 보조) | `FArchive` 의 UObject 인지 베이스 보조. |
| `Public/Serialization/ArchiveUObject.h` | `class FArchiveUObject : public FArchive` (L16) | UObject 인지 가능한 FArchive 베이스. |
| `Public/Serialization/ArchiveUObjectFromStructuredArchive.h` | `FArchiveUObjectFromStructuredArchive` (L82, L24 impl) | StructuredArchive(텍스트/JSON) ↔ FArchive 어댑터. |

### 2.2 메모리 직렬화 (UObject↔버퍼)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/ObjectWriter.h` | `class FObjectWriter : public FMemoryWriter` (L27) | UObject의 모든 UPROPERTY를 메모리 버퍼로. |
| `Public/Serialization/ObjectReader.h` | `class FObjectReader : public FMemoryArchive` (L28) | 위의 역방향. 객체 복제·트랜잭션·임시 저장에 사용. |
| `Public/Serialization/DuplicatedDataReader.h`, `DuplicatedDataWriter.h`, `DuplicatedObject.h` | `FDuplicateDataReader/Writer`, `FDuplicatedObject` | UObject 복제 (`StaticDuplicateObject`)의 내부. |

### 2.3 BulkData (대용량 페이로드)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/BulkData.h` | `FBulkData` (L469), `TBulkData<T>` (L1035), `FBulkMetaData` (L308), `FFormatContainer` (L1138), `FBulkDataRequest` (L1193), `FBulkDataBatchRequest : FBulkDataRequest` (L1294), `IBulkDataIORequest` (L83) | 메인 직렬화 스트림과 분리되는 큰 페이로드. 텍스처·메시·오디오의 픽셀/샘플 데이터. |
| `Public/Serialization/BulkDataReader.h`, `BulkDataWriter.h` | `FBulkDataReader`, `FBulkDataWriter` | BulkData를 일반 FArchive 처럼 다룸. |
| `Public/Serialization/BulkDataBuffer.h` | `FBulkDataBuffer<T>` | BulkData의 메모리 뷰. |
| `Public/Serialization/BulkDataScopedLock.h` | `FBulkDataScopedLock` | BulkData 동시 접근 보호. |
| `Public/Serialization/BulkDataCookedIndex.h` | `FBulkDataCookedIndex` | 쿠킹된 BulkData 색인. |
| `Public/Serialization/BulkDataRegistry.h` | `IBulkDataRegistry` 등 🛠 | BulkData 추적 (에디터). |

### 2.4 비동기 로더 (Iostore / Zen)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/AsyncLoading2.h` | `FZenPackageSummary` (L303), `FZenPackageVersioningInfo` (L283), `FExportBundleEntry` (L328), `FExportMapEntry` (L378), `FBulkDataMapEntry` (L405), `FPackageObjectIndex` (L59), `FPublicExportKey` (L180), `FRuntimeScriptPackages` (L423) | 5.x Iostore 패키지 포맷 + 비동기 로딩 본체. |
| `Public/Serialization/AsyncLoadingEvents.h` | `EAsyncLoadingEvent` 등 | 로딩 단계 이벤트. |
| `Public/Serialization/AsyncLoadingFlushContext.h` | `FAsyncLoadingFlushContext` | 동기화/플러시. |
| `Public/Serialization/AsyncPackageLoader.h` | `IAsyncPackageLoader` | 로더 인터페이스 (EDL/Zen 백엔드 추상). |
| `Public/Serialization/PackageStore.h` | `FPackageStore` (L226), `IPackageStoreBackend` (L188), `FPackageStoreEntry` (L49), `FPackageStoreReadScope` (L266) | 패키지 위치 인덱스. |
| `Public/Serialization/TransactionallySafeAsyncLoading.h` | (AutoRTFM 통합) | 트랜잭션 안전 비동기 로드. |

### 2.5 패키지 라이터·DerivedData (쿠킹/에디터)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/BasePackageWriter.h` | `FBasePackageWriter` (L8), `FBaseCookedPackageWriter` (L21) 🛠 | 쿠킹 시 패키지 출력 베이스. |
| `Public/Serialization/EditorBulkData.h` | `FEditorBulkData` (L131) 🛠 | 에디터 전용 BulkData (5.x) — `WITH_EDITORONLY_DATA`. |
| `Public/Serialization/EditorBulkDataReader.h`, `EditorBulkDataWriter.h` 🛠 | 동상 | |
| `Public/Serialization/DerivedData.h` | `UE::FDerivedData`, `UE::DerivedData::FCacheKey` 등 🛠 | DDC 통합. |

### 2.6 참조 검색 / 마이그레이션 보조

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Serialization/FindReferencersArchive.h` | `FFindReferencersArchive` | 누가 이 객체를 참조하는지. |
| `Public/Serialization/FindObjectReferencers.h` | 동상 헬퍼 | |
| `Public/Serialization/ArchiveReplaceObjectRef.h` | `FArchiveReplaceObjectRef<T>` | 모든 참조를 일괄 치환. |
| `Public/Serialization/ArchiveStackTrace.h` | `FArchiveStackTrace` 🛠 | 결정론 직렬화 검증 (쿠킹 비교). |

---

## 3. 자주 쓰는 API

```cpp
// === 표준 Serialize (UObject virtual) ===
void UMyAsset::Serialize(FArchive& Ar)
{
    Super::Serialize(Ar);                 // UPROPERTY 자동 직렬화
    Ar << CustomBuffer;                   // FArchive operator<< — 추가 데이터
    Ar << CustomCount;
    if (Ar.IsLoading() && CustomCount > LegacyMax)
        CustomCount = LegacyMax;          // 마이그레이션
}

// === 메모리 ↔ UObject ===
TArray<uint8> Bytes;
{
    FObjectWriter W(MyObj, Bytes);        // 모든 UPROPERTY → Bytes
}
{
    FObjectReader R(MyObj, Bytes);        // Bytes → MyObj 복원
}

// === 객체 복제 ===
UMyAsset* Copy = DuplicateObject<UMyAsset>(Original, /*Outer=*/Owner);

// === BulkData (대용량) ===
class UMyData : public UObject
{
public:
    FByteBulkData PixelData;              // 본 직렬화와 분리
    virtual void Serialize(FArchive& Ar) override
    {
        Super::Serialize(Ar);
        PixelData.Serialize(Ar, this);    // 지연 로드 가능 형태로 저장
    }
};

// === 비동기 로드 ===
LoadPackageAsync(TEXT("/Game/UI/Logo"), FLoadPackageAsyncDelegate::CreateLambda(
    [](const FName&, UPackage* Pkg, EAsyncLoadingResult::Type Result)
    { /* Pkg 사용 */ }));
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 UObject 직렬화 virtual (`Public/UObject/Object.h`)

| 시그니처 | 위치 | 호출 시점 / 용도 |
|----------|------|------------------|
| `virtual void Serialize(FArchive& Ar)` | Object.h L393 | **표준 직렬화 진입점.** UPROPERTY 자동 + 추가 데이터. **반드시 `Super::Serialize(Ar)` 첫 줄에**. |
| `virtual void Serialize(FStructuredArchive::FRecord)` | Object.h L394 | Structured(텍스트/JSON) 버전. |
| `virtual void PreSave(FObjectPreSaveContext)` | Object.h L283 | SavePackage 직전. 캐시 갱신·파생 데이터 산출. |
| `virtual void PreSaveRoot(FObjectPreSaveRootContext)` | Object.h L267 | 패키지 루트 객체에서만 호출. |
| `virtual void PostSaveRoot(FObjectPostSaveRootContext)` | Object.h L275 | 저장 종료 후 루트. |
| `virtual void CollectSaveOverrides(FObjectCollectSaveOverridesContext)` | Object.h L288 | 저장 시 일부 프로퍼티만 다른 값으로 직렬화. |
| `virtual void GetPreloadDependencies(TArray<UObject*>&)` | Object.h L632 | 로드 순서 보장이 필요한 외부 객체 알림. |
| `virtual void PostLoad()` | Object.h L351 | 디스크 로드 + 참조 해소 후. **버전 마이그레이션 표준 위치.** |

### 4.2 FProperty PURE_VIRTUAL (직렬화 본체)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void SerializeItem(FStructuredArchive::FSlot, void*, const void*) const` | UnrealType.h L581 | 단일 프로퍼티 값 직렬화 — 자세한 건 [`Property/`](../Property/SKILL.md). |
| `virtual EConvertFromTypeResult ConvertFromType(...)` | UnrealType.h L1992 | 옛 직렬화 데이터의 타입 변환. |

### 4.3 패키지 라이터 (쿠킹) 🛠

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `IPackageWriter::*` 🛠 | BasePackageWriter.h L8~ | 패키지 출력. 일반 게임 코드 안 씀. |
| `ICookedPackageWriter::*` 🛠 | BasePackageWriter.h L21~ | 쿠킹 산출물 출력. |

---

## 5. 예제

### 5.1 버전 마이그레이션이 있는 Serialize

```cpp
namespace FMyAssetVersion
{
    enum Type { Initial = 0, AddedTags = 1, RenamedField = 2, Latest = RenamedField };
};

void UMyAsset::Serialize(FArchive& Ar)
{
    Super::Serialize(Ar);

    int32 Ver = FMyAssetVersion::Latest;
    Ar << Ver;

    if (Ar.IsLoading() && Ver < FMyAssetVersion::AddedTags)
    {
        Tags.Empty();      // 기본값 적용
    }
    Ar << Tags;

    if (Ver >= FMyAssetVersion::RenamedField) Ar << NewName;
    else if (Ar.IsLoading()) NewName = OldName;
}
```

### 5.2 BulkData를 가진 자산

```cpp
UCLASS()
class UMyHeightField : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY()
    int32 Width = 0;

    UPROPERTY()
    int32 Height = 0;

    FByteBulkData Heights;            // 큰 픽셀/높이 데이터

    virtual void Serialize(FArchive& Ar) override
    {
        Super::Serialize(Ar);
        Heights.Serialize(Ar, this);
    }
};
```

### 5.3 누가 이 객체를 참조하는가?

```cpp
TArray<UObject*> Referencers;
FFindReferencersArchive Find(SuspiciousObj, Referencers);
// Referencers 에 후보 채워짐 — 디버깅용
```

### 5.4 모든 참조를 다른 객체로 치환

```cpp
TMap<UObject*, UObject*> Replacements;
Replacements.Add(OldAsset, NewAsset);
FArchiveReplaceObjectRef<UObject> Replace(World, Replacements, EArchiveReplaceObjectFlags::None);
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FEditorBulkData` 🛠 | EditorBulkData.h L131 | `WITH_EDITORONLY_DATA` | 에디터 내부 BulkData. 쿠킹 산출물에는 `FBulkData` 로 변환. |
| `FEditorBulkDataReader/Writer` 🛠 | EditorBulkDataReader.h, EditorBulkDataWriter.h | `WITH_EDITORONLY_DATA` | |
| `UE::FDerivedData`, `FCacheKey`, `FValueId` 🛠 | DerivedData.h | (DDC = `DerivedDataCache` 모듈, 에디터 빌드 의존) | 파생 데이터(텍스처 변환·셰이더 컴파일 결과 등) 캐시 키. |
| `FBaseCookedPackageWriter` 🛠 | BasePackageWriter.h L21 | 쿠킹·`WITH_EDITOR` | 쿠킹 시 패키지 출력. |
| `IBulkDataRegistry` 🛠 | BulkDataRegistry.h | `WITH_EDITOR` | BulkData 추적. |
| `FArchiveStackTrace` 🛠 | ArchiveStackTrace.h | `WITH_EDITOR` (결정론 검증) | 두 번 직렬화 결과 비교 — 쿠킹 결정론 회귀 탐지. |
| `PreSave/PostSaveRoot/CollectSaveOverrides` 🛠 (실용) | Object.h L267·L275·L288 | (런타임에도 시그니처 존재) | 사용처는 거의 SavePackage·쿠킹 — 게임 런타임 무관. |
| `GetAssetRegistryTags(...)` 🛠 | Object.h L898·L900 | `WITH_EDITORONLY_DATA` 영향 | [`Editor/`](../Editor/SKILL.md). |

> 게임 런타임에서 자주 쓰는 것은 `Serialize(FArchive&)` 와 `BulkData` 정도. `EditorBulkData`, `DerivedData`, `PackageWriter` 류는 모두 에디터·쿠킹 전용이다.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — `Serialize` 가상 함수의 라이프사이클 위치
- [`Package/`](../Package/SKILL.md) — `UPackage`/`Linker`/`SavePackage` 와 본 sub-skill의 짝
- [`Property/`](../Property/SKILL.md) — `FProperty::SerializeItem` 의 PURE_VIRTUAL 구현
- [`Cooking/`](../Cooking/SKILL.md) — `BeginCacheForCookedPlatformData`·`PreSave` 와 쿠킹 라이터의 결합
