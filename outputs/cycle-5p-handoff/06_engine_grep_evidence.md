---
type: postmortem-evidence
title: "06 — Engine 본가 grep 증거 (Wiki Manager patch 작성 시 인용 source)"
slug: 06_engine_grep_evidence
created: 2026-05-17
priority: P0 (모든 patch 의 권위 source)
---

# 06 — Engine 본가 grep 증거 매트릭스

> **목적**: 본 폴더의 patch 4건 (`02~05_*.md`) 작성 시 인용한 Engine 본가 라인의 정확한 검증 결과 + 권위 source. wiki manager 가 patch 적용 시 동일 인용 사용.

---

## 1. 권위 인용 7건 (Phase 2 작업 중 evaluator 가 verify 함)

| # | 주제 | Engine 파일 | 라인 | 검증 결과 |
| -- | -- | -- | -- | -- |
| 1 | `FMovieSceneFrameRange` USTRUCT 래퍼 | `Runtime/MovieScene/Public/MovieSceneFrameMigration.h` | L26-L104 | `TRange<FFrameNumber> Value` + custom Serialize + TStructOpsTypeTraits (WithSerializer + WithStructuredSerializeFromMismatchedTag + WithIdenticalViaEquality 등 5 트레잇) |
| 2 | UPROPERTY 부착 `FMovieSceneFrameRange` 사례 | `Runtime/MovieScene/Public/MovieSceneSection.h` | L787-L788 | `UPROPERTY(EditAnywhere, Category="Section") FMovieSceneFrameRange SectionRange;` — TRange 직접 부착 0건, 본 USTRUCT 래퍼 의무 |
| 3 | bitfield UPROPERTY 사례 | `Runtime/MovieScene/Public/MovieSceneSection.h` | L820, L824 | `uint32 bIsActive : 1` / `uint32 bIsLocked : 1` — `EditAnywhere, Category="Section"` 메타 |
| 4 | bitfield UPROPERTY 추가 사례 | `Runtime/PhysicsCore/Public/BodyInstanceCore.h` | L38-L59 | `UPROPERTY(EditAnywhere, BlueprintReadOnly, ...) uint8 b... : 1` 4건 — BlueprintReadOnly 메타와 호환 확인 |
| 5 | TArray cross-type explicit ctor | `Runtime/Core/Public/Containers/Array.h` | L745-L755 | `[[nodiscard]] UE_FORCEINLINE_HINT explicit TArray(const TArray<OtherElementType, OtherAllocator>& Other)` — copy-init 불가, direct-init 또는 manual loop 의무 |
| 6 | `Orient_Vertical` 그라데이션 의미 | `Runtime/SlateCore/Private/Rendering/ElementBatcher.cpp` | L1783-L1788 | `if( DrawElement.GradientType == Orient_Vertical ) { StartPt = TopLeft; EndPt = BotLeft; }` — "stop lines are vertical" = X 축 (left-to-right) 그라데이션 |
| 7 | AnimInstance Slot Name 권위 | `Runtime/Engine/Classes/Animation/AnimInstance.h` | L437, L442, L605, L1619 | `GetSlotMontageGlobalWeight(const FName& SlotNodeName)` / `GetSlotMontageLocalWeight(...)` / BP 노출 함수 / `FQueuedRootMotionBlend::SlotName` — SlotName 이 AnimInstance/Montage API 의 1급 식별자 |
| 8 | FCursorReply::Cursor 시그니처 | `Runtime/SlateCore/Public/Input/CursorReply.h` | L33 | `static FCursorReply Cursor(EMouseCursor::Type InCursor)` |
| 9 | EMouseCursor 타입 | `ApplicationCore/Public/GenericPlatform/ICursor.h` | L17-L60 | Default/ResizeLeftRight/CardinalCross/GrabHand/SlashedCircle 등 enum 값 |
| 10 | PostLoad 마이그레이션 PropertyTag matching | `Runtime/CoreUObject/Private/UObject/Class.cpp` | L1514, L1690-L1760, L1742 | `UStruct::SerializeTaggedProperties` + PropertyTag matching + brute force search — _DEPRECATED 접미사 자동 매칭 |
| 11 | StartTime_DEPRECATED 사례 | `Runtime/MovieScene/Public/MovieSceneSection.h` | L834-L848 | `UPROPERTY() float StartTime_DEPRECATED;` 등 — KMCProject StartFrame_DEPRECATED 패턴 차용 |

