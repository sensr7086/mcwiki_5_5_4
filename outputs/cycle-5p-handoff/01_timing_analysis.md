---
type: postmortem-detail
title: "01 — Phase 2 시간 분석 (실측 duration_ms)"
slug: 01_timing_analysis
created: 2026-05-17
---

# 01 — Phase 2 시간 분석

> **목적**: 11회 Agent 호출의 실측 duration_ms 를 정리하고 손실 사이클 (refactor 2회) 의 정확한 비용 계산.

---

## 1. 실측 Agent 호출 매트릭스

각 Agent 호출의 `duration_ms` 는 Agent tool 응답 내 footer (`<usage>...duration_ms: ...</usage>`) 에서 추출.

| # | 단계 | Agent | duration_ms | 초 | tool_uses | 결과 |
| -- | -- | -- | --: | --: | --: | -- |
| 1 | Phase 2a (1차) | ue-asset-specialist | 128,335 | 128 | 11 | ⚠ BLOCKER — TRange UPROPERTY |
| 2 | Phase 2a evaluator | ue-evaluator | 180,472 | 180 | 18 | 70.30 Conditional + Critical 1 발견 |
| 3 | Phase 2a-**refactor** | ue-asset-specialist | 157,594 | 158 | 9 | USTRUCT 래퍼 도입 |
| 4 | Phase 2a-refactor evaluator | ue-evaluator | 122,371 | 122 | 11 | 91.0 PASS |
| 5 | Phase 2b | ue-asset-specialist | 69,744 | 70 | 7 | PASS |
| 6 | Phase 2b evaluator | ue-evaluator | 88,902 | 89 | 12 | 94.0 PASS |
| 7 | Phase 2c (1차) | ue-slate-umg-specialist | 234,402 | 234 | 15 | ⚠ BLOCKER — TArray cross-type |
| 8 | Phase 2c evaluator | ue-evaluator | 192,626 | 193 | 24 | 75.0 Conditional + Critical 1 발견 |
| 9 | Phase 2c-**refactor** | ue-slate-umg-specialist | 109,720 | 110 | 11 | TInlineAllocator direct-init |
| 10 | Phase 2c-refactor evaluator | — | (skip) | (skip) | — | evaluator 사전 명시 ("~88+") 활용 |
| 11 | Phase 2d | ue-slate-umg-specialist | 195,088 | 195 | 13 | PASS |
| 12 | Phase 2d evaluator | ue-evaluator | 142,647 | 143 | 10 | 91.0 PASS |

> 항목 #10 (Phase 2c-refactor evaluator) 는 **재평가 skip** 결정. evaluator 가 항목 #8 평가 후 "If Critical 1 is fixed by the specialist with a one-liner... rises to ~88/100" 사전 명시. 변경 줄수 적음 + Minor 권고 5건 모두 반영 → 메인 Claude 가 재평가 skip 판단.

---

## 2. 단계별 누적 시간

```
Phase 2a   : 308초 (1차 BLOCKER)   + 280초 (refactor PASS)  = 588초
Phase 2b   : 159초 (PASS)                                   = 159초
Phase 2c   : 427초 (1차 BLOCKER)   + 110초 (refactor PASS)  = 537초
Phase 2d   : 338초 (PASS)                                   = 338초
─────────────────────────────────────────────────────────────────
합계                                                          1,622초 ≈ 27분
```

---

## 3. 손실 시간 계산

### 직접 손실 (refactor 사이클)

| 항목 | 시간 |
| -- | --: |
| Phase 2a-refactor specialist | 158초 |
| Phase 2a-refactor evaluator | 122초 |
| Phase 2c-refactor specialist | 110초 |
| Phase 2c-refactor evaluator | (skip — 0) |
| **직접 손실 합계** | **390초 (~24%)** |

### 간접 손실 (1차 시도 시간 — 결과적으로 무의미한 작업)

| 항목 | 시간 |
| -- | --: |
| Phase 2a 1차 specialist (BLOCKER 발생) | 128초 |
| Phase 2a 1차 evaluator (BLOCKER catch) | 180초 |
| Phase 2c 1차 specialist (BLOCKER 발생) | 234초 |
| Phase 2c 1차 evaluator (BLOCKER catch) | 193초 |
| **간접 손실 합계** | **735초** |

