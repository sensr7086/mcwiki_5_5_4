---
type: source
title: "UE CoreUObject — DeprecatedUProperty sub-skill"
slug: ue-coreuobject-deprecateduproperty
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/DeprecatedUProperty.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/FProperty]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/Asset-Lifecycle]]"
tags: [ue, runtime, foundation, coreuobject, migration, deprecated-uproperty, postload-migration]
---

# UE CoreUObject — DeprecatedUProperty sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/DeprecatedUProperty.md]]
> Parent: [[sources/ue-coreuobject-skill]]

본 sub-skill 은 **두 종류의 deprecation** 을 다룬다:

1. **UProperty → FProperty (UE 4.x → 5.x)** — Reflection 시스템 자체의 type 마이그레이션. 본 페이지 §1-§4.
2. **UPROPERTY 필드 자체의 `_DEPRECATED` 접미사 (UE 5.x 운영)** — 자산 데이터 호환 마이그레이션. 본 페이지 §5 + 페어 sub-skill [[sources/ue-coreuobject-serialization]] §5.2 / §5.7 cross-link.

## 1. Summary (Type 마이그레이션, UE 4 → 5)

UProperty (UE 4.25 이전) → [[entities/FProperty]] 마이그레이션 가이드. 옛 API 식별 + 변경 매핑 + 호환 코드.

## 2. Key claims

### 2.1 Type 마이그레이션 (UProperty → FProperty)

- UProperty 는 UObject 자손 였음 (4.x). FProperty 는 non-UObject struct (5.x).
- 매핑: `UProperty*` → `FProperty*`, `UObjectProperty*` → `FObjectProperty*`, etc.
- Cast 변경: `Cast<UObjectProperty>` → `CastField<FObjectProperty>`.
- TFieldIterator: `TFieldIterator<UProperty>` → `TFieldIterator<FProperty>`.
- 호환 코드 (4.x ↔ 5.x 동시): `using FProperty = UProperty;` (4.x) 의 typedef. 신규 코드는 5.x 만.
- 마이그레이션 도구: UE 가 자동 변환 — Editor 에서 UProperty 사용 시 deprecation warning.
- Editor 패널 / BP 노출 / Replication 등 표면 API 는 변화 없음 — 내부 cast 만 변경.

### 2.2 UPROPERTY 필드 deprecation (5.x 운영)

- **`_DEPRECATED` 접미사** — UPROPERTY 이름에 접미사 추가 시 `UStruct::SerializeTaggedProperties` brute force search 가 자동으로 옛 이름 ↔ `XXX_DEPRECATED` 매칭 (Engine `Class.cpp` L1690-L1760 권위, [[sources/ue-coreuobject-serialization]] §5.1).
- **`meta=(DeprecatedProperty, DeprecationMessage="...")`** — BP UI 에 deprecation warning 표시 (UHT 가 BP 그래프 노드에 warning 적용). 직렬화에는 영향 없음 — `_DEPRECATED` 접미사가 직렬화 호환 담당.
- **PostLoad 마이그레이션** — 옛 데이터를 신규 모델로 이전. 단일 필드 (§5.2) 또는 컨테이너 (§5.7) 패턴 ([[sources/ue-coreuobject-serialization]]).
- **Cycle cutoff 명문화** — 헤더 주석에 제거 시점 + `git grep "XXX_DEPRECATED"` → 0 hits 후 삭제.

## 3. Quotations

> "UProperty 는 deprecated. 신규 코드는 항상 FProperty 사용 — UProperty 는 호환 / 이해용으로만."

## 4. Open questions

- [ ] 5.x 잔여 UProperty API 카탈로그 (호환 목적)
- [ ] 자동 마이그레이션 도구의 한계
- [ ] `meta=(DeprecatedProperty)` 가 `_DEPRECATED` 접미사 없이 단독 사용 시 직렬화 호환성 (`DeprecationMessage` 만 표시되고 옛 이름 lookup X — 본 페이지 §5.4 결정 트리 참조)

## 5. ⭐ UPROPERTY 필드 deprecation (5.x 운영) — Cycle 5p+2 신규

> §1-§4 가 UProperty type 마이그레이션 (UE 4 → 5, *완료된 일회성 작업*) 을 다룬다면, §5 는 **5.x 운영 중 발생하는 자산 호환 deprecation** 을 다룬다. 본 sub-§은 [[sources/ue-coreuobject-serialization]] §5 의 entry point — 마이그레이션 본문은 serialization sub-skill 이 권위.

### 5.1 결정 트리 — 어떤 deprecation 도구를 쓸 것인가

