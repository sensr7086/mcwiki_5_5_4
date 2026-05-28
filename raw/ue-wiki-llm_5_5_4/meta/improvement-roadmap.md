---
name: improvement-roadmap
description: 6대 본질 문제 해결 방안 매트릭스 — 우선순위 + 가능성 + 즉시 적용 가능 / 중기 / 장기. 위키를 "비싸지만 부지런히 관리하면 작동" 도구로 유지하기 위한 실용 로드맵.
---

# Wiki 개선 로드맵 — 6대 문제 × 해결 방안

> [`CLAUDE-wiki-honest-limits.md`](./CLAUDE-wiki-honest-limits.md) 의 6대 문제에 대한 **구체적 해결 방안** + 우선순위 + 가능성 매트릭스.
>
> **원칙**: 모든 해결안 = "어떤 비용 / 어떤 가치" 를 명시. 마법 없음.

---

## 0. 종합 우선순위 매트릭스

| 해결안 | 영향도 | 가능성 | 즉시 / 중기 / 장기 | 담당 |
|--------|-------|-------|------------------|------|
| **Confidence Tag 시스템** | ⭐⭐⭐ | 즉시 | 즉시 (P0) | Wiki 작성자 + Claude |
| **라인 번호 → 함수명/시그니처** | ⭐⭐⭐ | 점진 가능 | 즉시 + 점진 (P0) | Claude 자동 |
| **Lazy Read + 30초 요약** | ⭐⭐ | 즉시 | 즉시 (P1) | Wiki 작성자 |
| **정직한 스코프 선언** | ⭐⭐ | 즉시 | 즉시 (P1) | 1회 작업 |
| **인라인 리마인더 (체크리스트 마지막)** | ⭐⭐ | 즉시 | 즉시 (P1) | 점진 |
| **Plan agent 사전 결정** | ⭐⭐ | 가능 | 중기 (P2) | 구조 변경 |
| **CI grep 자동 검증** | ⭐⭐⭐ | 어려움 | 중기 (P2) | 사용자 (CI 셋업) |
| **사용자 피드백 루프 (corrections.md)** | ⭐⭐ | 즉시 | 즉시 (P1) | 사용자 + Claude |
| **다른 모델 Evaluator (Claude vs GPT)** | ⭐⭐⭐ | 어려움 | 장기 (P3) | API 비용 + 셋업 |
| **Compile-time Lint (clang-tidy)** | ⭐⭐⭐ | 매우 어려움 | 장기 (P3) | 도구 작성 |
| **Render / RDG 카테고리 추가** | ⭐⭐ | 시간 소요 | 중기 (P2) | 분기마다 1 카테고리 |

---

## 1. 문제 1 — 토큰 폭주

> **현재**: 시나리오당 100~200KB / 40~60K 토큰 소비. 베이스라인 자체가 큼.

### 해결 1.1 — Lazy Read + 30초 요약 (즉시 ⭐)

**원리**: 모든 횡단 인덱스 (07/10/11/12 등) 첫머리에 **2KB 요약 블록** 추가. Claude 가 요약만 읽고 충분하면 본문 skip.

```markdown
<!-- 10_ComponentPolicies.md 첫머리 -->
## 30-Second Summary (TL;DR)

**6대 의무**:
1. Mobility 명시 (Static/Stationary/Movable)
2. NewObject 패턴 (DuplicateObject 금지)
3. UPROPERTY + TObjectPtr (GC 방어)
4. GetOwner 캐싱 (TWeakObjectPtr)
5. PrimaryComponentTick = false (불필요 시)
6. CDO 검사 (RF_ClassDefaultObject)

**자세한 설명 / 예시 / 함정** = 아래 본문 (또는 references/ComponentPoliciesDeep.md)
```

**효과**: 시나리오당 **30~50K 토큰 절감** (전체 본문 대신 요약만). 작업 진행 중 모호하면 본문 Read.
**비용**: 모든 횡단 인덱스 / 큰 SKILL.md 에 요약 추가 (~14 파일).