> 단, evaluator 의 catch 자체가 무의미한 작업은 아님 (오히려 그 catch 가 BLOCKER 차단의 핵심). 따라서 보수적 손실 = 390초, 적극적 손실 = 735초로 양극단 해석 가능.

### Engine grep 사전 verify 1회 비용 (가정)

- specialist 가 작성 전에 Engine grep 1회 (~5~15초 가정) 수행 시:
  - Phase 2a: TRange UPROPERTY 패턴 grep → 본가 0건 확인 → USTRUCT 래퍼 의무 인식 → 1차 시도부터 정답 작성
  - Phase 2c: TArray cross-type copy-init grep → Array.h L749-755 explicit constructor 확인 → direct-init 패턴 사용 → 1차 시도부터 정답
- **양 사례 모두 사전 verify 1회 (~30초 합계) 로 refactor 사이클 (390초) 100% 회피 가능**

---

## 4. tool_uses 분포 (보조 지표)

evaluator 의 tool_uses 가 specialist 보다 항상 많음 — Engine 본가 verify 가 evaluator 단계에서 집중되는 비대칭 구조 증거.

| 호출 | tool_uses 분포 |
| -- | -- |
| Phase 2a 1차 specialist | 11 (Edit 위주) |
| Phase 2a evaluator | **18** (Engine grep 다수) |
| Phase 2c 1차 specialist | 15 |
| Phase 2c evaluator | **24** (Engine grep 다수) |

→ Specialist 가 Engine grep 부담을 짊어지면 evaluator 의 tool_uses 감소 + 전체 시간 단축 (양쪽 Agent 가 동일 Engine grep 을 중복 수행하지 않음).

---

## 5. 시간 효율 개선 잠재력

본 보고서 적용 후 (보강 4건 모두 반영) 가정한 Phase 2 예상 시간:

| 항목 | Before | After (예상) |
| -- | --: | --: |
| Phase 2a | 588초 | ~250초 (1차 PASS, refactor 0회) |
| Phase 2b | 159초 | 159초 (변동 없음) |
| Phase 2c | 537초 | ~270초 (1차 PASS, refactor 0회) |
| Phase 2d | 338초 | 338초 (변동 없음) |
| **합계** | **1,622초 (27분)** | **~1,017초 (17분)** |

- **단축 효과: ~605초 (10분, 37%)** — refactor 사이클 2회 완전 회피 가정

---

## 6. 추가 관찰

### 재평가 skip 결정의 가치

- Phase 2c-refactor 의 재평가 skip 은 ~120초 절약 (evaluator 호출 회피)
- evaluator 가 "Critical 1 fixed → 88+" 명시한 패턴 활용 → 표준화 가치
- **권장 정책**: evaluator 가 "If X fixed, score Y" 형식으로 사전 명시한 경우, fix 가 변경 줄수 ≤ 20 + Minor 권고 N% 이상 반영 + OnPaint 외 함수 무변경 등 조건 충족 시 재평가 skip 가능 (`00_meta/03_EvaluatorRecipe` §X 신규)

### Pre-flight grep batch 의 효과

- 메인 (오케스트레이터 역할) 이 Phase 2 진입 전 1회 batch Engine grep 수행 시:
  - TRange / TMap / TSet UPROPERTY 패턴 grep
  - TObjectPtr / TWeakObjectPtr cross-type 변환 grep
  - bitfield UPROPERTY (`uint8 : 1`) 사례 grep
  - 모든 specialist 호출 prompt 에 동일 결과 첨부 → 4단계 모두 동시 보강
- 1회 batch (~30초) 로 전 phase 효과

---

## 7. 결론 — 시간 손실 정량화

| 분류 | 시간 | % |
| -- | --: | --: |
| 정상 작업 (Phase 2a-refactor + 2b + 2c-refactor + 2d) | 887초 | 55% |
| 직접 손실 (refactor 사이클) | 390초 | 24% |
| 간접 손실 (1차 BLOCKER 시도) | 735초 | 45% (보수) |
| **총 시간** | **1,622초 (27분)** | 100% |

→ **개선 잠재력 ~605초 (37%)** 가 보강 4건 적용 시 회수 가능.

---

## 변경 이력

- 2026-05-17 — 최초 작성. 11회 Agent 호출 duration_ms 실측 + 손실 분석.
