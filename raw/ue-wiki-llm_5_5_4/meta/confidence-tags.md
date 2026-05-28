---
name: confidence-tags
description: Wiki 콘텐츠 신뢰도 표시 시스템 — verified / grep-listed / inferred 3단계. 환각 리스크 (P4) 해결책. 모든 SKILL.md 인용에 신뢰도 명시 → Claude / 사용자가 코드 작성 시 가중. 가장 깊은 본질 문제 (위키 자체를 신뢰할 수 없음) 의 직접 대응.
---

# Confidence Tag 시스템

> [`improvement-roadmap.md §P0-1`](./improvement-roadmap.md) — 본질 문제 4 (검증 부재의 환각) 해결.
>
> **요지**: 위키의 모든 인용 = **3단계 신뢰도** 명시. Claude / 사용자가 코드 작성 시 신뢰도에 따라 가중. `[inferred]` = 사용 전 외부 검증 의무.

---

## 1. 3단계 신뢰도 정의

### 1.1 `[verified]` ✅ — 가장 안전

**의미**: grep 으로 클래스 / 함수 / 라인 확인 + 헤더 본문 들여다봄. 5.5.4 기준 사실.

**조건**:
- ✅ grep 결과 매칭 (파일 + 라인 또는 함수명)
- ✅ 헤더 / 소스 본문 직접 읽음
- ✅ 5.5.4 기준 명시
- ✅ 일자 명시

**사용 예**:
```markdown
## §3 UAnimInstance Native* 5단계 [verified] ✅
> grep "NativeUpdateAnimation" `Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h`
> 결과: 라인 1372 (NativeUpdateAnimation), 1378 (NativeThreadSafeUpdateAnimation), 1372 ENGINE_API virtual void
> 검증 일자: 2026-05-07
> UE 버전: 5.5.4
```

### 1.2 `[grep-listed]` ⚠️ — 중간

**의미**: Glob / grep 결과로 파일 또는 심볼 존재 확인. 본문 들여다보지 않음.

**조건**:
- ✅ Glob / grep 결과 파일명 확인
- ⚠️ 헤더 본문 미확인
- ⚠️ 시그니처 / 동작 = LLM 추론

