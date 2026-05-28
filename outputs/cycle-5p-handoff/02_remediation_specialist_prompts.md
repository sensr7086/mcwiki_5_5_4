---
type: postmortem-remediation
title: "02 — Specialist Agent Prompt 보강 (§pre-write Engine Grep 의무)"
slug: 02_remediation_specialist_prompts
created: 2026-05-17
priority: P0 (가장 큰 효과 — 원인 #1 직접 해소)
target_files:
  - "11 plugin specialist agent .md (agents/ue-asset-specialist.md, ue-components-specialist.md, ue-slate-umg-specialist.md, ue-animation-specialist.md, ue-gameframework-specialist.md, ue-input-specialist.md, ue-render-specialist.md, ue-plugin-specialist.md, ue-spatial-partition-specialist.md, ue-levelsequence-specialist.md, ue-editor-specialist.md)"
  - "vault 측 카탈로그 — sources/ue-agent-*.md 11종 동기 sync"
---

# 02 — Specialist Agent Prompt 보강

## 1. 문제

Specialist agent (Phase 2a: `ue-asset-specialist`, Phase 2c: `ue-slate-umg-specialist`) 가 작성 전에 Engine 본가 패턴을 verify 하지 않고 handoff document 의 명세를 액면가로 따랐다.

### 사례 1 — Phase 2a (TRange UPROPERTY)

```cpp
// ue-asset-specialist 1차 작성 (LINE 40, MCComboSection.h)
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Range")
TRange<FFrameNumber> SectionRange;  // ⚠ UHT reflection 불가 → 빌드 실패
```

- Engine 본가 (`MovieSceneSection.h L787-788`) 는 `FMovieSceneFrameRange` USTRUCT 래퍼 사용
- specialist 가 `MovieSceneSection.h` 그렙 1회 (~5초) 만 했어도 차단 가능
- evaluator 가 사후에 catch → refactor 사이클 발생

### 사례 2 — Phase 2c (TArray cross-type)

```cpp
// ue-slate-umg-specialist 1차 작성 (LINE 211, SMCComboTrackPanel.cpp)
TArray<UMCComboSection*> SortedSections = Track->Sections;  // ⚠ TArray<TObjectPtr<...>> → TArray<raw*> copy-init 불가 (Array.h L752 explicit ctor)
```

- Engine `Array.h L749-755` cross-type constructor 가 `explicit` 선언
- specialist 가 `Containers/Array.h` 그렙 1회 만 했어도 차단 가능

---

## 2. 보강 명세

### 2.1 대상 파일

11 plugin specialist agent `.md` (메인 prompt definition):
1. `ue-asset-specialist.md`
2. `ue-components-specialist.md`
3. `ue-slate-umg-specialist.md`
4. `ue-animation-specialist.md`
5. `ue-gameframework-specialist.md`
6. `ue-input-specialist.md`
7. `ue-render-specialist.md`
8. `ue-plugin-specialist.md`
9. `ue-spatial-partition-specialist.md`
10. `ue-levelsequence-specialist.md`
11. `ue-editor-specialist.md`

각 에이전트의 `.md` 안에 **§pre-write 1단계 — Engine Compile Blocker Verification** 신규 추가.

### 2.2 추가 §내용 (전 specialist 공통 template)

```markdown
## §pre-write 1단계 — Engine Compile Blocker Verification (의무)

코드 작성 *전* 에 다음 7가지 Compile blocker 후보를 Engine 본가에서 직접 verify.
각 항목은 grep 1회 (5~15초) 비용 — refactor 사이클 (수십 초 ~ 수백 초) 차단.

### A. UPROPERTY 부착 타입 검증

- 새 UPROPERTY 타입이 **templated container** (TRange<>, TMap<,>, TSet<>, TVariant<>, TOptional<>, TFunction<>) 인 경우:
  - Engine 본가에서 `UPROPERTY()\s*\n\s*TRange<` (또는 해당 타입) 패턴 grep
  - **본가 사용 사례 0건** → 직접 부착 불가 (UHT 미지원) → USTRUCT 래퍼 의무
  - 본가에 USTRUCT 래퍼 (예: `FMovieSceneFrameRange`, `FAssetData`) 존재 시 패턴 차용

### B. TArray cross-type copy-initialization 검증

- `TArray<A*> X = arr;` (arr 이 `TArray<TObjectPtr<A>>` 또는 다른 allocator 타입) 패턴 작성 시:
  - Engine `Containers/Array.h` L745-760 의 cross-type ctor 확인
  - `explicit` 선언 → copy-init 불가, direct-init 또는 manual `.Get()` loop 의무

### C. TObjectPtr 변환 검증

- `TObjectPtr<T> → T*` 변환은 명시적 `.Get()` 필요 (UE 5.x AutoSensingTObjectPtr 비활성 시)
- `auto P = TObjPtrVar;` 패턴은 TObjectPtr 보존 — raw 가 필요하면 `.Get()` 명시

### D. bitfield UPROPERTY 검증

- `uint8 b... : 1` UPROPERTY 부착 시:
  - Engine `MovieSceneSection.h L820/L824`, `BodyInstanceCore.h L38-59`, `UMG/Widget.h L387-388`, `Foliage/FoliageType.h L357` 등 본가 사례 확인
  - `BlueprintReadOnly` 메타와 호환됨 (UHT 정식 지원) — 본 사례들로 보강

### E. DEPRECATED UPROPERTY 마이그레이션 패턴

- 새 UPROPERTY 이름 변경 또는 자손→베이스 이동 시:
  - `_DEPRECATED` 접미사 (CoreRedirects 불필요 — `CoreUObject/Private/UObject/Class.cpp L1514 / L1690-1760` brute force search)
  - PostLoad idempotency 보장 (DEPRECATED 필드 0 리셋)
  - cutoff 시점 명문화 (Cycle 종료 등)

### F. Custom Serialize trait

- 새 USTRUCT 래퍼가 raw 멤버 (UPROPERTY 비부착) 를 가질 때:
  - `bool Serialize(FArchive&)` 함수 + `TStructOpsTypeTraits<...> { WithSerializer = true }` 트레잇 의무
  - Engine `FMovieSceneFrameRange` (`MovieSceneFrameMigration.h L107-110`) 패턴 차용

### G. FCursorReply / EMouseCursor signature

- OnCursorQuery 작성 시 `FCursorReply::Cursor(EMouseCursor::Type)` 시그니처 — Engine `SlateCore/Public/Input/CursorReply.h L33` 권위
- EMouseCursor enum 값 — `ApplicationCore/Public/GenericPlatform/ICursor.h L17~` 권위

---

### §pre-write 1단계 의무 보고

코드 작성 직후 보고서에 **"§pre-write Engine grep verify 결과"** 매트릭스 명시:

| 항목 | Engine 본가 파일:라인 | 사용 사례 N건 | 본 작성 패턴 일치 |
| -- | -- | -- | -- |
| (예) UPROPERTY FMovieSceneFrameRange | MovieSceneSection.h L788 | 1 | OK |
| (예) bitfield uint8 :1 | BodyInstanceCore.h L38-59 | 4 | OK |
| ... | ... | ... | ... |

해당 매트릭스가 보고서에 없는 경우 → evaluator 가 자동 Major 감점 (`00_meta/03_EvaluatorRecipe` §X 신설).
```

---

## 3. Patch 적용 위치 매트릭스

각 plugin specialist agent `.md` 의 **frontmatter 뒤 § Required reading** 다음 위치에 §pre-write 1단계 신규 추가.

예시 (ue-asset-specialist.md):

```markdown
---
frontmatter
---

# UE Asset Specialist

## Required reading
- [[sources/ue-coreuobject-uobject]]
...

## §pre-write 1단계 — Engine Compile Blocker Verification (의무)   ← 신규 추가
[위 §내용 그대로]

## Working principles
...

## Verification obligations
...
```

vault 측 카탈로그 (`sources/ue-agent-asset.md` 등 11종) 도 동기 sync — `00_meta/05_HandoffProtocol` 의 "Agent prompt ↔ vault catalog sync" 규정.

---

## 4. 검증

각 patch 적용 후:

1. 해당 specialist agent 호출 prompt 에 §pre-write 의무 자동 노출 확인
2. ue-evaluator 호출하여 patch 평가 (Generator/Evaluator 분리)
3. evaluator PASS (≥80) 시 vault 적용

---

## 5. 기대 효과

- **본 사례 (Phase 2a TRange / Phase 2c TArray cross-type)** 같은 BLOCKER 100% 차단
- refactor 사이클 0회 → Phase 시간 ~37% 단축
- evaluator 의 catch 부담 감소 (Engine grep 부분이 generator 로 이전)
- Article 1 Generator/Evaluator 분리 패턴의 "사전 검증 가능 항목" 비대칭 비용 해소

---

## 6. 변경 이력

- 2026-05-17 — 최초 작성. 11 specialist agent `.md` 갱신 patch 명세.
