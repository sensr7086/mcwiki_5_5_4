---
id: meta-frontmatter-standard
title: Frontmatter Standard — sub-skill YAML 의무 필드
version: 0.1.0
status: live
last_audit: 2026-05-09
language: ko
parent: ../CLAUDE-wiki-governance.md
---

# Frontmatter Standard

모든 sub-skill 은 본 표준의 YAML frontmatter 로 시작한다. 누락 1개당 Quality 점수 -2.

## 1. 필수 필드 (8개)

```yaml
---
id: <category>-<short-slug>            # 전역 유일. 예: tf-self-attention
title: <한국어 제목 또는 영어 식별자 + 한국어 부제>
version: 0.1.0                          # SemVer
status: draft | evaluated | live | stale | deprecated
last_audit: YYYY-MM-DD                  # 최근 감사일
language: ko                            # 본문 언어
category: 10_Foundations | 20_Makemore | ...   # 디렉토리 이름
karpathy_source:                        # S 등급 출처 1개 이상
  - kind: youtube                       # youtube | github | blog | x
    ref: "Z2H#7 Let's build GPT"
    url: "https://www.youtube.com/watch?v=kCc8FmEb1nY"
    timestamps:                         # 영상이면 핵심 구간
      - "0:00:00 intro"
      - "1:23:45 multi-head"
---
```

## 2. 선택 필드 (10개)

```yaml
---
# (위 필수 필드 생략)
quality_score: 87                       # Evaluator 채점 결과 (0-100)
quality_notes: "정확성 27/30, 출처 18/20, 완전성 22/25, 가독성 20/25"
related:                                # cross-link (Handoff)
  - 30_Transformer/05_SelfAttention
  - 40_Tokenizer/02_BPE
prerequisites:                          # 학습 선행 sub-skill
  - 10_Foundations/01_Micrograd
papers:                                 # B 등급 인용
  - "Vaswani et al. 2017, Attention Is All You Need"
  - "Bengio et al. 2003, A Neural Probabilistic Language Model"
code_repos:                             # S 등급 코드
  - karpathy/nanoGPT (commit a82b33b)
torch_version: "2.x"
seed: 1337
gpu_required: false
change_log:
  - "2026-05-09: 초안 작성"
deprecated_by: 30_Transformer/06_FlashAttention   # status: deprecated 시 필수
---
```

## 3. 필드 규칙

### 3.1. `id`

- 형식: `<2글자 카테고리 코드>-<kebab-slug>`
- 카테고리 코드:
  - `mt` (meta), `fd` (foundations), `mm` (makemore), `tf` (transformer), `tk` (tokenizer), `gp` (gpt2-reproduce), `it` (intro-talk), `dd` (deep-dive), `hu` (how-i-use), `gl` (glossary)
- 예: `tf-self-attention`, `mm-batchnorm`, `tk-bpe`.

### 3.2. `version`

- SemVer.
- 본문 의미 변경 = MINOR (`0.1.0 → 0.2.0`).
- 오타/링크 수정 = PATCH (`0.1.0 → 0.1.1`).
- 카테고리 이동/대규모 재구성 = MAJOR (`0.x → 1.0`).

### 3.3. `status`

| 값          | 의미                              |
| ---------- | ------------------------------- |
| draft      | 작성 중. 평가 미통과.                    |
| evaluated  | Evaluator 통과. cross-link 미완료 가능. |
| live       | 5단 의무 모두 통과 (`거버넌스 §8`).         |
| stale      | `last_audit` 6개월 초과 또는 트리거 감사 대기. |
| deprecated | 후속 sub-skill 로 흡수. body 는 redirect. |

### 3.4. `last_audit`

- ISO-8601 (`YYYY-MM-DD`).
- 본문/frontmatter **어느 한 줄이라도** 변경 시 갱신.

### 3.5. `karpathy_source`

- 최소 1개. S 등급 (영상 또는 GitHub) 위주.
- `timestamps` 는 영상의 경우 권장 (3~10개).

### 3.6. `related` / `prerequisites`

- 상대 경로 (`30_Transformer/05_SelfAttention`, 확장자 생략 가능).
- `prerequisites` 는 학습 순서상 먼저 봐야 할 sub-skill.

## 4. 자동 검증 (선택)

다음 셸 한 줄로 frontmatter 무결성 점검 가능:

```bash
# 모든 .md 의 frontmatter 만 추출
find . -name "*.md" -exec sh -c 'awk "/^---$/{i++}i==1" "$1"' _ {} \;
```

CI 가 있다면 `python-frontmatter` 또는 `js-yaml` 로 의무 필드 존재 검사를 권장.

## 5. 예시 — `tf-self-attention`

```yaml
---
id: tf-self-attention
title: Self-Attention — Q,K,V 의 의미와 causal mask
version: 0.1.0
status: draft
last_audit: 2026-05-09
language: ko
category: 30_Transformer
karpathy_source:
  - kind: youtube
    ref: "Z2H#7 Let's build GPT"
    url: "https://www.youtube.com/watch?v=kCc8FmEb1nY"
    timestamps:
      - "0:24:00 mathematical trick"
      - "0:42:00 single head of self-attention"
      - "1:11:00 multi-head"
  - kind: github
    ref: "karpathy/nanoGPT/model.py L23-L80"
    url: "https://github.com/karpathy/nanoGPT/blob/master/model.py"
related:
  - 30_Transformer/06_MultiHead
  - 30_Transformer/07_GPT_Block
prerequisites:
  - 30_Transformer/03_Token_Position_Embedding
papers:
  - "Vaswani et al. 2017, Attention Is All You Need, §3.2"
torch_version: "2.x"
seed: 1337
---
```