### 해결 1.2 — Skill 자동 로드 (Anthropic Skills 표준)

**원리**: SKILL.md 의 `description` (frontmatter) 만 자동 로드 → Claude 가 description 보고 필요 시에만 본문 Read.

```yaml
---
name: animation-ik
description: UE 5.5.4 IK 시스템 — Legacy AnimNode IK + 5.x IK Rig + IK Retargeter. {keywords}
---
```

**현재 상태**: 모든 SKILL.md 이미 frontmatter 있음 ✅. 다만 Claude Code Plugin 모드에서 자동 로드 동작 검증 필요.
**효과**: 사전 로드 양 = 0 → 시나리오 인식 시점에 필요한 것만 Read.

### 해결 1.3 — 시나리오별 Pre-Bundle

**원리**: 자주 쓰는 조합 = 미리 번들 작성.

```
_bundles/
├── animation-character-setup.md  (AnimInstance + AnimGraph + 07/10/11/12 요약)
├── components-actor-component.md (ActorComponent + 10 + 09 요약)
├── editor-asset-toolkit.md       (AssetEditorToolkit + 4단 분리 + 05 요약)
```

**효과**: 1개 Read 로 시나리오 완료 (~20KB).
**비용**: 번들 작성 + 유지 (자동화 어려움).

---

## 2. 문제 2 — 반응 속도 하락

> **현재**: 첫 응답까지 3~5배 느림 (10~15 Read 호출).

### 해결 2.1 — 병렬 Read (즉시 ⭐)

**원리**: Claude 가 Read 호출을 **단일 메시지에 다중** 사용. 직렬 → 병렬.

```
❌ 현재: Read(A) → 응답 → Read(B) → 응답 → ...
✅ 개선: 단일 메시지에 [Read(A), Read(B), Read(C), ...] 동시 호출
```

**효과**: 10회 Read = 직렬 5초 → 병렬 1.5초 (3배 이상 개선).
**상태**: 부분 적용 중. **Specialist agent 별로 의무화**.

### 해결 2.2 — Plan agent 사전 결정

**원리**: Plan agent (또는 Orchestrator) 가 **먼저** 어떤 sub-skill 필요한지 결정 → Specialist 는 정확히 그것만 Read.

```
사용자 명령
  ↓
Plan agent (1 Read = 03_WikiHarness)
  ↓
"이 작업은 X / Y / Z 만 필요" 결정
  ↓
Specialist (3 Read = X / Y / Z 병렬)
```

**현재**: Specialist 가 자체 결정. 일부 잉여 Read 발생.
**효과**: 잉여 Read 50% 감소.

### 해결 2.3 — Skill 자동 로드 (1.2 와 동일)

description 매칭 = 0 Read 로 시작. Anthropic Skills 표준 활용.

---

## 3. 문제 3 — Staleness (라인 번호 깨짐) ⭐

> **현재**: 116 SKILL.md 안 라인 번호 ("Pawn 598") = UE 5.8 즉시 깨짐.

### 해결 3.1 — 라인 번호 → 함수 시그니처 (즉시 ⭐)

**원리**: 라인 번호 대신 함수 시그니처 / 클래스 이름 인용.

```markdown
❌ 현재: APawn.h:598 — PossessedBy
✅ 개선: APawn::PossessedBy(AController* NewController)
        // 5.5.4 기준 — 정확한 라인 = grep "PossessedBy" Source/Runtime/Engine/Classes/GameFramework/Pawn.h
```

**효과**: 라인 변경 영향 X. 함수 시그니처 변경 (드물 때만) 영향.
**비용**: 116 SKILL.md 점진 갱신 (Claude 자동 가능).

### 해결 3.2 — 버전 태그 시스템

**원리**: 모든 인용에 `@ue-5.5.4` 태그. 새 버전 = 자동으로 "재검증 필요" 플래그.

```markdown
> APawn::PossessedBy `@ue-5.5.4` — 라인 598
> @ue-5.8 검증 필요
```

### 해결 3.3 — CI grep 자동 검증 (사용자 셋업)

