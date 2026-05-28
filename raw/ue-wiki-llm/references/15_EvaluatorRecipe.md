---
name: evaluator-recipe
description: 다른 Claude 인스턴스 / 사용자가 코드 리뷰어 (Evaluator) 역할 시 사용하는 회의적 평가 표준. UE 빌드 / stat unit / Cooked Build / Replicated 정합성 / GC 누수 / 정책 위반 자동 검사. Anthropic harness-design 글 1 의 "Generator + Evaluator 분리" 패턴 실현.
---

# 15. Evaluator Recipe — Generator/Evaluator 분리 표준

> 본 문서는 **글 1 (harness-design) 의 핵심 통찰** — "**Generator 가 자기 결과를 평가하면 무비판적으로 칭찬한다**" — 의 LLM_Wiki 적용. **다른 Claude 인스턴스 또는 사용자가 평가자 역할** 시 사용하는 회의적 평가 표준.
>
> **요지**: Wiki 작성자 / 코드 작성자가 자기 평가 = **자기 평가 편향**. 별도 Evaluator 가 평가해야 객관적. 본 문서는 **회의적 평가자의 행동 표준** 정의.

---

## 0. 평가자의 마인드셋 (Calibration)

### 0.1 회의적 모드 활성화

```
Generator 의 마인드셋:
  - "이 코드는 정책 따랐다"
  - "이 정도면 충분"
  - "테스트 안 해도 동작할 것"

Evaluator 의 마인드셋 (의무):
  - "어떤 함정을 못 봤나?"
  - "Cooked Build 에서 깨질 수 있나?"
  - "5년 후 다른 사람이 이 코드 보면?"
  - "정책 충돌 가능?"
  - "Edge case 모두 검토됐나?"
```

### 0.2 평가 시점

| 시점 | 적합한 Evaluator |
|------|----------------|
| Sub-skill 작성 후 | 다른 Claude 인스턴스 (별도 세션) |
| 코드 작성 후 | 사용자 (UE 개발자 — 직접 빌드 가능) |
| 큰 작업 (3+ 단계) 종료 시 | 두 단계: Claude 평가 → 사용자 검증 |
| Production 직전 | 사용자 (외부 검증 필수) |

### 0.3 글 1 의 4기준 → UE 적용

| 글 1 기준 | UE 적용 |
|----------|--------|
| **Design quality** | Code Architecture (SRP / DRY / 의존성 그래프) |
| **Originality** | (UE 표준 준수 — Originality 보다 Idiomatic) |
| **Craft** | UE 5.x 표준 코드 스타일 / 정책 준수 |
| **Functionality** | 실제 동작 (빌드 / 런타임 / Cooked / 멀티 플랫폼) |

→ **본 문서 §3 의 4기준** = Performance / Memory / Network / Maintainability.

---

## 1. 평가 단계 표준 (8단)

### Stage 1 — 정책 위반 자동 검사 (Static)

```
┌─ §1 6대 정책 (10_ComponentPolicies)
│  □ Mobility 명시?
│  □ NewObject 패턴 정확?
│  □ GC 방어 (UPROPERTY + TObjectPtr)?
│  □ GetOwner 캐싱?
│  □ PrimaryComponentTick = false?
│  □ CDO + RF_ClassDefaultObject 검사?
│
├─ §2 어셋 로드 (11_AssetLoadingPolicy)
│  □ Constructor 안 어셋 로드 X?
│  □ BeginPlay 동기 LoadObject X?
│  □ Soft vs Hard 결정 정확?
│  □ FStreamableHandle Pin?
│  □ Async 콜백 IsValid 검사?
│
├─ §3 어셋 최적화 (12_AssetOptimizationPolicy)
│  □ SkeletalMesh = LODSettings + BonesToRemove?
│  □ StaticMesh = ScreenSize 표준?
│  □ Audio = Attenuation + Concurrency?
│  □ Niagara = EffectType + Pool?
│
├─ §4 Input (Input)
│  □ Enhanced Input 사용?
│  □ DefaultInput.ini 두 줄?
│  □ ETriggerEvent 정확?
│  □ DeadZone 의무?
│  □ LocalPlayer Subsystem?
│
├─ §5 프로파일링 (07_ProfilingScopeRule)
│  □ Tick / Timer / 람다 / OnRep_* 첫 줄 스코프?
│
├─ §6 전역 이터레이터 (09_GlobalIteratorPolicy)
│  □ TActorIterator / TObjectIterator 사용 안 함?
│  □ Subsystem 등록 패턴 사용?
│
└─ §7 Override 규약 (04_OverrideIndex)
   □ Super 호출 위치 정확? (PostInit 처음 / EndPlay 마지막)
```

