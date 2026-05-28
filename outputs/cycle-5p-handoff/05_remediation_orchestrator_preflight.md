---
type: postmortem-remediation
title: "05 — Orchestrator pre-flight grep 의무 (07_AgentBoundaryProtocol 보강)"
slug: 05_remediation_orchestrator_preflight
created: 2026-05-17
priority: P2 (원인 #3 해소 — 메인 Claude 측 강화)
target_files:
  - "00_meta/07_AgentBoundaryProtocol.md"
  - "sources/ue-agent-orchestrator.md (카탈로그 sync)"
---

# 05 — Orchestrator pre-flight grep 의무

## 1. 문제

메인 Claude (오케스트레이터 역할) 가 specialist 호출 prompt 작성 시 다음 두 비효율 발생:

### 비효율 1 — Engine grep 결과 사전 첨부 안 함

- 본 사례에서 메인 Claude 가 Phase 2a / Phase 2c specialist 호출 시 handoff document 의 §2 매트릭스 그대로 인용
- Engine 본가 `MovieSceneSection.h` / `Array.h` grep 결과를 prompt 에 사전 첨부하지 않음
- specialist 가 Engine grep 부담을 짊어지지만 (§02_remediation_specialist_prompts.md 적용 시), 메인이 1회 batch 로 미리 했다면 모든 specialist 가 즉시 활용 가능

### 비효율 2 — Pre-flight grep batch 부재

- 메인 Claude 의 Phase 2 진입 전 단계 (Phase 2 pre-flight task #2) 가 단순히 "기존 MCCombo 파일 구조 파악" 만 수행
- Engine 본가의 핵심 패턴 grep (TRange UPROPERTY, TArray cross-type, FCursorReply 시그니처 등) 누락
- 4단계 (2a/2b/2c/2d) 모두 동일 Engine grep 을 specialist 가 개별 수행 → 시간 중복 (~4 × 10초)

---

## 2. 보강 명세

### 2.1 대상 파일

`00_meta/07_AgentBoundaryProtocol.md` 의 **§Phase II Orchestrator MCP 권한 점진** 또는 **§Main ↔ Specialist Boundary 5단계** 다음 위치에 **§Pre-Flight Engine Grep Batch 의무** 신규 추가.

### 2.2 추가 §내용

```markdown
## §Pre-Flight Engine Grep Batch 의무 (Cycle 5p 신규)

### 배경

Phase 2+ 의 multi-step specialist 호출 워크플로우 (예: KMCProject Phase 2a/2b/2c/2d) 시
메인 (오케스트레이터 역할) 이 specialist 호출 *전* 에 Engine 본가 grep 1회 batch 로
모든 specialist 가 동일 결과를 즉시 활용할 수 있도록 의무화.

### Pre-Flight Engine Grep 항목 (7가지)

handoff document (`synthesis/*` 또는 `mc-*`) 의 §2 격상 매트릭스 / §5 BC 패턴 / §7 specialist 분담에서 다음 항목 검출:

A. **UPROPERTY 부착 타입** — templated container 사용 여부 (TRange/TMap/TSet/TVariant/TOptional/TFunction)
B. **TArray cross-type copy-init** — `TArray<A*> = TArray<TObjectPtr<A>>` 패턴
C. **TObjectPtr 변환** — `.Get()` 명시 필요 위치
D. **bitfield UPROPERTY** — `uint8 b... : 1` 사용 여부
E. **DEPRECATED 마이그레이션** — `_DEPRECATED` 접미사 vs CoreRedirects
F. **Custom Serialize trait** — USTRUCT 래퍼 + `WithSerializer` 트레잇 필요 여부
G. **Slate API 시그니처** — FCursorReply / EMouseCursor / FSlateDrawElement 정확성

각 항목에 대해 Engine 본가 grep 1회 (~5~15초) → 결과를 후속 specialist 호출 prompt 에 사전 첨부.

### 적용 예시 (본 KMCProject Phase 2 사례 재구성)

```
Phase 2 pre-flight task (메인 Claude):
1. 기존 MCCombo 파일 구조 파악 (기존 — 유지)
2. Engine 본가 Pre-Flight Grep Batch (신규 — Cycle 5p 추가):
   a. grep "UPROPERTY()\s*\n\s*TRange<" Engine/Source/...
      → 0건 확인 → FMovieSceneFrameRange USTRUCT 래퍼 의무
   b. read Engine/Source/Runtime/MovieScene/Public/MovieSceneFrameMigration.h L26-110
      → FMovieSceneFrameRange 패턴 학습 → KMCProject FMCComboFrameRange 작성 의무
   c. grep "explicit TArray" Engine/Source/Runtime/Core/Public/Containers/Array.h
      → L752 explicit cross-type ctor 확인 → direct-init 의무
   d. grep "uint8 b\w+ : 1" Engine/Source/Runtime/...
      → MovieSceneSection.h L820/L824 + BodyInstanceCore.h L38-59 사례 4건
      → bitfield UPROPERTY 정식 지원 확인
   ...
3. 결과 batch document 작성 — 후속 4 specialist 호출 prompt 에 사전 첨부
```

### Pre-Flight Batch Document 양식

메인 Claude 가 specialist 호출 prompt 안에 다음 §명시:

```markdown
## Pre-Flight Engine Grep 결과 (사전 batch — 메인 수행)

| 항목 | Engine 본가 verify 결과 | 후속 작성 패턴 |
| -- | -- | -- |
| UPROPERTY SectionRange | MovieSceneSection.h L788 — FMovieSceneFrameRange USTRUCT 래퍼 (TRange<FFrameNumber> 직접 부착 0건) | FMCComboFrameRange USTRUCT 래퍼 의무 |
| TArray cross-type copy | Array.h L752 — explicit ctor | direct-init or manual .Get() loop 의무 |
| bitfield UPROPERTY | MovieSceneSection.h L820/L824 (uint32 :1) + BodyInstanceCore.h L38-59 (uint8 :1) | uint8 :1 + EditAnywhere + BlueprintReadOnly 정합 |
| FCursorReply 시그니처 | CursorReply.h L33 — `FCursorReply::Cursor(EMouseCursor::Type)` | OnCursorQuery 작성 시 권위 사용 |
```

### 책임 분리 (Article 1 패턴)

- **메인 Claude (오케스트레이터)**: Pre-Flight Engine Grep Batch 1회 수행 + 결과를 prompt 에 사전 첨부
- **Specialist**: §pre-write 1단계 Engine Grep Verification 수행 — 메인의 batch 결과를 *재검증* (sanity)
- **Evaluator**: §Stage 2.X Engine Authority Verification — generator 의 verify 결과를 *재검증* (Article 1 self-eval bias 회피)

→ 3중 verify 구조로 BLOCKER 영구 차단.

### 효과 검증

본 §적용 후 (보강 4건 모두 반영 가정) :
- 본 사례 같은 Phase 2 multi-step 워크플로우 시간 ~37% 단축 (예상)
- refactor 사이클 0회 → 사용자 대기 시간 감소
- evaluator catch 부담 분산 → tool_uses 감소

### 변경 이력

- Cycle 5p (2026-05-17) — KMCProject Phase 2 postmortem 기반 신규 §Pre-Flight Engine Grep Batch 추가.
```

---

## 3. ue-agent-orchestrator.md (카탈로그 sync)

vault 측 `sources/ue-agent-orchestrator.md` 도 동기 sync.

해당 페이지의 §10 (Article 2 Orchestrator-Workers + §5.4 Agent Boundary Protocol) 다음에 본 §Pre-Flight Engine Grep Batch cross-link.

---

## 4. 적용 후 검증

1. `00_meta/07_AgentBoundaryProtocol.md` patch 적용
2. `sources/ue-agent-orchestrator.md` 동기 sync
3. ue-evaluator 호출 평가
4. PASS 시 vault 적용
5. 다음 KMCProject 또는 다른 multi-step 워크플로우 시 자동 적용

---

## 5. 기대 효과

- 메인 (오케스트레이터 역할) 의 pre-flight 단계가 단순 파일 구조 파악 → Engine 본가 batch grep + 후속 specialist 활용 → 시간 절약
- Article 1 Generator/Evaluator + Article 2 Orchestrator-Workers 패턴의 통합 (3중 verify)

---

## 6. 변경 이력

- 2026-05-17 — 최초 작성.