**원리**: 분기마다 / UE 버전 업그레이드 시 자동 실행 스크립트.

```bash
# 예: scripts/wiki-staleness-check.sh
for SKILL in $(find 02_Skills -name "SKILL.md"); do
  # 1. 클래스 / 함수 이름 추출
  # 2. UE Source 에서 grep
  # 3. 매칭 안 되면 meta/staleness-report.md 에 기록
done
```

**효과**: 분기마다 자동 검증 → staleness 조기 발견.
**비용**: 사용자가 CI / 로컬 스크립트 셋업.

### 해결 3.4 — Diff 기반 감사

**원리**: UE 5.5 → 5.8 git diff → 영향받는 SKILL.md 자동 식별.

```bash
git diff UE-5.5.4..UE-5.8.0 -- Engine/Source/Runtime/Engine/ | \
  grep -E "^\+.*class|^\-.*class" > affected_classes.txt
# → Wiki 의 affected_classes 인용 sub-skill 자동 플래그
```

---

## 4. 문제 4 — 검증 부재의 환각 리스크 ⭐⭐

> **현재**: 116 SKILL.md 일부 = grep 검증 X (LLM 추론). Claude 가 신뢰 → cascade error.

### 해결 4.1 — Confidence Tag 시스템 (즉시 ⭐⭐⭐)

**원리**: 각 섹션 / 인용에 신뢰도 태그.

```markdown
## §3 UAnimInstance Native* 5단계 [verified] ✅
> 검증: grep "NativeUpdateAnimation" Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h
> 결과: 라인 1372 확인 (2026-05-07)

## §4 IK Rig 7 Solvers [grep-listed] ⚠️
> Glob 결과로 헤더 파일 존재 확인. 본문 들여다보지 않음.

## §5 5.x Inertialization 0ms 블렌드 [inferred] ❌
> LLM 추론. 실제 동작 미검증. 사용 전 Epic docs 확인 의무.
```

**3단계 태그**:
- `[verified]` ✅ — grep + 헤더 본문 확인
- `[grep-listed]` ⚠️ — 파일 존재만 확인 (내용 미검증)
- `[inferred]` ❌ — LLM 추론 (가장 위험)

**효과**: Claude 가 코드 작성 시 tag 보고 신뢰도 가중. `[inferred]` = 사용자 / Epic docs 추가 검증 의무.
**비용**: 116 SKILL.md 점진 적용 (큰 작업 — 분기 단위).

### 해결 4.2 — 사용자 피드백 루프 (즉시 ⭐)

**원리**: 사용자가 위키 틀린 부분 발견 시 `meta/corrections.md` 누적.

```markdown
# Wiki Corrections Log

## 2026-05-15 — Animation/IK §3.2 EAdditiveAnimationType
**위키 주장**: AAT_LocalSpaceBase / AAT_RotationOffsetMeshSpace 2종
**실제** (UE 5.5.4 grep): AAT_None / AAT_LocalSpaceBase / AAT_RotationOffsetMeshSpace 3종
**수정**: SKILL.md 갱신 완료 (commit abc123)

## ... (누적)
```

**효과**: 위키가 자기 수정 시스템. 사용자가 디버깅 시 발견한 거짓 = 영구 기록.

### 해결 4.3 — 다른 모델 Evaluator (장기)

**원리**: Generator (Claude) 가 작성 → Evaluator (GPT-5 / Gemini Pro) 가 평가. 다른 사각지대.

**비용**: 별도 API 셋업, 비용. 자동화 어려움.
**효과**: Claude 사각지대 보완 (예: Claude 가 빠뜨린 함정을 다른 모델이 잡음).

### 해결 4.4 — Compile-as-Test (의무화)

**원리**: 위키 기반 코드 = 항상 컴파일 + Cooked Build 검증 후만 "사용 가능".

```
Generator 코드 작성
  ↓
Evaluator 평가 (15_EvaluatorRecipe)
  ↓
사용자 Compile (Development) — 통과 의무
  ↓
사용자 Cooked Build — 통과 의무
  ↓
사용자 런타임 검증 — stat unit / memreport
  ↓
"사용 가능" 인증
```