### Stage 2 — 컴파일 검증 (의무)

```bash
# Development Editor
"<UE>/Engine/Build/BatchFiles/Build.bat" <Project>Editor Win64 Development -Project="<.uproject>"
# 결과: 0 Error, 0 Warning 표준 (Warning 도 검토)

# Cooked Build (Development) — 글 1 핵심
"<UE>/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun \
  -project="<.uproject>" \
  -platform=Win64 \
  -clientconfig=Development \
  -build -cook -package
# 결과: Cook 단계 Error 0 + Package 단계 정상

# Cooked Build (Shipping) — Production 필수
... -clientconfig=Shipping ...
```

### Stage 3 — 런타임 검증 (Editor PIE → Standalone → Cooked)

| 단계 | 명령 | 검증 |
|------|------|------|
| 1 | Editor PIE | 컴파일 통과 / 즉시 동작 |
| 2 | Standalone Game (`-game`) | Editor 캐시 없이 동작 |
| 3 | **Cooked Build (Development)** | **글 1 핵심 — Editor PIE 와 다름** |
| 4 | Cooked Build (Shipping) | 최종 Production |

```cpp
// 콘솔 검증 명령어 (Cooked 안에서도)
stat unit                 // Game / Draw / GPU 시간
stat fps                  // FPS
stat memory               // 메모리
stat scenerendering       // 렌더 통계
memreport -full           // 풀 메모리 리포트
profilegpu                // GPU 1프레임 프로파일
showflag.X                // 디버그 시각화
```

### Stage 4 — 성능 측정 (4기준)

#### 4.1 Performance (목표: 60fps 또는 30fps)

```
stat unit
- Frame: < 16.67ms (60fps) / < 33.33ms (30fps)
- Game: < 8ms (50%) — CPU 게임 스레드
- Draw: < 5ms (30%) — CPU 렌더 스레드
- GPU: < 8ms (50%)

stat scenerendering
- DrawCalls: < 1500 (PC) / < 600 (Mobile)
- Triangles: < 5M (PC) / < 1M (Mobile)
```

#### 4.2 Memory (메모리 예산)

```
memreport -full
- Total: < 4GB (PC) / < 2GB (Mobile) — 플랫폼 별 다름
- Texture: < 800MB (PC) / < 200MB (Mobile)
- Mesh: < 600MB
- Audio: < 100MB
- Animation: < 200MB
- Particle: < 100MB
```

#### 4.3 Network (멀티플레이)

```
stat net
- 전송: < 8 KB/s (per Player) — 표준 캐릭터
- 수신: < 16 KB/s
- ServerMove RPC: 33Hz (Player) / 5Hz (AI)

DOREPLIFETIME 검증:
- 모든 Replicated 멤버 = GetLifetimeReplicatedProps 등록?
- OnRep_* 콜백 = TRACE_CPUPROFILER_EVENT_SCOPE?
```

#### 4.4 Maintainability (유지보수성)

```
- Code Coverage: 단위 테스트 (선택)
- Documentation: SKILL.md 갱신 / cross-link 정확?
- Naming: Epic 표준 (U/A/F/I/E 접두사)?
- File Length: SKILL.md < 30KB / .cpp < 1500 라인?
```

### Stage 5 — Edge Case 매트릭스

| 케이스 | 검증 |
|--------|------|
| **Mobile (Mobile Forward)** | r.Mobile=1 + 빌드 + 런타임 |
| **Mobile (Mobile Deferred 5.x)** | r.Mobile.SupportDeferredShading=1 |
| **VR (OpenXR)** | VR 모드 + 양안 렌더 + Foveated Rendering |
| **Switch / Console** | Console 빌드 + 메모리 한계 |
| **Lumen 비활성** | r.DynamicGlobalIlluminationMethod=0 |
| **Nanite 비활성** | r.Nanite=0 |
| **저사양** | Scalability 0 (Low) |
| **Network — Lag** | NetEmulation 200ms |
| **Network — PacketLoss** | NetEmulation 5% loss |
| **Couch Co-op (2 Player)** | Player2 Gamepad 분리 |

### Stage 6 — Replicated 정합성 검사

