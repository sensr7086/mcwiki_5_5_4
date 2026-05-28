---
type: postmortem-remediation
title: "04 — Evaluator Stage 2 Compile 강화 (Engine 본가 grep 의무)"
slug: 04_remediation_evaluator_stage2
created: 2026-05-17
priority: P0 (원인 #2/#4 직접 해소 — Phase 1/2 evaluator 양쪽 강화)
target_files:
  - "00_meta/03_EvaluatorRecipe.md"
  - "sources/ue-agent-evaluator.md (카탈로그 sync)"
---

# 04 — Evaluator Stage 2 Compile 강화

## 1. 문제

`00_meta/03_EvaluatorRecipe` 의 Stage 2 (Compile) 가 현재 다음 항목을 포함:

- UCLASS / UPROPERTY meta 정합성
- Build.cs 의존성 확인
- WITH_EDITOR 가드

그러나 **Engine 본가의 실제 UPROPERTY 부착 사례 grep 으로 verify** 의무는 명시되지 않음.

본 사례에서:
- Phase 2a evaluator (180초) 가 Engine `MovieSceneSection.h L787-788` 직접 verify 후 `FMovieSceneFrameRange` USTRUCT 래퍼 발견 → Critical 감점
- Phase 2c evaluator (193초) 가 Engine `Array.h L749-755` `explicit` ctor 발견 → Critical 감점

→ evaluator 가 (specialist 가 미리 해야 할) Engine grep 을 사후에 수행하는 비대칭 구조.

---

## 2. 보강 명세

### 2.1 대상 파일

`00_meta/03_EvaluatorRecipe.md` 의 Stage 2 (Compile) 섹션에 **§Stage 2.X — Engine Authority Verification** 신규 추가.

### 2.2 추가 §내용

```markdown
## Stage 2.X — Engine Authority Verification (Cycle 5p 신규)

### 의무

Stage 2 Compile 평가 시 evaluator 는 다음 7항목 (specialist `.md` §pre-write 와 동일) 을 Engine 본가에서 직접 verify:

A. UPROPERTY 부착 타입 — templated container (TRange/TMap/TSet/TVariant/TOptional/TFunction) 직접 부착 사례 grep
B. TArray cross-type copy-init — `Containers/Array.h L745-760` `explicit` ctor 검증
C. TObjectPtr 변환 — `.Get()` 명시 확인
D. bitfield UPROPERTY — `MovieSceneSection.h L820/L824` 등 본가 사례 grep
E. DEPRECATED 마이그레이션 — `_DEPRECATED` 접미사 vs CoreRedirects 결정
F. Custom Serialize trait — `TStructOpsTypeTraits` 사용 케이스 grep
G. FCursorReply / EMouseCursor 시그니처 — `CursorReply.h L33` / `ICursor.h L17~` verify

### 보고 매트릭스 (의무)

평가 보고서에 다음 양식의 **§Engine Authority Verification 매트릭스** 명시:

| 항목 | Generator 작성 패턴 | Engine 본가 사용 사례 | verify 결과 |
| -- | -- | -- | -- |
| (예) UPROPERTY SectionRange | `TRange<FFrameNumber>` 직접 부착 | MovieSceneSection.h L788 — `FMovieSceneFrameRange` 래퍼 사용 (0건 직접 부착) | **FAIL — USTRUCT 래퍼 의무** |
| (예) TArray copy-init | `TArray<A*> = TArray<TObjectPtr<A>>` copy-init | Array.h L749-755 — `explicit` ctor | **FAIL — direct-init 의무** |
| (예) bitfield uint8 :1 | `uint8 b... : 1` UPROPERTY 부착 | BodyInstanceCore.h L38-59 (4 사례) | PASS |

### Self-correction 패턴

evaluator 가 Engine grep 수행 중 generator 의 권위 인용이 잘못된 라인 / 타입을 가리킬 경우:
1. 정정된 권위 인용을 보고서 §"Engine 권위 인용 정정" 에 명시
2. Generator 의 권위 인용 신뢰도 점수에 반영 (Maintainability 감점)

### specialist `.md` §pre-write 와의 분담

- **Generator (specialist)**: 작성 *전* 에 본 7 항목 Engine grep 수행 + 보고서에 verify 결과 첨부 의무
- **Evaluator**: 작성 *후* 에 generator 의 verify 결과를 *재검증* + generator 누락 항목 catch
- 양쪽 모두 의무 → Generator 의 verify 누락은 evaluator 가 catch (sanity 보장)

### Phase 1 evaluator 적용

handoff document (`synthesis/*` 또는 `mc-*`) 의 Phase 1 evaluator (예: `mc-combo-section-levelsequence-style-upgrade` 의 evaluator 89.10) 도 본 §적용 의무.
즉 handoff document 의 §2 격상 매트릭스 / §5 BC 패턴에 작성된 모든 UPROPERTY 타입을 Engine grep 으로 verify.

→ 본 사례 같은 "Phase 1 evaluator 89.10 통과 + Phase 2 BLOCKER" 비대칭 영구 차단.

### 변경 이력

- Cycle 5p (2026-05-17) — KMCProject Phase 2 postmortem 기반 신규 §Stage 2.X 추가.
```

---

## 3. ue-agent-evaluator.md (카탈로그 sync)

vault 측 `sources/ue-agent-evaluator.md` 도 동기 sync — `00_meta/05_HandoffProtocol` 의 "Agent prompt ↔ vault catalog sync" 의무.

해당 페이지의 §7 Self-correction 또는 §3 Stage 2 절에 본 §Stage 2.X 신규 cross-link.

---

## 4. 적용 후 검증

1. `00_meta/03_EvaluatorRecipe.md` patch 적용
2. `sources/ue-agent-evaluator.md` 동기 sync
3. ue-evaluator 호출 평가 (self-eval bias 회피 — Generator/Evaluator 분리)
4. PASS 시 vault 적용
5. 다음 evaluator 호출부터 자동 적용

---

## 5. 본 정책의 첫 적용 — Phase 1 evaluator 재평가 후보

본 §Stage 2.X 적용 후 다음 synthesis 페이지의 Phase 1 evaluator 결과 재평가 권장:

1. `synthesis/mc-combo-section-levelsequence-style-upgrade` (89.10 → ?) — §2.1 TRange 오류 catch 시 등급 강등 가능성
2. (다른 KMCProject 또는 mc- synthesis 페이지가 있으면) 동일 적용

---

## 6. 기대 효과

- Phase 1 evaluator 도 Compile-level verify 의무화 → handoff document 단계에서 차단
- Phase 2+ specialist evaluator 의 Engine grep 부담 분산 — generator 가 사전 verify, evaluator 가 검증
- **본 사례 같은 BLOCKER 영구 차단**

---

## 7. 변경 이력

- 2026-05-17 — 최초 작성.