**사용 예**:
```markdown
## §4 IK Rig 7 Solvers [grep-listed] ⚠️
> Glob: `Engine/Plugins/Animation/IKRig/Source/IKRig/Public/Rig/Solvers/*.h`
> 결과: IKRigBodyMoverSolver.h / IKRigFullBodyIK.h / IKRigLimbSolver.h /
>      IKRigPoleSolver.h / IKRigSetTransform.h / IKRigStretchLimb.h / IKRigSolverBase.h
> 미확인: 각 Solver 의 정확한 동작 / 파라미터 / virtual 시그니처
> 검증 필요: Epic docs 또는 헤더 본문 직접 확인
```

### 1.3 `[inferred]` ❌ — 가장 위험

**의미**: LLM 추론. grep 검증 없음. UE 표준 패턴 또는 일반 지식 기반.

**조건**:
- ❌ grep 검증 X
- ❌ 헤더 본문 미확인
- ⚠️ LLM 의 UE 일반 지식 추론
- 🚨 사용 전 외부 검증 의무

**사용 예**:
```markdown
## §5 5.x Inertialization 0ms 블렌드 [inferred] ❌
> 출처: LLM 추론 (UE 일반 지식)
> 미검증: 실제 동작 / API 시그니처 / 파라미터
> 사용 전 의무:
>   - Epic docs 검색: "Inertialization Unreal Engine 5"
>   - grep 검증: Engine/Source 안 FAnimNode_Inertialization 정의
>   - Cooked Build 동작 확인
```

---

## 2. 적용 규칙

### 2.1 적용 위치

| 위치 | 적용 의무 |
|------|---------|
| 클래스 / 함수 인용 (라인 번호 / 시그니처) | ✅ 의무 |
| 5.x 신규 API 설명 | ✅ 의무 |
| 함정 / 안티패턴 | ✅ 의무 |
| 결정 매트릭스 / 선택 기준 | ⚠️ 권장 |
| 메인 내러티브 (요약 / 인덱스) | ❌ 선택 |

### 2.2 섹션 단위 vs 인용 단위

```markdown
✅ 섹션 단위 (권장 — 효율):
## §3 UAnimInstance Native* 5단계 [verified]
(전체 섹션이 verified)

✅ 인용 단위 (정밀 필요 시):
## §5 IK Rig
- UIKRigDefinition [verified]
- 7 Solvers [grep-listed]
- FBIK 다중 골 동시 풀이 [inferred]
- AnimGraph 통합 흐름 [inferred]
```

### 2.3 Claude 의 동작 의무

Claude 가 코드 작성 시:
- `[verified]` 인용 → 신뢰 가능 (직접 사용)
- `[grep-listed]` 인용 → "본문 추가 검증 권고" 라고 사용자에게 알림
- `[inferred]` 인용 → "사용 전 외부 검증 의무" 라고 사용자에게 명시 + 코드 작성 시 보수적 접근

---

## 3. 적용 우선순위 (점진 적용)

### Phase 1 — Tier 1 핵심 SKILL 5개 (P0 — 우선)

```
□ skills/CoreUObject/references/UObject.md
□ skills/Components/references/ActorComponent.md
□ skills/GameFramework/references/Actor.md
□ skills/Animation/references/AnimInstance.md
□ skills/AssetClasses/references/Mesh.md
```

### Phase 2 — Tier 1 나머지 + 횡단 인덱스

```
□ skills/Components/* (15)
□ skills/GameFramework/* (6)
□ skills/Animation/* (7)
□ references/10/11/12 (3)
```

### Phase 3 — 전체 (분기 단위)

```
□ 02_Skills 전체 (116)
□ 00_Overview 횡단 인덱스 (14)
```

---

## 4. Claude 자동 적용 가이드 (Wiki 작성 시)

**규칙**:

```python
def assign_confidence(citation):
    if grep_verified and read_header:
        return "[verified]"
    elif glob_listed_only:
        return "[grep-listed]"
    else:  # LLM inference
        return "[inferred]"
```

**의무**:
1. Wiki 작성 / 갱신 시 반드시 태그 부여
2. 검증 일자 + UE 버전 명시
3. `[inferred]` = 다음 검증자 (Evaluator / 사용자) 가 의무 검증

---

## 5. 사용자 피드백 통합

`meta/corrections.md` 에 사용자가 발견한 거짓 누적:

```markdown
## 2026-05-15 — Animation/IK §3.2 [inferred → 거짓]
**위키 주장** [inferred]: "EAdditiveAnimationType 2종"
**실제** (사용자 grep): "3종 — AAT_None / AAT_LocalSpaceBase / AAT_RotationOffsetMeshSpace"
**조치**: SKILL.md 갱신 → [verified] 태그로 격상
```

→ `[inferred]` 항목들이 점진 `[verified]` 로 격상 (또는 삭제).

---

## 6. 효과 (예상)

| 측면 | 적용 전 | 적용 후 |
|------|--------|--------|
| Claude 의 위키 신뢰 가중 | 균일 (모두 신뢰) | 차등 (verified 우대) |
| 환각 리스크 | 80~85% 정확도 | 90%+ (검증된 것만 신뢰) |
| 사용자 검증 부담 | 전체 의무 | `[inferred]` 만 |
| 위키 staleness 감지 | 늦음 (분기 감사) | 즉시 (사용 시 검증) |

---

## 7. 첫 적용 예시 — Animation/IK [grep-listed → verified 격상]

현재 `skills/Animation/references/IK.md` 상태:
- 7 Solvers 목록 = `[grep-listed]` (Glob 결과로 파일명 확인 / 본문 미확인)
- AnimNode_IKRig 라이프사이클 = `[inferred]` (LLM 추론)
- IK Retargeter 16 Ops = `[grep-listed]` (파일명만)
- Legacy AnimNode IK 8종 = `[grep-listed]`

**격상 작업** (다음 세션):
1. 각 Solver 헤더 직접 Read → `[verified]`
2. AnimNode_IKRig 헤더 Read → 시그니처 검증
3. 16 Ops 각 파일 첫 줄 확인 → `[verified]`

---

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. **3단계 신뢰도 시스템** 정의 + 적용 규칙 + Claude 동작 의무 + 점진 적용 우선순위 + 사용자 피드백 통합. **P4 (환각 리스크) 직접 대응**. |