**효과**: 위키 거짓 → 컴파일 에러 → 즉시 발견.
**비용**: 사용자 의무 (Claude 가 강제 X).

---

## 5. 문제 5 — 지시 준수 감소

> **현재**: 컨텍스트 길수록 LLM 정책 잊음. 작업 중반 1~2개 누락.

### 해결 5.1 — Sub-agent 분리 (이미 적용)

**원리**: 각 specialist = 별도 컨텍스트. orchestrator 가 분배.
**상태**: ✅ 이미 12 specialist 구조 (Plugin v1.3.0).
**효과**: 각 specialist = 짧은 컨텍스트 → 정책 준수 ↑.

### 해결 5.2 — 인라인 리마인더 (즉시 ⭐)

**원리**: SKILL.md 끝부분 체크리스트 = 작업 끝에 다시 한번 표시.

```markdown
## 체크리스트 (작업 종료 전 의무)

- [ ] 6대 정책 적용?
  - [ ] Mobility
  - [ ] NewObject
  - [ ] UPROPERTY + TObjectPtr
  - [ ] GetOwner 캐싱
  - [ ] PrimaryComponentTick
  - [ ] CDO 검사
- [ ] 모든 콜백 첫 줄 프로파일링 스코프?
- [ ] Super 호출 위치 정확?
- [ ] 어셋 = Soft + PreLoad?
- [ ] TActorIterator 사용 X?
```

**현재**: 일부 SKILL.md 만 체크리스트 있음. **모든 SKILL.md 에 의무화**.
**효과**: 작업 중반 망각 방지 (Claude 가 끝에 다시 봄).

### 해결 5.3 — Compile-time Lint (장기)

**원리**: 정책 = 빌드 시 자동 강제. clang-tidy 커스텀 체크.

```cpp
// 예: Mobility 누락 = 빌드 에러
[[ue-policy-mobility]]
class UMyComponent : public UActorComponent
{
    // Constructor 안 SetMobility 호출 안 하면 빌드 에러
};
```

**효과**: 잊을 수 없음. 빌드가 강제.
**비용**: clang-tidy 커스텀 룰 작성 (UE 빌드 시스템 통합 — 상당한 작업).

### 해결 5.4 — Atomic SKILL 분할

**원리**: 30KB SKILL → 5KB × 6 = 각 SKILL 좁고 깊음.
**상태**: 부분 적용 (Level 3 progressive disclosure 일부).
**효과**: Claude 가 작은 SKILL 만 보면 정책 준수 ↑.

---

## 6. 문제 6 — 커버 안 된 영역

> **현재**: Render / RDG / USF / 플랫폼 SDK 거의 0.

### 해결 6.1 — 정직한 스코프 선언 (즉시 ⭐)

**원리**: README / CLAUDE.md 에 "이 위키 = X / Y / Z 만 커버. RDG / USF = Epic docs" 명시.

```markdown
# Wiki Scope

## 커버 ✅
- Components / GameFramework / Animation / Input / UMG / Slate
- AssetClasses / Editor / Subsystem / Plugins (GAS / Niagara / Significance)

## 커버 X (다른 데서) ⚠️
- RDG (Render Dependency Graph) → Epic docs / Source/Runtime/RenderCore
- USF / Custom Shader → Epic docs / Source/Shaders
- SceneViewExtension → Epic docs
- Build.cs / 빌드 시스템 → UnrealBuildTool docs
- 플랫폼 SDK (Steam / EOS / PSN / Switch) → 각 SDK docs
- Online Subsystem → Epic OnlineSubsystem docs
```

**효과**: 사용자 / Claude 가 즉시 "이거 위키 밖" 인지 → 시간 낭비 X.

### 해결 6.2 — 외부 링크 큐레이션

**원리**: 커버 X 영역 = **링크 모음만** 작성 (depth X, breadth O).

```
skills/_OutOfScope/
├── Render-RDG-Links.md   (Epic docs + Source 위치 + 핵심 클래스만 나열)
├── USF-Shader-Links.md
└── Platform-SDK-Links.md
```

