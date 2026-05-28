---
id: meta-handoff-protocol
title: Handoff Protocol — sub-skill 간 cross-link 규약
version: 0.1.0
status: live
last_audit: 2026-05-09
language: ko
parent: ../CLAUDE-wiki-governance.md
---

# Handoff Protocol

sub-skill 간 인용/링크 규약. **SSoT 위반 (한 주제를 여러 곳에서 풀어쓰기) 방지** 가 목적.

## 1. 핵심 원칙

1. **한 주제 = 한 sub-skill 정식 설명**.
2. 다른 sub-skill 에서 같은 주제를 언급할 때는 **한 줄 요약 + 정식 sub-skill 링크**.
3. 정식 sub-skill 의 frontmatter `id` 가 인용의 anchor.

## 2. cross-link 형태 4종

### 2.1. 본문 링크 (가장 흔함)

```markdown
... self-attention 의 인과 마스크는 [tf-self-attention §4](../30_Transformer/05_SelfAttention.md#4-causal-mask) 참조.
```

규칙:
- 상대 경로. `../<카테고리>/<파일>.md[#앵커]`.
- 인용 시 `id` 도 같이 언급해 검색성 확보.

### 2.2. frontmatter `related`

같은 학습 흐름에서 함께 보면 좋은 sub-skill. 1~5개.

```yaml
related:
  - 30_Transformer/05_SelfAttention
  - 30_Transformer/06_MultiHead
  - 40_Tokenizer/02_BPE
```

### 2.3. frontmatter `prerequisites`

학습 순서상 먼저 읽어야 하는 sub-skill. 0~3개.

```yaml
prerequisites:
  - 10_Foundations/01_Micrograd
  - 30_Transformer/03_Token_Position_Embedding
```

### 2.4. Glossary 인용

자주 등장하는 용어 (LayerNorm, BPE, KV cache 등) 는 `90_Glossary/` 의 단일 항목으로 환원하고, 본문에서는:

```markdown
KV cache ([90_Glossary/kv-cache](../90_Glossary/README.md#kv-cache)) 는 ...
```

## 3. 본문 안 "관련 sub-skill" 절 표준

§4.1 의 8개 의무 절 중 **§8 관련 sub-skill** 은 다음 형식:

```markdown
## 8. 관련 sub-skill

### 학습 선행 (prerequisites)
- [10_Foundations/01_Micrograd](../10_Foundations/01_Micrograd.md) — 자동미분 기초.

### 다음 단계 (next)
- [30_Transformer/06_MultiHead](./06_MultiHead.md) — self-attention 의 멀티헤드 확장.

### 관련 주제 (related)
- [40_Tokenizer/02_BPE](../40_Tokenizer/02_BPE.md) — 입력 토큰화는 self-attention 의 입력 차원을 결정.
- [70_Deep_Dive_LLM/03_Inference](../70_Deep_Dive_LLM/03_Inference.md) — 추론 단계의 KV cache 와 직결.
```

3개 그룹 (prerequisites / next / related) 으로 분리.

## 4. SSoT 위반 검출

### 4.1. 자동 (대략적)

```bash
# 같은 키워드가 여러 sub-skill 에서 정식 설명되는지 점검 (heuristic)
grep -rn "## 1. 정의" 30_Transformer/ 40_Tokenizer/ | head
```

### 4.2. 수동

분기별 감사 (`04_AuditPolicy.md` Step 4) 의 cross-reference 단계에서 점검.

## 5. 자주 보이는 위반

| 위반                                                          | 처리                                          |
| ----------------------------------------------------------- | ------------------------------------------- |
| BPE 를 `40_Tokenizer/02_BPE` 와 `30_Transformer/03_Embed` 양쪽 정식 설명 | `30_Transformer/03_Embed` 에서는 한 줄 요약 + 링크만 남김. |
| LayerNorm 을 `20_Makemore/03_BatchNorm` 안에서 풀어쓰기                | `90_Glossary` 항목으로 분리 + 본문 cross-link.        |
| `related` 가 없는 sub-skill                                      | 완전성 -3 (Quality).                            |
| 깨진 상대 경로                                                     | 완전성 -2 / 회.                                  |

## 6. cross-link 갱신 트리거

다음 이벤트 발생 시 인용하는 sub-skill 을 모두 점검:

- 인용 대상의 `id` 변경.
- 인용 대상의 카테고리 이동.
- 인용 대상이 `deprecated` / `removed`.
- 인용 대상의 절 구조 (`§N`) 변경.

## 7. 외부 링크 (Karpathy 영상/논문/레포) 와의 차이

본 protocol 은 **위키 내부** 링크에만 적용. 외부 링크는 `karpathy_source` (frontmatter) + 본문 인용 형식 (`[Z2H#7 1:23:45]`) 을 따른다 (`거버넌스 §2`).
