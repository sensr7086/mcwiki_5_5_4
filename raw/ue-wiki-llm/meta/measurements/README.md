---
name: wiki-measurements
description: 위키 효용 실측 누적 시스템 — 가설 (CLAUDE-wiki-honest-limits §1) 을 데이터로 검증. 시나리오별 With-Wiki vs No-Wiki 점수 / 토큰 / 마진 누적.
---

# `meta/measurements/` — 위키 효용 실측 누적

> [`CLAUDE-wiki-honest-limits.md`](../CLAUDE-wiki-honest-limits.md) §1 의 **예측 매트릭스** (Components/GameFramework +15%p 등) 를 **실측 데이터로 검증**.
>
> 매번 작업 후 위키 효용을 측정 → 누적 → 가설 보정.

---

## 📊 측정 표준

각 측정 = 한 시나리오 / 한 작업 단위. 다음 4축 기록:

| 축 | 측정 |
|----|------|
| **A. With-Wiki** | 위키 표준 + 정책 적용한 코드 점수 / 토큰 |
| **B. No-Wiki** | 위키 없이 (또는 No-Wiki 가상 baseline) 같은 작업 점수 / 토큰 |
| **마진** | A점 - B점 (위키 가치) |
| **토큰 비용** | A토큰 - B토큰 (위키 비용) |

---

## 📁 파일 명명 규약

```
{YYYY-MM-DD}_{시나리오}_with-vs-no-wiki.md
```

예시:
- `2026-05-08_MCSoftStaticMesh_with-vs-no-wiki.md` ⭐ (첫 실측)
- `2026-05-15_AnimationFootIK_with-vs-no-wiki.md`
- `2026-05-22_EditorAssetEditor_with-vs-no-wiki.md`

---

## 🔬 측정 신뢰도 등급

| 등급 | 조건 | 신뢰도 |
|------|------|--------|
| ⭐⭐⭐ | **별도 Claude 세션** No-Wiki + **별도 평가자** | 가장 높음 |
| ⭐⭐ | 같은 Claude **다른 컨텍스트** No-Wiki + 별도 평가자 | 보통 |
| ⭐ | 같은 Claude **가상 No-Wiki baseline** + 자기 평가 | 낮음 (Self-eval bias 위험) |

**현재 누적**:
- ⭐⭐⭐: 0건
- ⭐⭐: 0건
- ⭐: 1건 (2026-05-08 MCSoftStaticMesh)

→ 진짜 외부 측정 (⭐⭐⭐) 이 누적되어야 가설 검증 신뢰 가능.

---

## 📋 측정 보고서 표준 형식

```markdown
# Evaluator Report — {시나리오}
> 대상 / 날짜 / 평가 표준

## 0. 평가 요약
| 항목 | A. With-Wiki | B. No-Wiki |
|------|--------------|------------|
| 라인 수 / 문자 / 토큰 | ... | ... |
| 정책 통과 | N/16 | N/16 |
| 종합 점수 | XX/100 | XX/100 |
| 권장 | ... | ... |

## 1. 정책 준수 매트릭스 (15_EvaluatorRecipe Stage 1)
## 2. Critical 결함 (있을 시)
## 3. 토큰량 ↔ 효율성 트레이드오프
## 4. 점수 계산 (가중치)
## 5. 권장 수정
## 6. 외부 검증 의무 (Stage 8)
## 7. 결론
## 8. 적용 정책 인용
```

---

## 🎯 누적 표 — `_summary.md`

전체 측정 결과 통계는 [`_summary.md`](./_summary.md) 참조.

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | **첫 실측** 보관 — MCSoftStaticMesh +60 마진 (⭐ 신뢰도 — 가상 baseline) |
