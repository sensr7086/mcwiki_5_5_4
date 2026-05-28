---
id: meta-policy-priority
title: Policy Priority — Article 1 ~ 10
version: 0.1.0
status: live
last_audit: 2026-05-09
language: ko
parent: ../CLAUDE-wiki-governance.md
---

# Policy Priority — Article 1 ~ 10

정책 충돌 시 **위쪽 Article 이 항상 우선**한다. 본 문서는 거버넌스 §5 의 상세본.

## Article 1 — Generator/Evaluator 분리 (최상위)

> 작성한 세션은 같은 세션 안에서 그 글을 평가하지 않는다.

**근거**: Anthropic "Building effective agents" — 자가 평가는 편향이 강하다. 평가는 별도 세션에서 빈 컨텍스트로 시작.

**위반 예시**: "방금 쓴 sub-skill 을 같은 대화에서 점수까지 매기기."

## Article 2 — 정확성 (Karpathy 영상/코드와 일치)

> 영상/코드와 다른 진술이 발견되면, 본문이 즉시 우선 수정된다. 단순화는 허용되지만 사실 왜곡은 금지.

**근거**: Karpathy 콘텐츠는 "spelled out" 정확성을 핵심 가치로 한다. 위키가 그것을 깨면 존재 의의 상실.

**위반 예시**: causal mask 의 `-inf` 위치를 잘못 표기, AdamW 의 weight decay 기본값을 잘못 인용.

## Article 3 — 출처 추적성

> 모든 핵심 주장에는 S/B 등급 인용이 붙는다. 인용 없는 일반론은 등재하지 않는다.

**근거**: 위키의 신뢰도 = 역추적 가능성.

**위반 예시**: "보통 LR 은 3e-4 가 좋습니다" (출처 없음). → 수정: `[Z2H#9 33:12]` 영상에서 Karpathy 가 인용한 LR 기준 제시.

## Article 4 — 단순성

> 같은 결과를 내는 두 설명/코드 중에서, 더 짧고 단순한 쪽이 우선.

**근거**: Karpathy 의 스타일 그 자체. micrograd 가 ~150 LOC 로 자동미분을 보이는 것이 본보기.

**위반 예시**: 추상 클래스를 5단 상속해 만든 attention 구현.

## Article 5 — 재현성

> 시드 / 차원 / 환경 (PyTorch 버전, 디바이스) 명시.

**근거**: 영상에서도 항상 `torch.manual_seed(1337)` 로 결정성 확보.

**위반 예시**: "loss 가 ~2.5 로 떨어집니다" (시드 없음).

## Article 6 — 시간 견디기

> 모델 이름·논문 인용·코드 라인은 frontmatter `last_audit` 에 묶어둔다. 본문에 "최신" 표현 금지.

**근거**: GPT-2 → GPT-4 → o1 → R1 처럼 외부 정의가 빠르게 변한다. 위키 본문은 audit cycle 로 그 변화를 흡수해야 한다.

**위반 예시**: "현존 최강 모델인 GPT-4" (시간 의존).

## Article 7 — 한국어 본문

> 본문 산문은 한국어. 클래스/함수/하이퍼파라미터 식별자, 영상 인용, 논문 제목은 영어 그대로.

**위반 예시**: `BatchNorm` 을 "배치정규화" 로 일관성 없이 혼용.

## Article 8 — 분량 절제

> sub-skill 본문은 300~1500 줄. Karpathy 의 어조 (담백, 사족 없음) 모방.

**위반 예시**: "참고로", "사실", "한편" 남발. 같은 개념을 두 번 설명.

## Article 9 — Cross-link (SSoT)

> 한 주제는 한 sub-skill 에서만 정식 설명. 다른 곳에서는 한 줄 요약 + 정식 sub-skill 링크.

**위반 예시**: BPE 를 `40_Tokenizer` 와 `30_Transformer` 양쪽에서 풀어쓰기.

## Article 10 — Audit 트레일

> 모든 변경은 frontmatter `last_audit` 갱신과 짧은 사유 (커밋 메시지 또는 `change_log`).

**위반 예시**: 본문 한 줄 수정하고 `last_audit` 그대로 두기.

---

## 충돌 시나리오

- **Article 4 (단순성) vs Article 2 (정확성)**: 단순성을 위해 코드를 줄였더니 영상과 결과가 달라진다 → Article 2 승리. 정확성 우선.
- **Article 8 (분량) vs Article 3 (출처)**: 본문이 길어진다고 인용을 빼면 안 된다 → Article 3 승리. 본문 다른 곳을 줄여라.
- **Article 7 (한국어) vs Article 9 (cross-link)**: 한국어 sub-skill 이 영어 sub-skill 을 인용 → 영어 식별자 그대로 인용 OK.