**효과**: Claude 가 "이거 위키 밖" 인지 후 → 외부 링크 안내.

### 해결 6.3 — 점진적 확장

**원리**: 분기마다 1 카테고리 추가. 5년 후엔 거의 커버.

| 분기 | 추가 카테고리 |
|------|-------------|
| 2026 Q3 | Render 베이스 (RenderCore + RDG 핵심) |
| 2026 Q4 | USF / Shader 표준 |
| 2027 Q1 | Online Subsystem |
| 2027 Q2 | Platform SDK 매트릭스 |

---

## 7. 우선순위 통합 — 즉시 시작할 5가지 (P0)

다음 5가지 = **이번 / 다음 세션에서 시작 가능**:

### P0-1 — Confidence Tag 시스템 도입 (Problem 4)
- `meta/confidence-tags.md` 작성
- 가장 자주 쓰이는 SKILL.md 5개부터 적용
- 점진 확대

### P0-2 — 라인 번호 → 함수 시그니처 (Problem 3)
- Claude 가 자동 갱신 (스크립트 또는 sub-agent)
- 우선 가장 핵심 SKILL.md 부터

### P0-3 — 30초 요약 블록 (Problem 1)
- 14 횡단 인덱스 + 큰 SKILL.md 첫머리 추가
- 본문 skip 가능

### P0-4 — 정직한 스코프 선언 (Problem 6)
- CLAUDE.md / README 갱신
- `skills/_OutOfScope/` 폴더 신설

### P0-5 — corrections.md 시작 (Problem 4)
- `meta/corrections.md` 빈 파일 + 사용 가이드
- 사용자가 디버깅 시 발견한 거짓 누적

### P0-6 — 측정 누적 시스템 (P4 + 가설 검증) ⭐ 신규

- **상태**: ✅ 시작됨 (2026-05-08 — 첫 측정)
- `meta/measurements/` 폴더 + `_summary.md` 누적 표
- 시나리오별 With-Wiki vs No-Wiki 점수 / 토큰 / 마진 정량 측정
- 신뢰도 등급 (⭐ / ⭐⭐ / ⭐⭐⭐) 으로 self-eval bias 명시
- 진짜 별도 세션 측정 (⭐⭐⭐) 누적이 가설 검증의 핵심
- **첫 실측**: MCSoftStaticMesh +60 마진 (⭐ 가상 baseline) — `meta/measurements/2026-05-08_*.md`

**다음 측정 우선순위**:
1. 별도 세션 No-Wiki Animation 발 IK (⭐⭐ 신뢰도 시도)
2. Editor 인하우스 툴 (예측 +28 검증)
3. 일반 C++ (예측 0 — 위키 무용지 검증)

### P0-7 — 매크로 라이브러리 (Problem 1 — 토큰 폭주) ⭐ 신규 — 전략 1

- **상태**: ✅ 적용됨 (2026-05-08 — 8개 매크로)
- `templates/boilerplate-macros/UEWikiMacros.h` — 8개 핵심 매크로
- **데이터 출처**: `measurements/2026-05-08` 의 토큰 분포 분석 (보일러플레이트 76%)
- **목표**: 위키 코드 13.5x → ~9x 토큰 (정책 준수는 그대로)

**8 매크로 (Problem 1 + Problem 4 결함 회피)**:
1. `UE_WEAK_THIS(N)` — TWeakObjectPtr (-83%)
2. `UE_SAFE_LAMBDA(W, S, B)` — IsValid 자동 람다 (Critical 결함 ② 자동 회피)
3. `UE_DECLARE_STREAMABLE_HANDLE(N)` — Pin + EndPlay Cancel (Critical ①③ 자동 회피)
4. `UE_COMPONENT_DEFAULTS()` — Mobility + Tick=false (-75%)
5. `UE_COMPONENT_DEFAULTS_STATIC()` — Static 변형
6. `UE_RETURN_IF_CDO()` — CDO 가드 (-80%)
7. `UE_PROFILE()` — 함수 자동 프로