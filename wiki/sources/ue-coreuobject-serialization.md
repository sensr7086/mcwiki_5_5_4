---
type: source
title: "UE CoreUObject — Serialization sub-skill"
slug: ue-coreuobject-serialization
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Serialization.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-18
related_entities:
  - "[[entities/UPackage]]"
related_concepts:
  - "[[concepts/Asset-Lifecycle]]"
  - "[[concepts/BulkData]]"
tags: [ue, runtime, foundation, coreuobject, serialization, case-study-pair, kmcproject-pair, deprecated-uproperty, container-migration, postload-rename-outer]
---

# UE CoreUObject — Serialization sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Serialization.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

FArchive 직렬화 — Serialize override + [[concepts/BulkData]] (FBulkData) + LoadPackageAsync + PreSave/PostLoad + FObjectAndNameAsStringProxyArchive (BP variable-as-text 직렬화) + Custom Version (자산 버전 마이그레이션) + PostLoad DEPRECATED 접미사 마이그레이션 (Class.cpp brute force search) + **§5.7 (Cycle 5p+2 신규) — 컨테이너 마이그레이션 + UObject::Rename Outer 교체 4-step**.

## 2. Key claims

- FArchive: 직렬화의 베이스 — `<<` operator override. ArIsLoading / ArIsSaving 분기.
- UObject::Serialize(FArchive& Ar) override: 표준 패턴. UPROPERTY 가 자동 직렬화하지만, 수동 데이터 (BulkData / 캐시) 는 override 필요.
- Custom Version: FCustomVersion 등록 → 옛 자산 로드 시 마이그레이션.
- PreSave / PostLoad — 직렬화 전후 hook.
- FObjectAndNameAsStringProxyArchive — UObject 참조를 path string 으로 직렬화 (BP variable inspector 등).
- `Ar << bUseField` 패턴: 직렬화 시 분기 (예: 옛 버전 호환).
- LoadPackageAsync — 비동기 patch.
- **§5 신규 (Cycle 5p §B3)** — PostLoad DEPRECATED 접미사 마이그레이션 — `UStruct::SerializeTaggedProperties` + PropertyTag matching + brute force search 기반.
- **§5.7 신규 (Cycle 5p+2)** — 컨테이너 마이그레이션 (TArray 자체 deprecated) + UObject::Rename Outer 교체 + placeholder 부모 생성 4-step. KMCProject Phase 4c 사례 일반화.

## 3. Quotations

> "직렬화 + Custom Version 으로 자산 마이그레이션 — 옛 자산 깨짐 회피."

## 4. Open questions

- [ ] FStructuredArchive (5.x) vs FArchive 차이
- [ ] FObjectAndNameAsStringProxyArchive 의 한계 (Soft vs Hard ref)
- [ ] PostLoad 마이그레이션이 cooked build 시 실행되는 시점 (자산 cook 시점 vs runtime 시점 — `GIsCookerLoadingPackage` 가드 결정 트리)

## 5. ⭐ PostLoad 마이그레이션 (DEPRECATED 접미사 패턴) — Cycle 5p §B3 신규

### 5.1 Engine 권위 — `_DEPRECATED` 접미사 brute force search

→ Engine 본가: `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp` L1514 / L1690-L1760 / L1742 (UE 5.7.4 verify).

`UStruct::SerializeTaggedProperties` 는 자산 로드 시 PropertyTag 와 현재 UPROPERTY 를 매칭한다. 이름이 변경된 경우:

1. **CoreRedirects** — `Engine/Config/BaseEngine.ini` 에 `[CoreRedirects]` 등록 (이름 매핑)
2. **`_DEPRECATED` 접미사** — UPROPERTY 이름 자체에 접미사 추가. Class.cpp L1690-L1760 의 **brute force search** 가 자동으로 `XXX` ↔ `XXX_DEPRECATED` 매칭 (CoreRedirects 등록 불필요)

`_DEPRECATED` 접미사 패턴이 권장 — `.ini` 외부 의존성 회피.

### 5.2 PostLoad 마이그레이션 3-step (단일 필드)

