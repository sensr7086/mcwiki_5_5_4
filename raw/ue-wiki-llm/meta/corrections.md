---
name: wiki-corrections-log
description: 사용자가 디버깅 / 컴파일 / Cooked Build 검증 중 발견한 위키 거짓 / 부정확 항목 누적 로그. P4 (환각 리스크) 자기수정 시스템.
---

# Wiki Corrections Log

> 사용자가 위키를 신뢰하고 코드 작성 → 컴파일 / 런타임 / Cooked Build 에서 거짓 발견 시 본 문서에 영구 기록.
>
> **목적**: 위키의 자기수정 시스템. `[inferred]` 항목이 거짓으로 판명 → 즉시 갱신 + 영구 학습.

---

## 사용법

### 거짓 발견 시 작성 형식

```markdown
## YYYY-MM-DD — {SKILL.md 경로} §{섹션}

**위키 주장** `[verified|grep-listed|inferred]`:
> {틀린 내용 인용}

**실제** (검증 방법):
> {실제 동작 / 정확한 API}

**검증 출처**:
- grep: `명령어`
- Cooked Build 결과: {로그}
- Epic docs: {링크}
- 사용자 디버깅: {상황}

**조치**:
- [ ] SKILL.md 갱신 (commit {SHA})
- [ ] Confidence Tag 격상 / 강등
- [ ] Cross-link 영향 받는 sub-skill 갱신
- [ ] 사용자 알림 (Critical 시)

**영향 받는 코드** (있을 시):
- 파일:라인
- 권고: 재작성 / 패치
```

---

## 영구 기록 (시간순)

### (예시 항목 — 실제 발견 시 교체)

```markdown
## 2026-05-15 — Animation/references/IK.md §3.2 [inferred → 거짓]

**위키 주장** [inferred]:
> "AnimNode_IKRig 의 LODThreshold 는 2 가 권장"

**실제** (Cooked Build 검증):
> Cooked Shipping 에서 LODThreshold=2 시 LOD 2+ 의 IK 가 부분 적용 → flicker 발생.
> 실제 권고: LODThreshold=1 또는 -1 (모든 LOD) 또는 0 (LOD 0 만).

**검증 출처**:
- grep `LODThreshold` `Engine/Plugins/Animation/IKRig/Source/IKRig/Public/AnimNodes/AnimNode_IKRig.h` → 해당 멤버는 int32 (음수 = 모든 LOD)
- Cooked Shipping 빌드 + 디바이스 테스트 (PC High)

**조치**:
- [x] SKILL.md 갱신 → "LODThreshold = 0 (LOD 0만) / 1 (LOD 0,1) 또는 -1 (모든 LOD). 2+ = 권장 X"
- [x] Confidence Tag → [verified]
- [x] ue-animation-specialist.md cross-link 갱신

**영향 받는 코드**:
- (사용자 프로젝트 — Source/MyGame/Private/MyAnimInstance.cpp:42)
- 권고: LODThreshold=2 → LODThreshold=1 변경
```

---

## (실제 항목 시작 — 빈 상태)

> 아직 발견된 거짓 없음. 사용자가 디버깅 / 검증 중 발견 시 위 형식으로 추가.

---

## 통계 (월간 / 분기별 자동 계산)

```
2026 Q2 (5월):
- [verified] 항목 거짓 발견: 0
- [grep-listed] 항목 거짓 발견: 0
- [inferred] 항목 거짓 발견: 0
- 갱신된 SKILL.md: 0

(통계는 거짓 발견 시 누적)
```

---

## Confidence Tag 변동 추적

| SKILL.md | 섹션 | 이전 Tag | 신규 Tag | 사유 | 일자 |
|----------|------|---------|---------|------|------|
| (예) Animation/IK §3.2 | LODThreshold | [inferred] | [verified] (수정 후) | 사용자 Cooked 검증 | 2026-05-15 |
| ... | ... | ... | ... | ... | ... |

---

## 자주 발견되는 거짓 패턴 (학습)

### 패턴 1 — 5.x 신규 API 환각

LLM 이 "5.x 표준" 으로 추론한 API 가 실제로 존재 X 또는 시그니처 다름.
**대응**: `[inferred]` 의 5.x API = 사용 전 grep 의무.

### 패턴 2 — 라인 번호 오류

UE 5.7 minor 패치 (5.7.1 → 5.7.4) 만으로도 라인 번호 변경 가능.
**대응**: 함수 시그니처 우선 + 라인 번호는 보조.

### 패턴 3 — 동작 추론 오류

Glob 결과로 파일은 확인했지만 동작은 추론. 실제와 다름.
**대응**: `[grep-listed]` → 헤더 본문 Read 후 `[verified]` 격상.

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. **사용자 피드백 통합 시스템** 시작. P4 (환각 리스크) 자기수정 도구. |

---

## 관련

- 🚨 [`confidence-tags.md`](./confidence-tags.md) — 3단계 신뢰도 시스템
- 🚨 [`CLAUDE-wiki-honest-limits.md`](./CLAUDE-wiki-honest-limits.md) — 위키 본질 한계
- 📋 [`improvement-roadmap.md`](./improvement-roadmap.md) — 6대 문제 × 해결 방안
- 🕰 [`../references/18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) — 분기별 staleness 감사