---

## 2. 추가 verify 권장 항목 (본 사례 외)

### TMap / TSet / TVariant UPROPERTY 부착

- 본 사례에서 TRange 만 verify 했으나 다른 templated container 도 동일 패턴 (USTRUCT 래퍼 의무) 가능성
- 향후 specialist 가 TMap<K,V> 또는 TSet<T> 또는 TVariant<...> 를 UPROPERTY 부착하려 할 때 동일 grep 의무

### TWeakObjectPtr / TSoftObjectPtr / TSoftClassPtr cross-type

- TArray<TWeakObjectPtr<T>> ↔ TArray<T*> 변환도 동일 explicit ctor 검증 필요
- Phase 2 본 사례는 TObjectPtr 만 발생 — 다른 smart ptr 도 동일 적용

### IDetailCustomization / IPropertyTypeCustomization 시그니처

- Phase 3+ Editor 작업 시 PropertyEditor 모듈의 시그니처 verify 의무
- 본 사례 외이지만 Cycle 5p 적용 후 다음 phase 에서 확인

---

## 3. Wiki Manager patch 작성 시 인용 의무

각 patch 의 권위 인용 시 본 §1 의 라인 정확 사용. 예시:

### `02_remediation_specialist_prompts.md` 의 §pre-write A (UPROPERTY 부착 타입)

```markdown
- 새 UPROPERTY 타입이 **templated container** (TRange<>, TMap<,>, TSet<>, ...) 인 경우:
  - Engine 본가에서 `UPROPERTY()\s*\n\s*TRange<` 패턴 grep
  - **본가 사용 사례 0건** (verify 결과 — `MovieSceneSection.h L787-L788` 은 `FMovieSceneFrameRange` USTRUCT 래퍼 사용) → 직접 부착 불가
  - USTRUCT 래퍼 의무 — 권위: `MovieSceneFrameMigration.h L26-L104` (FMovieSceneFrameRange 패턴)
```

### `04_remediation_evaluator_stage2.md` 의 §Stage 2.X B (TArray cross-type)

```markdown
- TArray cross-type copy-init 검증:
  - Engine `Containers/Array.h L745-L755` 의 cross-type ctor 가 `explicit` 선언
  - 따라서 `TArray<A*> X = arr` (arr 이 `TArray<TObjectPtr<A>>`) copy-init 불가
  - direct-init `TArray<A*> X(arr);` 또는 manual `.Get()` loop 의무
```

---

## 4. Cycle 5p 적용 후 검증 (mcwiki MCP 도구)

본 폴더의 patch 4건 적용 후 다음 검증 batch:

1. `find_claim_conflict` — 본 patch 의 Engine 권위 인용이 vault 다른 페이지의 인용과 충돌 없는지
2. `find_stale_baseline` — Engine 본가 인용 라인이 stale (Engine 업그레이드 후 변경) 가능성 확인
3. `lint` — patch 적용 후 vault 전체 lint 0 issues
4. `find_cross_link_broken` — patch 가 추가한 cross-link 정합성
5. `suggest_missing_cross_link` — 본 §6 의 11 권위 인용을 sources 페이지에 reverse-link 추천 후보

---

## 5. 변경 이력

- 2026-05-17 — 최초 작성. Phase 2 작업 중 evaluator 가 verify 한 11 Engine 권위 인용 정리.
