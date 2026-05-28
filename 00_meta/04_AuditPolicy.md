---
id: meta-audit-policy
title: Audit Policy — 분기별 staleness 감사
version: 0.1.0
status: live
last_audit: 2026-05-09
audit_cadence: quarterly
language: ko
parent: ../CLAUDE-wiki-governance.md
---

# Audit Policy — 분기별 staleness 감사

위키가 시간을 견디기 위한 운영 절차. Karpathy 콘텐츠 자체는 비교적 안정적이지만, 인용 모델 (GPT-4 → o1 → R1) 과 코드베이스 (nanoGPT, llm.c) 는 빠르게 진화한다.

## 1. 감사 트리거

| 트리거                                     | 빈도/조건                  | 범위                         |
| --------------------------------------- | ---------------------- | -------------------------- |
| 분기별 정기                                   | 매 분기 첫 주               | 모든 `live` sub-skill         |
| Karpathy 신작 영상 (≥30분)                    | 즉시                     | 관련 카테고리                     |
| 인용 코드 메이저 버전 갱신                          | 1주 내                   | 해당 코드 인용 sub-skill          |
| 인용 모델 후속 발표 (GPT-x, Llama-x, DeepSeek 등) | 1개월 내                  | `60/70/80` 카테고리 + Glossary |
| 본문 모순 신고                                 | 즉시                     | 신고된 단일 sub-skill            |

## 2. 8단계 감사 절차

ue-wiki-llm `18_ModelEvolutionAudit` 의 응용:

### Step 1 — Inventory

- `live` sub-skill 목록 + 각 frontmatter 의 `last_audit` 추출.
- `last_audit` 6개월 초과 = 자동 `stale` 후보.

### Step 2 — Source Validation

- frontmatter `karpathy_source.url` HTTP 200 확인.
- 영상 제목/길이 변경 없는지 (재업로드/삭제 점검).
- GitHub 인용은 commit hash 가 여전히 유효한지.

### Step 3 — Load-Bearing Test

- 본문에서 "이 sub-skill 이 없으면 무엇이 망가지나" 자문.
- 다른 sub-skill 의 핵심 prerequisite 인가?
- 단순 보충 자료에 가까우면 `Simplify` 또는 `Merge` 후보.

### Step 4 — Cross-Reference

- `related` / `prerequisites` 가 가리키는 sub-skill 의 `status` 확인.
- 가리키는 대상이 `deprecated` 면 본 sub-skill 도 영향 확인.

### Step 5 — Real-World Check

- Karpathy 가 최근 1년 내 X/블로그/영상에서 해당 주제에 대한 update 발언이 있었는가?
- 인용 모델/코드의 현재 상태가 본문과 충돌하지 않는가?
- 예: GPT-4 인용 → 현재 GPT-5 가 출시됐다면 본문 수정 필요할 수 있음.

### Step 6 — Decision (6종)

| 결정         | 조건                                                | 후속                                  |
| ---------- | ------------------------------------------------- | ----------------------------------- |
| Continue   | 모든 검증 통과. 본문 변경 불필요.                              | `last_audit` 만 갱신.                  |
| Update     | 일부 사실 변경. 본문 일부 수정.                               | 수정 후 재평가 (`03_EvaluatorRecipe`).    |
| Simplify   | 본문이 비대해졌거나 중복 발생.                                 | 분량 축소, 일부를 다른 sub-skill 로 분할.       |
| Merge      | 다른 sub-skill 과 사실상 동일 주제.                         | 본 sub-skill 본문을 흡수, redirect 만 남김.  |
| Deprecate  | 후속 sub-skill 로 대체됨. 외부 참고로만 유의미.                  | `status: deprecated`, `deprecated_by` 명시. |
| Remove     | Karpathy 가 콘텐츠 철회 또는 잘못된 정보로 판명.                  | 파일 삭제 + git 히스토리에 이유 기록.            |

### Step 7 — Implementation

- 결정에 따라 본문 / frontmatter / cross-link 갱신.
- `version` 적절히 bump (의미 변경 = MINOR).

### Step 8 — Communication

- 변경 요약을 `change_log` 또는 git commit message 에 기록.
- 영향받는 다른 sub-skill 의 작성자에게 (또는 자기 자신에게) 알림.

## 3. `stale` 처리

`last_audit` 6개월 초과 시:

1. 자동으로 `status: stale` 부여.
2. 다음 정기 감사에서 재평가.
3. 재평가 시 6종 결정 중 하나로 종료.
4. 일정 기간 (1년) `stale` 유지되면 `Deprecate` 검토.

## 4. 감사 보고서 양식

```markdown
# Audit Report — YYYY Q?

- 감사일: YYYY-MM-DD
- 감사자: (사람 또는 평가 세션)
- 트리거: 정기 / 신작 영상 / 코드 갱신 / ...

## Inventory

- live: N개
- stale: M개
- 신규 트리거 영향: K개

## Decisions

| sub-skill           | 결정       | 사유                          | 후속                  |
| ------------------- | -------- | --------------------------- | ------------------- |
| tf-self-attention   | Continue | 변경 없음                       | last_audit 갱신       |
| dd-deepseek-r1      | Update   | DeepSeek V3.5 발표로 인용 갱신 필요 | 본문 §4.2 갱신, version bump |
| ...                 |          |                             |                     |

## 다음 감사 예정일: YYYY-MM-DD
```

## 5. 외부 참고 (감사 패턴 원전)

- ue-wiki-llm `18_ModelEvolutionAudit` (8단계 + 6종 결정 원전).
- Anthropic 공식 블로그 "How we update models without breaking customer integrations" (구조적 유사 패턴).