```cpp
// MyAsset.h
UCLASS()
class UMyAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    virtual void PostLoad() override;

    // 신규 필드
    UPROPERTY(EditAnywhere, ..., Category = "Range")
    FMyNewRange RangeData;  // USTRUCT 래퍼 (TRange 직접 UPROPERTY 불가 — UHT 미지원)

    // DEPRECATED — Cycle N 종료 시 삭제 의무
    UPROPERTY()  // EditAnywhere X — 마이그레이션 전용
    FFrameNumber StartFrame_DEPRECATED;
    UPROPERTY()
    FFrameNumber EndFrame_DEPRECATED;
};
```

```cpp
// MyAsset.cpp PostLoad — idempotency 보장
void UMyAsset::PostLoad()
{
    Super::PostLoad();  // 의무 — 자손 override 시 누락 시 마이그레이션 실패

    // 마이그레이션 분기 — DEPRECATED 0 리셋으로 두 번째 호출 시 분기 skip
    if (StartFrame_DEPRECATED.Value != 0 || EndFrame_DEPRECATED.Value != 0)
    {
        RangeData = FMyNewRange(StartFrame_DEPRECATED, EndFrame_DEPRECATED);
        StartFrame_DEPRECATED = FFrameNumber(0);
        EndFrame_DEPRECATED   = FFrameNumber(0);
    }
}
```

⭐ **3-step 의무**:
1. **DEPRECATED 접미사** — UPROPERTY 이름에 `_DEPRECATED` 접미사 추가 (CoreRedirects 불필요)
2. **PostLoad idempotency** — DEPRECATED 필드를 마이그레이션 후 0 으로 리셋 → 두 번째 호출 시 분기 skip
3. **Cycle cutoff 명문화** — 헤더 주석에 제거 시점 (예: Cycle 6 종료) 명시 + `git grep "XXX_DEPRECATED"` → 0 hits 확인 후 삭제

### 5.3 함정 — `Super::PostLoad()` 누락

자손 클래스가 PostLoad override 시 `Super::PostLoad()` 첫 줄 호출 누락 시 **베이스 마이그레이션 미실행** → 자산 깨짐 가능성.

방어 패턴:
- 자손 PostLoad 선언부 위에 안내 주석 ("자손 override 시 반드시 Super::PostLoad() 선행 호출 의무 — 베이스가 _DEPRECATED 마이그레이션 수행")
- 코드 리뷰 시 자손 PostLoad 의 Super 호출 강제 점검

### 5.4 False-positive — Phase 1 자산이 DEPRECATED 0 으로 저장된 경우

`StartFrame_DEPRECATED == 0 && EndFrame_DEPRECATED == 0` 인 자산 (예: 신규 생성 직후 저장) 은 마이그레이션 분기 skip. RangeData 가 생성자 default 값으로 유지됨.

실무 상 영향:
- Phase 1 자산 0건 환경 (디자이너 아직 미작성) → 영향 0
- 자산 작성 후 cutoff 도달 전 발견 시 수동 RangeData 셋 의무

### 5.5 ⭐ Case Study: KMCProject FMCComboFrameRange + UMCComboSection (Cycle 5p §B3)