```cpp
// 멀티플레이 코드 의무 검증
✅ bReplicates = true 인 Actor:
  - GetLifetimeReplicatedProps override 의무
  - 모든 UPROPERTY(Replicated) 멤버 등록
  - OnRep_* 함수 = UFUNCTION() 의무

✅ Server / Client RPC:
  - Server RPC = WithValidation + _Validate 의무
  - Client RPC = bReplicates = true 의무
  - NetMulticast = 사용 신중

✅ 권한 검사:
  - HasAuthority() / GetLocalRole() 일관 사용
  - Server 만 변경 = HasAuthority() 가드
```

### Stage 7 — GC 누수 검사

```
1. Editor 안에서 obj list class=AYourActor 실행
   - Spawn / Destroy 후 Count 0 으로 복귀?

2. Memreport -full
   - Spawn / Destroy 사이클 후 메모리 증가?

3. obj refs Class=YourClass
   - 어떤 객체가 참조 보유?
   - TObjectPtr / TWeakObjectPtr / 구조체 / Subsystem?

4. GC 강제 실행:
   - obj gc

5. 의심 사항:
   - TStrongObjectPtr 사용처 — 명시적 Reset?
   - FGCObject 자손 — AddReferencedObjects 정확?
   - Subsystem 참조 — Map 전환 시 정리?
```

### Stage 8 — 외부 검증 (사용자 의무)

> **Claude 가 못 하는 검증 — 사용자 / QA 가 의무**:

```
□ 실제 게임패드 / VR / Mobile 디바이스 테스트
□ 실제 멀티플레이 (Listen Server + 2 Client)
□ Cooked Build Shipping 패키징 + 디바이스 설치
□ QA 시나리오 테스트
□ 디자이너 협업 (BP 자식 / 자산 변경)
□ Production 환경 시뮬 (Replication / 메모리 한계)
□ 출시 후 Telemetry 수집 + 분석
```

---

## 2. Evaluator 보고서 표준 (Output)

### 2.1 보고서 구조

```markdown
# Evaluator Report — {작업명} ({날짜})

## 평가 요약
- 종합 점수: X / 100
- Critical 이슈: N개
- Major 이슈: N개
- Minor 이슈: N개
- 권장: 통과 / 수정 필요 / 거부

## §1. 정책 위반 (Stage 1 결과)
| 정책 | 결과 | 위반 위치 |
|------|------|---------|
| 6대 정책 | ✅ / ⚠️ / ❌ | (이슈 위치) |
| 어셋 로드 | ... | ... |
| ... | ... | ... |

## §2. 컴파일 결과 (Stage 2)
- Development Editor: ✅ / ❌ + 에러 로그
- Cooked Development: ✅ / ❌
- Cooked Shipping: ✅ / ❌

## §3. 런타임 결과 (Stage 3)
| 단계 | 결과 | 비고 |
|------|------|------|
| Editor PIE | ✅ | 정상 |
| Standalone | ✅ | 정상 |
| Cooked Development | ⚠️ | 첫 Spawn 200ms 히칭 |
| Cooked Shipping | ❌ | Crash — UInputAction nullptr |

## §4. 성능 측정 (Stage 4)
| 기준 | 측정 | 목표 | 결과 |
|------|------|------|------|
| Frame Time | 22ms | 16.67ms | ❌ 30fps 떨어짐 |
| Memory (Total) | 4.2GB | 4GB | ⚠️ 초과 |
| ... | ... | ... | ... |

## §5. Edge Case (Stage 5)
- Mobile: ❌ Compile 실패
- VR: ✅ 정상
- ... 

## §6-8. 추가 검증
- Replicated 정합성: ✅
- GC 누수: ✅ 없음
- 외부 검증 의무: ⚠️ Cooked Shipping 미검증

## 권장 수정
1. **Critical** — UInputAction nullptr 가드 추가 (P0)
2. **Major** — Mobile 호환성 (P1)
3. **Minor** — SKILL.md cross-link 추가 (P3)
```

### 2.2 점수 계산

| 영역 | 가중치 | 만점 |
|------|-------|------|
| 정책 위반 | 30% | 30 |
| 컴파일 (Cooked 포함) | 20% | 20 |
| 런타임 동작 | 20% | 20 |
| 성능 4기준 | 20% | 20 |
| Edge Case | 10% | 10 |
| **합계** | 100% | **100** |

