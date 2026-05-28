---
id: meta-evaluator-recipe
title: Evaluator Recipe — 8단계 평가 절차
version: 0.2.0
status: live
last_audit: 2026-05-17
language: ko
parent: ../CLAUDE-wiki-governance.md
---

# Evaluator Recipe — 8단계 평가 절차

Generator/Evaluator 분리 (Article 1) 의 운영 절차. 평가는 **반드시 새 세션** 에서 빈 컨텍스트로 시작.

## 0. 사전 조건

- 평가 대상 sub-skill 의 frontmatter 가 §1~§5 필수 필드를 모두 갖춤.
- 평가자 컨텍스트에는 (a) 거버넌스 + 메타 6개 파일, (b) 평가 대상 sub-skill 만 로드. 다른 sub-skill 본문은 cross-link 검증 시점에만 부분 로드.

## 1. 8단계

### Step 1 — Source Verification (출처 검증) [10분]

- frontmatter `karpathy_source` 의 URL/타임스탬프가 실제 존재하는가?
- 본문 인용 (`[Z2H#7 1:23:45]`) 이 영상 실제 내용과 일치하는가?
- **실패 처리**: 인용 1개 무효 = 출처 추적성 -3점.

### Step 2 — Code Verification (코드 검증) [15분]

- 코드 스니펫이 import / 차원 / 시드 모두 명시했는가?
- 가능하면 실제 실행 (Python REPL 또는 Colab) 으로 결과 재현.
- nanoGPT/micrograd 등 인용된 레포 라인 번호가 commit hash 기준 정확한가?
- **실패 처리**: 재현 불가 = 정확성 -10 (재초안 가능).

### Step 3 — Section Completeness (절 완전성) [5분]

- §4.1 의 8개 의무 절 모두 존재? (정의/출처/핵심개념/코드/라이프사이클/패턴/함정/관련)
- 각 절이 placeholder ("TBD") 가 아닌 실제 내용?
- **실패 처리**: 누락 1개당 완전성 -3점.

### Step 4 — Cross-link Audit [10분]

- `related` / `prerequisites` 의 상대 경로가 실제 파일을 가리키는가?
- 본문 안의 `[…](…/…)` 링크가 모두 유효한가?
- 같은 주제를 다른 sub-skill 에서 또 풀어쓰지 않는가? (SSoT)
- **실패 처리**: SSoT 위반 = 완전성 -5.

### Step 5 — Tone & Style (Karpathy 어조) [10분]

- 사족 (`참고로`, `사실은`, `한편`) 빈도 점검 (3개/1000자 초과 시 감점).
- 마케팅 톤 (`강력한`, `혁신적인`, `최고의`) 발견 시 즉시 감점.
- 한 단락 한 아이디어 원칙 준수?
- 코드 5줄당 1줄 주석 비율?
- **실패 처리**: 가독성 -2 ~ -5 / 회.

### Step 6 — Policy Compliance (정책 준수) [5분]

- Article 1 ~ Article 10 위반 점검.
- 특히 Article 6 (시간 견디기): "최신", "현존 최강" 같은 시간 의존 표현 0개.
- **실패 처리**: 위반 즉시 차원 감점 + frontmatter `status: draft` 강제.

### Step 7 — Quality Scoring (100점 채점) [10분]

- `00_QualityCriteria.md` 의 4개 차원 채점.
- 차원별 점수와 사유를 평가 보고서에 기록.
- **결과**: 총점 + 차원별 코멘트.

### Step 8 — Decision (결정) [5분]

| 총점     | 결정                             | 후속 조치                          |
| ------ | ------------------------------ | ----------------------------- |
| 90+    | live 승급                        | frontmatter `status: live` 변경 |
| 80–89  | live 승급 + 개선 메모                | 작성자에게 메모 전달                    |
| 65–79  | evaluated. 추가 보완 후 재평가         | `status: evaluated`           |
| < 65   | draft 강제                       | 핵심 차원의 재초안                     |

## 1.5 ⭐ UE 코드 평가 시 Stage 2.X — Engine Authority Verification (Cycle 5p 신규)

> Step 2 (Code Verification) 의 *UE C++ 코드 평가 시 확장*. 사용자가 evaluator 를 **수동 호출 시** 적용 (auto-evaluator 호출 제거 정책 — Cycle 5p, timeout 심각). UE 5.7.4 Engine 본가에서 직접 verify 의무.

### 1.5.1 의무 — 7 항목 (Generator §pre-write 와 페어)

specialist agent `.md` 의 §pre-write 1단계 와 동일한 7 항목을 evaluator 가 *재검증* (Generator/Evaluator 분리 — Article 1):

- **A. UPROPERTY 부착 타입** — templated container (TRange/TMap/TSet/TVariant/TOptional/TFunction) 직접 부착 사례 grep (권위: `MovieSceneSection.h L787-788` FMovieSceneFrameRange + `MovieSceneFrameMigration.h L26-104`)
- **B. TArray cross-type copy-init** — `Containers/Array.h L745-755` `explicit` ctor 검증
- **C. TObjectPtr 변환** — `.Get()` 명시 확인
- **D. bitfield UPROPERTY** — `MovieSceneSection.h L820, L824` + `BodyInstanceCore.h L38-59` 등 본가 사례 grep
- **E. DEPRECATED 마이그레이션** — `_DEPRECATED` 접미사 vs CoreRedirects 결정 (`Class.cpp L1690-1760`)
- **F. Custom Serialize trait** — `TStructOpsTypeTraits` (`MovieSceneFrameMigration.h L107-110`)
- **G. FCursorReply / EMouseCursor 시그니처** — `CursorReply.h L33` / `ICursor.h L17~`