> **case study 페어**: [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §5 (PostLoad BC compat 패턴) + [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5.3 (Phase 2 베이스 격상 — PostLoad).
>
> **vault scope 정책** ([[00_meta/08_VaultScopePolicy]]): 본 sub-§은 KMCProject (mc-) 실측 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강한 항목.

KMCProject `UMCComboSection` 베이스가 Phase 2a-refactor 에서 4 → 12 필드 격상 시 **§5.2 3-step 패턴을 그대로 적용**:

| 변경 | 옛 UPROPERTY | 신규 UPROPERTY | 마이그레이션 |
| -- | -- | -- | -- |
| 1 | `FFrameNumber StartFrame` | `FFrameNumber StartFrame_DEPRECATED` (UPROPERTY() 만, EditAnywhere X) | PostLoad — `SectionRange = FMCComboFrameRange(StartFrame_DEPRECATED, EndFrame_DEPRECATED)` |
| 2 | `FFrameNumber EndFrame` | `FFrameNumber EndFrame_DEPRECATED` (동일) | (위와 같이) |
| 3 | (없음 — 신규) | `FMCComboFrameRange SectionRange` (USTRUCT 래퍼) | 마이그레이션 결과 저장 |

⭐ **idempotency 보장**:
```cpp
void UMCComboSection::PostLoad()
{
    Super::PostLoad();
    if (StartFrame_DEPRECATED.Value != 0 || EndFrame_DEPRECATED.Value != 0)
    {
        const FFrameNumber NewStart = StartFrame_DEPRECATED;
        const FFrameNumber NewEnd   = (EndFrame_DEPRECATED.Value < NewStart.Value) ? NewStart : EndFrame_DEPRECATED;
        SectionRange = FMCComboFrameRange(NewStart, NewEnd);
        StartFrame_DEPRECATED = FFrameNumber(0);
        EndFrame_DEPRECATED   = FFrameNumber(0);
    }
}
```

⭐ **Cycle 6 cutoff 명문화** — KMCProject Phase 2 의 cutoff 결정:
```cpp
/** DEPRECATED — Phase 2a 마이그레이션 전용. 제거 시점: Cycle 6 종료
 *  (모든 .uasset 재저장 후 git grep "StartFrame_DEPRECATED" → 0 hits 확인 후 삭제). */
UPROPERTY()
FFrameNumber StartFrame_DEPRECATED;
```

⭐ **자손 PostLoad 안내 주석** — `UMCComboSection` 의 자손 (`UMCComboMontageSection` / `UMCComboInputSection` / `UMCComboNotifySection`) 이 PostLoad override 시 Super 호출 의무:
```cpp
/** 자손 override 시 반드시 Super::PostLoad() 선행 호출 의무.
 *  베이스 PostLoad 가 _DEPRECATED 마이그레이션을 수행하므로 누락 시 마이그레이션 실패. */
virtual void PostLoad() override;
```

### 5.6 evaluator 검증 (Cycle 5p)

본 sub-§ 의 권위 인용 (`Class.cpp L1514 / L1690-L1760 / L1742`) 은 KMCProject Phase 2a-refactor evaluator (91.0 / 100 PASS) 가 직접 verify. UE 5.7.4 (Build.version verify ✓) 에서 함수명 / 라인 모두 일치.

## 5.7 ⭐⭐ 컨테이너 마이그레이션 패턴 + UObject::Rename Outer 교체 4-step (Cycle 5p+2 신규)

> §5.2 의 3-step 패턴이 *단일 UPROPERTY 필드 마이그레이션* 을 다룬다면, §5.7 은 **컨테이너 (TArray<TObjectPtr<UObject>>) 자체 가 deprecated 되어 *새 부모 컨테이너* 로 이전되는 케이스** 를 다룬다. 단일 필드 4-step (DEPRECATED + PostLoad + Cycle cutoff + idempotent) 에 **Outer 교체 의무** 가 추가된 형태.
>
> 일반화 트리거: KMCProject Phase 4c (`synthesis/mc-combo-editor-levelsequence-lite` §5.7.9).

### 5.7.1 결정 트리 — 단일 필드 vs 컨테이너

| 케이스 | 적용 패턴 | 비고 |
| -- | -- | -- |
| 단일 UPROPERTY 필드의 *값* 형태 변경 (예: FFrameNumber × 2 → FMCComboFrameRange USTRUCT) | **§5.2 3-step** | 필드값 복사 + 0 리셋만으로 idempotent |
| TArray / TMap / 단일 UObject 참조의 *컨테이너 자체* 가 새 부모 모델로 이전 (예: Asset->Tracks → Asset->Bindings → Binding->Tracks 5단계 계층 진입) | **§5.7 4-step** (본 sub-§) | 컨테이너 element 의 *Outer 교체* (UObject::Rename) 의무 + placeholder 부모 생성 가능 |
| 별도 UPROPERTY 이름 변경 (단순 rename) | CoreRedirects 또는 `_DEPRECATED` 접미사만으로 충분 (§5.1) | 마이그레이션 코드 불필요 |
| UClass 자체 변경 (예: 베이스 클래스 교체) | Class redirect + PostLoad 안 `IsA` 분기 후 신규 객체 생성 (별도 §) | 본 §5.7 범위 외 |

### 5.7.2 Engine 권위 — UObject::Rename + ERenameFlags

→ Engine 본가: `Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h` L1090 (`UObject::Rename`) + 동 파일 `ERenameFlags` enum 정의 (UE 5.7.4 verify).

```cpp
// UObject::Rename 시그니처 (Engine 권위)
virtual bool Rename(const TCHAR* NewName = nullptr,
                    UObject* NewOuter = nullptr,
                    ERenameFlags Flags = REN_None);
```

**ERenameFlags 핵심 3 조합 (PostLoad 마이그레이션 의무)**:

| Flag | 값 | 의미 | PostLoad 마이그레이션 필요성 |
| -- | -- | -- | -- |
| `REN_None` | 0x0000 | 기본 (redirector 생성 + dirty + transactional) | ❌ 모든 부작용 발생 — 사용 X |
| `REN_ForceNoResetLoaders` | 0x0001 | LinkerLoad 강제 보존 | ⚠ 일반 PostLoad 마이그레이션 불필요 |
| `REN_Test` | 0x0002 | 실제 rename 안 함, 가능 여부만 확인 | ⚠ 본 마이그레이션 외 — dry-run 용 |
| **`REN_DoNotDirty`** | **0x0004** | **package dirty 마크 회피** | **✅ 의무 — PostLoad 가 매 자산 로드 시 dirty 시키면 사용자 의도 외 변경 마크 폭주** |
| `REN_DontCreateRedirectors` | 0x0010 | ObjectRedirector 생성 회피 | ✅ 의무 — stale redirector 가 cooked 빌드에서 dead reference 유발 |
| `REN_NonTransactional` | 0x0020 | undo stack 등록 회피 | ✅ 의무 — PostLoad 가 undo entry 추가 시 자산 열기만 해도 undo 1건 |
| `REN_ForceGlobalUnique` | 0x0040 | 전역 unique 이름 강제 | ⚠ 본 마이그레이션 외 |
| `REN_SkipGeneratedClasses` | 0x0080 | BP-generated class skip | ⚠ 본 마이그레이션 외 |

⭐ **3 flags 의무 조합 (PostLoad 컨테이너 마이그레이션)**:
```cpp
Track->Rename(nullptr, NewOuter,
    REN_DontCreateRedirectors | REN_NonTransactional | REN_DoNotDirty);
```

### 5.7.3 4-step 패턴 (컨테이너 마이그레이션)

```cpp
// MyAsset.h
UCLASS()
class UMyAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    virtual void PostLoad() override;

    // 신규 컨테이너 (새 부모 모델)
    UPROPERTY(EditAnywhere, Instanced, Category = "Hierarchy")
    TArray<TObjectPtr<UMyParent>> Parents;

    // DEPRECATED — 옛 컨테이너 (직접 자식)
    UPROPERTY(meta = (DeprecatedProperty,
        DeprecationMessage = "Use Parents → Parent->Children instead. PostLoad 자동 마이그레이션."))
    TArray<TObjectPtr<UMyChild>> Children_DEPRECATED;
};
```

```cpp
// MyAsset.cpp PostLoad — 4-step 컨테이너 마이그레이션
void UMyAsset::PostLoad()
{
    Super::PostLoad();  // §5.3 의무

    // Step 1: idempotency 조기 종료 (이미 마이그레이션 됨 또는 옛 데이터 없음)
    if (Children_DEPRECATED.Num() == 0)
    {
        return;
    }

    // Step 2: placeholder 새 부모 생성 — 옛 데이터의 default 새 부모 1개.
    //   (Outer = this Asset, Transactional 플래그 — undo/redo 안전)
    UMyParent* LegacyParent = NewObject<UMyParent>(this, NAME_None, RF_Transactional);
    if (!LegacyParent)
    {
        UE_LOG(LogTemp, Error,
            TEXT("UMyAsset::PostLoad — Legacy Parent 생성 실패. 마이그레이션 중단."));
        return;
    }
    LegacyParent->DisplayName = TEXT("(Legacy)");

    // Step 3: 각 element 의 Outer 교체 (UObject::Rename) + 새 부모로 이전.
    //   3 flags 의무 조합 — REN_DontCreateRedirectors | REN_NonTransactional | REN_DoNotDirty.
    for (const TObjectPtr<UMyChild>& ChildPtr : Children_DEPRECATED)
    {
        UMyChild* Child = ChildPtr.Get();
        if (!Child)
        {
            continue;
        }
        Child->Rename(nullptr, LegacyParent,
            REN_DontCreateRedirectors | REN_NonTransactional | REN_DoNotDirty);
        LegacyParent->Children.Add(Child);
    }

    // Step 4: 새 컨테이너 등록 + DEPRECATED 비우기 + 자산 dirty (저장 시 마이그레이션 영구 적용).
    Parents.Add(LegacyParent);
    Children_DEPRECATED.Empty();

#if WITH_EDITOR
    MarkPackageDirty();  // 다음 저장 시 마이그레이션 결과 직렬화 보장
#endif

    UE_LOG(LogTemp, Log,
        TEXT("UMyAsset::PostLoad — 마이그레이션 완료: Children_DEPRECATED %d → (Legacy) Parent 이전."),
        LegacyParent->Children.Num());
}
```

### 5.7.4 4-step 의무 매트릭스

| Step | 동작 | 의무 사유 |
| -- | -- | -- |
| **1. idempotency 조기 종료** | `Children_DEPRECATED.Num() == 0 → return` | 사용자 미저장 시 매 로드 재실행 — 부작용 없으려면 새 부모 데이터 검증 후 조기 종료 |
| **2. placeholder 부모 생성** | `NewObject<UMyParent>(this, ..., RF_Transactional)` | 옛 자식이 새 부모를 필요로 함. 비어있는 placeholder + 사용자가 Detail 패널에서 후속 설정 권고 |
| **3. Outer 교체 (UObject::Rename)** | `Child->Rename(nullptr, NewOuter, 3 flags)` | 새 부모 = 새 Outer (UCLASS Instanced 패턴) — `NewObject<>(NewParent, ...)` 의무 미러. 3 flags 누락 시 §5.7.5 함정 A/B/C 발생 |
| **4. 새 컨테이너 등록 + Empty + Dirty** | `Parents.Add + Children_DEPRECATED.Empty + MarkPackageDirty` | Empty 누락 시 매 로드 반복 마이그레이션 / Dirty 누락 시 사용자가 명시 저장 안 하면 disk 데이터 변경 X |

### 5.7.5 함정 A/B/C/D — 3 flags 누락 영향

| 함정 | 누락 flag | 증상 |
| -- | -- | -- |
| **A** | `REN_DoNotDirty` 누락 | PostLoad 가 매 자산 로드 시 package dirty 마크 → 사용자가 자산 열기만 해도 "수정됨" 표시 + Save All 시 무의미 변경 폭주 |
| **B** | `REN_DontCreateRedirectors` 누락 | 옛 Outer → 새 Outer 경로에 `ObjectRedirector` 자동 생성 → cooked 빌드에서 dead reference 또는 zombie redirector 누적 |
| **C** | `REN_NonTransactional` 누락 | PostLoad 가 undo stack 에 entry 추가 → 자산 열기만 해도 undo 1건 추가 ("Rename Track1" 등) + transaction memory 누적 |
| **D** | (구조적) Empty() 누락 | DEPRECATED 컨테이너 비우지 않으면 매 로드 마이그레이션 재실행 → in-memory 누적 (Parents 안 LegacyParent 중복 1, 2, 3, ...). 단 사용자 저장 시 1회로 수렴 |

### 5.7.6 ⭐ Case Study: KMCProject Phase 4c (Cycle 5p+2)

> **case study 페어**: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.7.9 (Phase 4c — Tracks → Bindings 컨테이너 마이그레이션).
>
> **vault scope 정책** ([[00_meta/08_VaultScopePolicy]]): 본 sub-§은 KMCProject (mc-) 실측 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강한 항목.

KMCProject `UMCComboAsset` 가 Phase 4c 에서 5단계 계층 (AssetRoot → Binding → Track → Section → SubProperty) 진입 시 §5.7.3 4-step 패턴 그대로 적용:

| Step | KMCProject 적용 | 코드 |
| -- | -- | -- |
| 1. idempotency | `Tracks_DEPRECATED.Num() == 0 → return` | `UMCComboAsset::PostLoad` 첫 줄 |
| 2. placeholder | `LegacyBinding = NewObject<UMCComboBinding>(this, NAME_None, RF_Transactional); LegacyBinding->DisplayName = TEXT("(Legacy)");` | SkeletalMesh 비어있는 상태 → 사용자가 Detail 패널에서 셋 |
| 3. Outer 교체 | `Track->Rename(nullptr, LegacyBinding, REN_DontCreateRedirectors \| REN_NonTransactional \| REN_DoNotDirty);` | 3 flags 의무 조합 |
| 4. Empty + Dirty | `Bindings.Add(LegacyBinding); Tracks_DEPRECATED.Empty(); MarkPackageDirty();` | WITH_EDITOR 가드 |

**Engine 권위 매트릭스 (Phase 4c verify, UE 5.7.4)**:
- `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h` L425 — `virtual void PostLoad()` 표준 hook
- `Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h` L1090 — `UObject::Rename` + ERenameFlags 정의
- `Engine/Source/Runtime/MovieScene/Public/MovieScene.h` — `FMovieScene::Possessables_DEPRECATED` 미러 패턴 (Engine 본가가 동일 4-step 적용)

**KMCProject Phase 4c 빌드 PASS 검증** (2026-05-18) — 본 §5.7.3 / §5.7.4 / §5.7.5 모두 실측 verify.

## 6. Cross-link

### Engine 권위

- `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp` L1514 (`UStruct::SerializeTaggedProperties`) / L1690-L1760 (PropertyTag matching + brute force search) / L1742 (_DEPRECATED 접미사 자동 매칭)
- `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h` L425 (`virtual void PostLoad()` — §5.7 표준 hook)
- `Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h` L1090 (`UObject::Rename` + ERenameFlags — §5.7 컨테이너 마이그레이션 의무)
- `Engine/Source/Runtime/MovieScene/Public/MovieSceneSection.h` L834-L848 (`StartTime_DEPRECATED` 등 Engine 본가 단일 필드 사례 — §5.2)
- `Engine/Source/Runtime/MovieScene/Public/MovieSceneFrameMigration.h` L26-L104 (`FMovieSceneFrameRange` USTRUCT 래퍼 — UPROPERTY 부착용 패턴)
- `Engine/Source/Runtime/MovieScene/Public/MovieScene.h` (`FMovieScene::Possessables_DEPRECATED` — §5.7 컨테이너 마이그레이션 Engine 본가 사례)

### Parent / 페어 sub-skills

- Parent: [[sources/ue-coreuobject-skill]]
- 페어 sub-skill: [[sources/ue-coreuobject-uobject]] (UObject 라이프사이클 + §2.14 Instanced 4 meta + §2.17 후보 PostLoad 일반화) · [[sources/ue-coreuobject-property]] (UPROPERTY meta) · [[sources/ue-coreuobject-package]] (UPackage 직렬화) · [[sources/ue-coreuobject-deprecateduproperty]] (UProperty → FProperty 4.x→5.x + §3 컨테이너 마이그레이션 cross-link)

### Concept

- [[concepts/Asset-Lifecycle]] · [[concepts/BulkData]] · [[concepts/Cooked-vs-Uncooked]]

### ⭐ Case study (mc-, Cycle 5p §B3 + Cycle 5p+2 §5.7)

- [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §5 (Phase 1 handoff document — PostLoad BC compat 패턴 명세 — §5.2 사례)
- [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5.3 (Phase 2 누적 합성 — FMCComboFrameRange + PostLoad idempotency 실측 — §5.2 사례) + **§5.7.9 (Phase 4c — Tracks → Bindings 컨테이너 마이그레이션 — §5.7 사례)**

### Governance (Cycle 5p / 5p+2)

- [[00_meta/08_VaultScopePolicy]] §3 — `mc-` 페이지 사례를 `ue-` 일반 페이지에 reverse-link 의무 (본 §5.5 + §5.7.6)
- [[00_meta/03_EvaluatorRecipe]] §1.5 — Stage 2.X Engine Authority Verification (본 §5.6 + §5.7.6)