| 시나리오 | 권장 도구 | 비고 |
| -- | -- | -- |
| UPROPERTY 이름 단순 변경 (의미 유지) | **`CoreRedirects` (BaseEngine.ini)** 또는 **`_DEPRECATED` 접미사** | CoreRedirects = .ini 외부 의존 / `_DEPRECATED` = 코드 안 self-documenting (권장) |
| UPROPERTY 필드 값 형태 변경 (예: FFrameNumber × 2 → USTRUCT 래퍼) | **`_DEPRECATED` 접미사 + PostLoad 3-step** ([[sources/ue-coreuobject-serialization]] §5.2) | 단일 필드 마이그레이션 |
| UPROPERTY 컨테이너 자체 deprecation (예: TArray<Track> → TArray<Binding<Tracks>>) | **`_DEPRECATED` 접미사 + PostLoad 4-step + UObject::Rename Outer 교체 3 flags** ([[sources/ue-coreuobject-serialization]] §5.7) | 컨테이너 마이그레이션 — 본 sub-skill `_DEPRECATED` 접미사 + serialization §5.7 의 4-step 패턴 결합 |
| BP 그래프 노드 deprecation (사용 노드에 warning 표시) | **`meta=(DeprecatedProperty, DeprecationMessage="...")`** | 단독 사용 시 직렬화 영향 X — `_DEPRECATED` 접미사와 조합 권장 |
| UCLASS / UFUNCTION 자체 deprecation | `meta=(DeprecatedFunction)` / UE_DEPRECATED 매크로 | UPROPERTY 범위 외 — 본 sub-skill 다루지 않음 |
| 베이스 UClass 교체 (예: AActor → APawn) | Class redirect + PostLoad 안 IsA 분기 후 신규 객체 생성 | 본 sub-skill 범위 외 |

### 5.2 표준 패턴 매트릭스 (단일 필드 + 컨테이너)

| 패턴 | 권위 | KMCProject 사례 |
| -- | -- | -- |
| **단일 필드 3-step** — DEPRECATED 접미사 + PostLoad idempotent + Cycle cutoff | [[sources/ue-coreuobject-serialization]] §5.2 + Engine `Class.cpp` L1690-L1760 brute force | Phase 2a `StartFrame_DEPRECATED + EndFrame_DEPRECATED → FMCComboFrameRange SectionRange` ([[synthesis/mc-combo-section-levelsequence-style-upgrade]] §5) |
| **컨테이너 4-step** — DEPRECATED 접미사 + PostLoad idempotent + placeholder 부모 생성 + UObject::Rename Outer 교체 3 flags + Empty + Dirty | [[sources/ue-coreuobject-serialization]] §5.7 + Engine `UObjectGlobals.h` L1090 Rename + `MovieScene.h` Possessables_DEPRECATED 미러 | **Phase 4c `Asset->Tracks_DEPRECATED → Bindings → Binding->Tracks` 5단계 계층 진입** ([[synthesis/mc-combo-editor-levelsequence-lite]] §5.7.9.3) |

### 5.3 `meta=(DeprecatedProperty)` vs `_DEPRECATED` 접미사 — 두 도구 조합

```cpp
UPROPERTY(meta = (DeprecatedProperty,
    DeprecationMessage = "Use NewField instead. Phase X 자동 마이그레이션 대상."))
TArray<TObjectPtr<UMyChild>> OldField_DEPRECATED;
```

이 패턴이 권장 — 두 도구 효과 합산:

| 도구 | 효과 |
| -- | -- |
| `_DEPRECATED` 접미사 (이름) | Engine `Class.cpp` L1690-L1760 brute force search — 자산 직렬화 호환 (옛 자산 로드 시 `OldField` 태그 → `OldField_DEPRECATED` 자동 매칭) |
| `meta=(DeprecatedProperty)` (메타) | BP 그래프 노드 deprecation warning + IDE / Editor `Details Panel` 안 deprecated 표시 |
| `DeprecationMessage="..."` (메타 인자) | BP / IDE warning 텍스트 customize — 마이그레이션 안내 |

⭐ **둘 중 하나만 사용 시 결과**:
- `_DEPRECATED` 접미사 단독 → 직렬화 호환 ✅ / BP 그래프 warning ❌
- `meta=(DeprecatedProperty)` 단독 → 직렬화 호환 ❌ (옛 자산 직렬화 시 데이터 손실) / BP 그래프 warning ✅

→ **본 페이지 권고: 자산 직렬화 호환 의무 시 `_DEPRECATED` 접미사 의무, BP UI 보강 위해 `meta=(DeprecatedProperty)` 추가 권장**.

### 5.4 함정 — `meta=(DeprecatedProperty)` 단독 사용 (직렬화 호환 X)

옛 코드:
```cpp
UPROPERTY(EditAnywhere)
TArray<TObjectPtr<UMyChild>> Children;
```

신규 코드 (잘못된 deprecation):
```cpp
UPROPERTY(meta = (DeprecatedProperty, DeprecationMessage = "Deprecated"))
TArray<TObjectPtr<UMyChild>> Children;  // 이름 변경 없음 → BP warning 만, 데이터 호환 X
```