### 1.5.2 보고 매트릭스 (의무)

평가 보고서에 다음 양식의 **§Engine Authority Verification 매트릭스** 명시:

| 항목 | Generator 작성 패턴 | Engine 본가 사용 사례 | verify 결과 |
| -- | -- | -- | -- |
| (예) UPROPERTY SectionRange | `TRange<FFrameNumber>` 직접 부착 | MovieSceneSection.h L788 — `FMovieSceneFrameRange` 래퍼 (0건 직접 부착) | **FAIL — USTRUCT 래퍼 의무** |
| (예) TArray copy-init | `TArray<A*> = TArray<TObjectPtr<A>>` copy-init | Array.h L749-755 — `explicit` ctor | **FAIL — direct-init 의무** |
| (예) bitfield uint8 :1 | `uint8 b... : 1` UPROPERTY 부착 | BodyInstanceCore.h L38-59 (4 사례) | PASS |

### 1.5.3 Self-correction 패턴

evaluator 가 Engine grep 수행 중 generator 의 권위 인용이 잘못된 라인 / 타입을 가리킬 경우:
1. 정정된 권위 인용을 보고서 §"Engine 권위 인용 정정" 에 명시
2. Generator 의 권위 인용 신뢰도 점수에 반영 (가독성 -5)

### 1.5.4 분담 (Article 1 Generator/Evaluator + Article 2 Orchestrator)

- **Generator (specialist)**: 작성 *전* 에 본 7 항목 Engine grep 수행 + 보고서에 verify 결과 첨부 의무 (specialist `.md` §pre-write 1단계 — Cycle 5p)
- **Evaluator (사용자 수동 호출)**: 작성 *후* 에 generator 의 verify 결과를 *재검증* + generator 누락 항목 catch
- **Orchestrator (메인)**: 사전 batch grep ([[00_meta/07_AgentBoundaryProtocol]] §Pre-Flight Engine Grep Batch — Cycle 5p)

→ 3중 verify 로 Compile blocker 영구 차단. KMCProject Phase 2 실측 (`outputs/cycle-5p-handoff/01_timing_analysis.md`): refactor 회피 시 ~605s (37%) 단축.

### 1.5.5 Phase 1 evaluator 적용 (handoff document)

handoff document (`synthesis/*` 또는 `mc-*`) 의 Phase 1 evaluator 도 본 §적용 의무 — [[00_meta/08_VaultScopePolicy]] §3.5 (Cycle 5p) 참조.

handoff document 의 §2 격상 매트릭스 / §5 BC 패턴에 작성된 모든 UPROPERTY 타입을 Engine grep 으로 verify. 사용 사례 0건 → **Critical 감점 30** (정확성 차원).

### 1.5.6 적용 정책

- ⚠ **사용자 수동 호출 전용** — Cycle 5p 정책 (evaluator 자동 호출 제거 — timeout 심각). 사용자가 명시적으로 `/evaluate` 또는 ue-evaluator 호출 시 본 §1.5 적용.
- ⚠ **UE 코드 평가 시만** — wiki sub-skill 본문 평가 (§1 Step 1~8) 와 *별도*. UE C++ 코드 작성물 평가 시 *추가* 적용.

## 2. 평가 보고서 양식

```markdown
# Evaluation Report — <sub-skill id>

- 평가일: YYYY-MM-DD
- 평가자: (별도 세션 ID 또는 사람)
- 대상 버전: <id>@<version>

## 점수

| 차원      | 점수    | 코멘트          |
| ------- | ----- | ------------ |
| 정확성     | xx/30 |              |
| 출처      | xx/20 |              |
| 완전성     | xx/25 |              |
| 가독성     | xx/25 |              |
| **총점**  | xx/100 |              |

## 8단계 결과

1. Source: PASS / FAIL — ...
2. Code:   ...
...

## 결정

- [ ] live
- [ ] evaluated (보완 권고)
- [ ] draft (재초안)

## 보완 권고

- 1.
- 2.
```

## 3. 평가자 자질

- Karpathy 영상 ≥ 1편 직접 시청 경험.
- PyTorch 코드 읽기 가능.
- 정책 우선순위 (`01_PolicyPriority.md`) 숙지.

## 4. 자가 평가 함정 (Article 1 위반 사례)

- 같은 대화에서 작성 + 채점 → 평가자 문맥에 작성 의도/약점이 미리 노출됨.
- "내가 잘 썼다고 생각해서 90점" → 객관 기준 ≠ 자기 만족.
- 작성 직후 "한 번 더 검토" 도 자가 평가다. 별도 세션이라야 의미 있다.

## 5. 변경 이력

| 날짜 | 버전 | 변경 |
| -- | -- | -- |
| 2026-05-09 | 0.1.0 | 최초 작성. 8단계 (Source / Code / Section / Cross-link / Tone / Policy / Score / Decision) + 평가 보고서 양식 + 평가자 자질 + 자가 평가 함정 (Article 1). |
| 2026-05-17 | 0.2.0 | **§1.5 신규 — UE 코드 평가 시 Stage 2.X — Engine Authority Verification** (Cycle 5p). KMCProject Phase 2 postmortem (`outputs/cycle-5p-handoff/`) 기반. 7 항목 (A~G) Engine 본가 grep 의무 + 보고 매트릭스 + Self-correction + 3중 verify 분담 (Generator §pre-write / Evaluator §Stage 2.X / Orchestrator §Pre-Flight). **사용자 수동 호출 전용 정책** 명시 (auto-evaluator 호출 제거 — timeout 심각). handoff document Phase 1 evaluator 도 [[00_meta/08_VaultScopePolicy]] §3.5 페어 적용. |