| 점수 | 권장 |
|------|------|
| 90+ | 통과 (Production 준비) |
| 70-89 | 통과 — Minor 수정 후 |
| 50-69 | 수정 필요 — Major 이슈 해결 |
| < 50 | 거부 — 재작성 또는 큰 재구조화 |

---

## 3. 멀티 Claude 협업 패턴 (글 1 핵심)

### 3.1 표준 흐름

```
Session A (Generator):
  1. Wiki Read → Sprint Contract 작성 (<외부>/{날짜}_*_generator.md)
  2. 코드 작성
  3. Decision Log 기록
  4. Session 종료 → 사용자에게 _handoff 파일 전달

Session B (Evaluator — 별도 Claude 인스턴스):
  1. _handoff_*_generator.md Read
  2. 본 문서 (15_EvaluatorRecipe) 표준 적용
  3. Stage 1-7 자동 검사
  4. Stage 8 (외부 검증) — 사용자 의무 명시
  5. Evaluator Report 작성 (<외부>/{날짜}_*_evaluator.md)
  6. 사용자에게 발견 사항 보고

Session C (Generator — 수정 Pass):
  1. _handoff_*_evaluator.md Read
  2. Critical / Major 이슈 수정
  3. <외부>/{날짜}_*_v2.md 작성
  4. 사용자에게 보고

(반복 — Approval 까지)
```

### 3.2 사용자 (Human Evaluator) 역할

```
Stage 8 의무:
  - 실제 빌드 (Cooked Shipping)
  - 디바이스 테스트 (Mobile / VR / Console)
  - 멀티플레이 실 검증
  - QA 시나리오 통과
  - Production Telemetry 분석
  
사용자 Approval 후만 Production 배포
```

---

## 4. 안티패턴 (Evaluator 가 빠지지 말 것)

| # | 안티패턴 | 정답 |
|---|---------|------|
| 1 | "이 정도면 통과" 안일한 평가 | 회의적 마인드셋 (§0.1) 의무 |
| 2 | Generator 가 자기 평가 | 별도 Claude 인스턴스 또는 사용자 |
| 3 | Stage 1 (정적) 만 통과 → 통과 처리 | Stage 2 (Cooked Build) 까지 의무 |
| 4 | "Cooked Build 검증 의무" 적기만 함 | 실제 빌드 + 결과 첨부 |
| 5 | Edge Case 무시 (Mobile / VR) | Stage 5 매트릭스 의무 |
| 6 | 점수만 부여 + 권장 수정 안 함 | 우선순위별 수정 사항 명시 |
| 7 | "Minor 만" 이슈로 분류 — Major 회피 | 심각도 기준 엄격 (14_TaskHandoff §4.1) |
| 8 | 외부 검증 의무 명시 안 함 | Stage 8 (사용자 의무) 명시 |

---

## 5. 관련 문서

- 🚨 [`14_TaskHandoffTemplate.md`](./14_TaskHandoffTemplate.md) — Handoff 표준 (§4 Evaluator Findings 페어)
- 🎯 [`16_PolicyPriority.md`](./16_PolicyPriority.md) — 정책 충돌 해결 (Evaluator 가 충돌 발견 시)
- 🚨 [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) — Stage 1 §5 검증
- 🚨 [`09_GlobalIteratorPolicy.md`](./09_GlobalIteratorPolicy.md) — Stage 1 §6 검증
- 🚨 [`10_ComponentPolicies.md`](./10_ComponentPolicies.md) — Stage 1 §1 검증
- 🚨 [`11_AssetLoadingPolicy.md`](./11_AssetLoadingPolicy.md) — Stage 1 §2 검증
- 🎯 [`12_AssetOptimizationPolicy.md`](./12_AssetOptimizationPolicy.md) — Stage 1 §3 검증
- 🚨 `Input/SKILL.md` — Stage 1 §4 검증

---

## 6. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **Anthropic harness-design 글 1** 의 "Generator + Evaluator 분리" 패턴 LLM_Wiki 적용. **8단 평가 표준** (정책 위반 자동 검사 / 컴파일 / 런타임 / 성능 / Edge Case / Replicated 정합성 / GC 누수 / 외부 검증) + **4기준 + 가중치** (Performance 20% + Memory + Network + Maintainability) + Evaluator Report 표준 + 점수 계산 + **멀티 Claude 협업 패턴** (Generator/Evaluator/사용자 3단 + 반복 흐름) + 안티패턴 8종. |