→ **옛 자산 로드 시 `Children` 태그 → 동일 이름 UPROPERTY 가 여전히 존재 (이름 변경 X) → 정상 로드 + deprecated warning**. 마이그레이션 코드 (PostLoad) 가 없으면 옛 데이터를 신규 모델로 이전하는 단계 자체가 없다.

⚠ **이 패턴이 적절한 시점은 단 하나** — UPROPERTY 자체를 완전 제거할 예정이지만 cycle 안에서 사용자 / 디자이너가 점진 제거하도록 warning 표시할 때. 데이터 이전 의도가 있다면 `_DEPRECATED` 접미사 + PostLoad 필수.

### 5.5 ⭐ Case Study: KMCProject Phase 4c (Cycle 5p+2)

> **case study 페어**: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.7.9.3 (Phase 4c — Tracks → Bindings 컨테이너 마이그레이션) + [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §5 (Phase 2a — 단일 필드 마이그레이션).
>
> **vault scope 정책** ([[00_meta/08_VaultScopePolicy]]): 본 sub-§은 KMCProject (mc-) 실측 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강한 항목.

KMCProject 가 두 가지 deprecation 패턴을 모두 적용한 사례:

| 사례 | 패턴 | 코드 |
| -- | -- | -- |
| **Phase 2a 단일 필드** | §5.2 단일 필드 3-step | `UMCComboSection` 안 `StartFrame_DEPRECATED + EndFrame_DEPRECATED` (각각 `UPROPERTY()` 만) → `FMCComboFrameRange SectionRange` (USTRUCT 래퍼) |
| **Phase 4c 컨테이너** | §5.7 컨테이너 4-step + `meta=(DeprecatedProperty)` 조합 | `UMCComboAsset` 안 `UPROPERTY(meta = (DeprecatedProperty, DeprecationMessage = "Use Bindings → Binding->Tracks instead. Phase 4c 자동 마이그레이션 대상.")) TArray<TObjectPtr<UMCComboTrack>> Tracks_DEPRECATED;` + `PostLoad` 안 `Track->Rename(nullptr, LegacyBinding, REN_DontCreateRedirectors \| REN_NonTransactional \| REN_DoNotDirty)` 3 flags |

**Engine 권위 매트릭스 (Phase 4c verify, UE 5.7.4)**:
- `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h` L425 — `virtual void PostLoad()`
- `Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h` L1090 — `UObject::Rename + ERenameFlags`
- `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp` L1690-L1760 — `_DEPRECATED` 접미사 brute force
- `Engine/Source/Runtime/MovieScene/Public/MovieScene.h` — `FMovieScene::Possessables_DEPRECATED` 미러 패턴

**KMCProject Phase 4c 빌드 PASS 검증** (2026-05-18) — 본 §5.2 (단일 필드) + §5.3 (`_DEPRECATED` + `meta=(DeprecatedProperty)` 조합) 패턴 실측 verify.

## 6. Cross-link

### Engine 권위

- `Engine/Source/Runtime/CoreUObject/Public/UObject/Class.h` — FField + FProperty (5.x)
- `Engine/Source/Runtime/CoreUObject/Public/UObject/UnrealType.h` — FProperty 자손 (FObjectProperty / FStructProperty / FArrayProperty etc.)
- `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp` L1690-L1760 — `_DEPRECATED` 접미사 brute force (§5.1)
- `Engine/Source/Runtime/CoreUObject/Public/UObject/UObjectGlobals.h` L1090 — `UObject::Rename + ERenameFlags` (§5.2 컨테이너 마이그레이션)
- `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h` L425 — `virtual void PostLoad()`
- `Engine/Source/Runtime/MovieScene/Public/MovieScene.h` — `FMovieScene::Possessables_DEPRECATED` 미러

### Parent / 페어 sub-skills

- Parent: [[sources/ue-coreuobject-skill]]
- 페어 sub-skill (UPROPERTY 필드 deprecation 본문 권위): [[sources/ue-coreuobject-serialization]] §5.2 단일 필드 / §5.7 컨테이너
- 페어 sub-skill (FProperty type): [[sources/ue-coreuobject-property]] · [[sources/ue-coreuobject-reflection]]

### Concept

- [[concepts/Reflection-System]] · [[concepts/Asset-Lifecycle]] · [[concepts/UPROPERTY-Markup]]

### ⭐ Case study (mc-, Cycle 5p+2 §5.5)

- [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §5 — Phase 2a 단일 필드 마이그레이션 사례
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.7.9.3 — Phase 4c 컨테이너 마이그레이션 사례

### Governance (Cycle 5p+2)

- [[00_meta/08_VaultScopePolicy]] §3 — `mc-` 페이지 사례를 `ue-` 일반 페이지에 reverse-link 의무 (본 §5.5)
- [[00_meta/03_EvaluatorRecipe]] §1.5 — Stage 2.X Engine Authority Verification (본 §5.5 Engine 권위 매트릭스)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
