---
type: postmortem-remediation
title: "03 — Synthesis handoff document Phase 1 작성 정책 강화"
slug: 03_remediation_synthesis_policy
created: 2026-05-17
priority: P1 (원인 #2 직접 해소)
target_files:
  - "00_meta/08_VaultScopePolicy.md (§3.5 신규 추가)"
  - "또는 00_meta/05_HandoffProtocol.md (§4.X 신규 추가)"
---

# 03 — Synthesis handoff document Phase 1 작성 정책 강화

## 1. 문제

본 사례의 **synthesis `mc-combo-section-levelsequence-style-upgrade`** 는 Phase 1 evaluator 가 **89.10 / 100 PASS** 줬음에도 다음 두 항목의 Compile-level 오류가 있었다:

### 오류 1 — §2.1 P0 매트릭스의 `SectionRange` 타입

```markdown
| **P0** | `SectionRange` | `TRange<FFrameNumber>` | MovieSceneSection.h L787-788 | StartFrame/EndFrame 통합 |
```

- 권위 인용은 `MovieSceneSection.h L787-788` 맞음 (정확)
- 그러나 해당 라인의 **실제 타입은 `FMovieSceneFrameRange` (USTRUCT 래퍼)**, `TRange<FFrameNumber>` 가 아님
- synthesis 작성자가 `FMovieSceneFrameRange::Value` 의 내부 타입 (`TRange<FFrameNumber>`) 을 직접 사용할 수 있다고 가정 → 잘못된 명세

### 오류 2 — synthesis §5 PostLoad BC 패턴의 `TRange<FFrameNumber>` UPROPERTY 부착

```markdown
UPROPERTY(EditAnywhere, ..., Category = "Combo|Range")
TRange<FFrameNumber> SectionRange;
```

- 직접 UPROPERTY 부착 불가 (UHT reflection 미지원) → specialist 가 그대로 따라가서 BLOCKER 발생

---

## 2. 보강 명세

### 2.1 대상 파일

**옵션 A** (권장): `00_meta/08_VaultScopePolicy.md` 에 `§3.5 Handoff Document Compile-Level Verify 의무` 신규 추가.

**옵션 B**: `00_meta/05_HandoffProtocol.md` 에 신규 §추가.

본 보고서는 **옵션 A** 기준 작성. wiki manager 판단으로 위치 조정 가능.

### 2.2 추가 §내용 (00_meta/08_VaultScopePolicy.md)

```markdown
## §3.5 — Handoff Document Compile-Level Verify 의무 (Cycle 5p 신규)

### 배경

`mc-*` 또는 `synthesis/*` handoff document (특히 Phase 1 설계 + Phase 2 specialist 인계용)
의 §2 격상 매트릭스 / §5 BC 패턴 / §7 specialist 분담 등에 작성된 **UPROPERTY 타입 / 함수 시그니처 / 직렬화 트레잇** 이
Engine 본가에서 실제 사용 가능한지 verify 의무.

본 §은 `00_meta/03_EvaluatorRecipe` Stage 2 의 *handoff document* 특화 보강 (Phase 1 evaluator 가 적용).

### Compile-Level Verify 7 항목 (§02_remediation_specialist_prompts.md A~G 와 동일)

A. UPROPERTY 부착 타입 — templated container 직접 부착 가능성 verify
B. TArray cross-type copy-initialization — `explicit` ctor 검증
C. TObjectPtr 변환 — `.Get()` 명시 의무
D. bitfield UPROPERTY — Engine 본가 사용 사례 grep
E. DEPRECATED 마이그레이션 패턴 — CoreRedirects vs PostLoad 결정
F. Custom Serialize trait — `WithSerializer` + USTRUCT 래퍼 권위
G. FCursorReply / EMouseCursor 시그니처

### Phase 1 evaluator 의무 추가

`00_meta/03_EvaluatorRecipe` 의 Stage 2 (Compile) 평가 시:
1. handoff document 의 모든 UPROPERTY 타입 (§2 매트릭스 / §5 PostLoad 등) 을 Engine grep 으로 verify
2. 사용 사례 0건 또는 잘못된 타입 (USTRUCT 래퍼 미사용) → **Critical 감점 30** (Pass with notes 등급 강등 또는 Fail)
3. verify 결과를 evaluator 보고서 §"Compile-Level Engine Verify 매트릭스" 에 명시

### 명세 작성자 (wiki-maintainer / 사용자) 가 미리 할 수 있는 verify

handoff document 작성 단계에서 :
- 본 사례 같은 격상 매트릭스 작성 시 Engine 본가 grep 1회 batch (~30초)
- 각 UPROPERTY 행에 Engine 본가 사용 사례 라인 인용 의무 (예: `MovieSceneSection.h L788`)
- USTRUCT 래퍼 필요 시 명세에 명시 (specialist 가 따라 작성)

### 예시 — 본 사례 정정 후 §2.1 매트릭스

```markdown
| **P0** | `SectionRange` | `FMCComboFrameRange` (USTRUCT 래퍼) | MovieSceneSection.h L788 (FMovieSceneFrameRange 미러) + MovieSceneFrameMigration.h L26-104 | StartFrame/EndFrame 통합. UPROPERTY 부착을 위해 TRange<FFrameNumber> 직접 부착 불가 → FMovieSceneFrameRange 패턴 차용 의무. |
```

→ 위 정정으로 specialist 가 1차 시도부터 USTRUCT 래퍼 작성 → refactor 사이클 0회.

### 변경 이력

- Cycle 5p (2026-05-17) — KMCProject Phase 2 postmortem 보고서 기반 신규 §3.5 작성.
```

---

## 3. 적용 후 검증

1. `00_meta/08_VaultScopePolicy.md` patch 적용
2. ue-evaluator 호출 평가
3. PASS 시 vault 적용
4. mcwiki MCP 6 도구 batch (lint / find_cross_link_broken / ...)
5. 본 정책의 첫 적용 — `synthesis/mc-combo-section-levelsequence-style-upgrade` §2.1 / §5 정정 patch (별도 작업)

---

## 4. 기대 효과

- 신규 synthesis handoff document 작성 시 Engine 본가 verify 의무 → specialist 가 1차 시도부터 정답
- 본 사례 같은 "Phase 1 evaluator 89.10 통과 + Phase 2 BLOCKER" 비대칭 차단

---

## 5. 변경 이력

- 2026-05-17 — 최초 작성.
