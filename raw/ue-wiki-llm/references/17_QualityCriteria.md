---
name: quality-criteria
description: UE 코드 품질 4기준 (Performance / Memory / Network / Maintainability) + 측정 채널 (stat unit / Memreport / Profiler / Insights) + few-shot 캘리브레이션. 글 1 의 "주관적 품질의 채점 가능화" 적용. Tier 4 정책의 측정 표준.
---

# 17. Quality Criteria — 측정 가능한 코드 품질 기준

> 본 문서는 **글 1 (harness-design) 의 "주관적 품질의 채점 가능화"** 적용. UE 코드 품질을 4기준으로 분류 + 각 기준의 측정 채널 + few-shot 예시.
>
> **요지**: "이 코드는 좋다" 는 주관적 — **측정 가능한 4기준 + 정량 임계값** 으로 변환.

---

## 0. 4기준 (Performance / Memory / Network / Maintainability)

### 0.1 글 1 의 4기준 → UE 적용

| 글 1 기준 | UE 기준 | 측정 채널 |
|----------|---------|---------|
| Design quality | **Maintainability** | 정적 분석 + Code Review |
| Originality | (UE = Idiomatic 추구) | UE 표준 준수 |
| Craft | **Performance** + **Memory** + **Network** | stat unit / memreport / stat net |
| Functionality | (Tier 1-3 정책 — 16_PolicyPriority) | 빌드 + 런타임 검증 |

### 0.2 가중치 매트릭스

| 기준 | 가중치 | 만점 | 측정 도구 |
|------|-------|------|---------|
| **Performance** | 35% | 35 | stat unit / profilegpu |
| **Memory** | 25% | 25 | memreport / obj refs |
| **Network** | 15% | 15 | stat net / NetEmulation |
| **Maintainability** | 25% | 25 | 정적 분석 + Code Review |
| **합계** | 100% | **100** | |

> **Production 통과 기준 = 80+** (Tier 1-3 정책 전부 만족 + Quality 80+).

---

## 1. Performance (35%) — 60fps 유지

### 1.1 임계값 매트릭스

| 플랫폼 | 목표 FPS | Frame Time | Game | Draw | GPU |
|--------|---------|-----------|------|------|------|
| **PC High-End** | 60 | < 16.67ms | < 8ms | < 5ms | < 8ms |
| **PC Mid-Range** | 60 | < 16.67ms | < 10ms | < 6ms | < 12ms |
| **PC Low / Console** | 30 | < 33.33ms | < 16ms | < 10ms | < 18ms |
| **Mobile (High)** | 30 | < 33.33ms | < 18ms | < 10ms | < 20ms |
| **Mobile (Low)** | 30 | < 33.33ms | < 20ms | < 12ms | < 22ms |
| **VR (90fps)** | 90 | < 11.1ms | < 5ms | < 4ms | < 6ms |

### 1.2 측정 명령어

```cpp
// Editor / Cooked Build 콘솔
stat unit                  // Frame / Game / Draw / GPU 시간
stat fps                    // FPS + Frame Time
stat scenerendering         // 렌더 통계
stat gpu                    // GPU 단계별
profilegpu                  // 1프레임 GPU 프로파일 (CSV)
profile cpu start ~ profile cpu stop  // CPU 프로파일

// 핵심 stat
stat slate                  // UMG / Slate
stat anim                   // SkeletalMesh Animation
stat input                  // 입력 처리
stat physics                // Physics
stat audio                  // Audio
stat ai                     // AI / BehaviorTree
stat foliage                // Foliage / HISM
stat lighting               // Lighting
```

### 1.3 점수 계산 (35점)

| 측정 | 만점 |
|------|------|
| Frame Time 임계값 | 15 |
| Game Thread | 5 |
| Draw Thread | 5 |
| GPU | 5 |
| DrawCalls (< 1500 PC / < 600 Mobile) | 3 |
| Triangles (< 5M PC / < 1M Mobile) | 2 |

### 1.4 few-shot 예시

#### Good (35점)
```
stat unit:
  Frame: 14.2ms (60fps)
  Game: 6.8ms
  Draw: 3.5ms
  GPU: 7.2ms

stat scenerendering:
  DrawCalls: 850
  Triangles: 2.3M

→ 35/35 (모든 임계값 만족)
```

#### Bad (15점)
```
stat unit:
  Frame: 22.5ms (44fps) ← 30fps 떨어지는 PC ✗
  Game: 14.5ms ← 임계값 8ms 초과
  Draw: 4.2ms (OK)
  GPU: 12.1ms ← 임계값 8ms 초과

stat scenerendering:
  DrawCalls: 2200 ← 임계값 1500 초과
  Triangles: 7.1M ← 임계값 5M 초과

→ 15/35 (다수 임계값 미달 — 최적화 필요)
```

### 1.5 정책 cross-link

- 12_AssetOptimizationPolicy §6 — 다수 NPC 통합 매트릭스
- 09_GlobalIteratorPolicy — TActorIterator 금지
- 10_ComponentPolicies §5 — PrimaryComponentTick = false

---

## 2. Memory (25%) — 메모리 한계 + 누수 방지

### 2.1 임계값 매트릭스

| 플랫폼 | Total | Texture | Mesh | Audio | Animation |
|--------|-------|---------|------|-------|-----------|
| **PC High** | 8GB | 2GB | 1.5GB | 200MB | 500MB |
| **PC Mid** | 4GB | 1GB | 800MB | 150MB | 300MB |
| **Console (PS5)** | 12.5GB | 3GB | 2GB | 250MB | 500MB |
| **Mobile (High)** | 4GB | 600MB | 400MB | 80MB | 150MB |
| **Mobile (Low)** | 2GB | 300MB | 200MB | 50MB | 80MB |

### 2.2 측정 명령어

```cpp
// 메모리 측정
stat memory                 // 카테고리별 (~MEM_*)
memreport -full             // 풀 리포트 (txt 파일 출력)
obj list class=AYourActor   // 특정 클래스 인스턴스
obj refs Class=YourClass    // 참조 보유처 추적
obj gc                      // GC 강제 실행

// 메모리 추적 (시간별)
stat memoryallocator        // Allocator 별
listusedtextures            // 사용 중인 Texture
```

### 2.3 GC 누수 검사

```cpp
// 의심 시나리오:
1. Spawn 100개 → Destroy → obj list class=AYourActor → 0?
2. Map 전환 → memreport → 이전 Map 자산 unload?
3. TStrongObjectPtr 사용처 = 명시적 Reset?
4. FGCObject 자손 = AddReferencedObjects 정확?
5. Subsystem 멤버 = Map 전환 시 정리?
```

### 2.4 점수 계산 (25점)

| 측정 | 만점 |
|------|------|
| Total 메모리 임계값 | 10 |
| 카테고리별 (Texture / Mesh / Audio / Anim) | 8 |
| GC 누수 없음 | 5 |
| Map 전환 시 메모리 정리 | 2 |

### 2.5 정책 cross-link

- 11_AssetLoadingPolicy — Soft Reference + Streaming
- 10_ComponentPolicies §3 — GC 방어
- 12_AssetOptimizationPolicy §3 — Actor Merging

---

## 3. Network (15%) — 멀티플레이 효율

### 3.1 임계값 (Player 1명 기준)

| 항목 | 표준 | 비고 |
|------|------|------|
| 전송 (Tx) | < 8 KB/s | per Player Character |
| 수신 (Rx) | < 16 KB/s | |
| Replicated 멤버 수 | < 30 per Actor | DOREPLIFETIME |
| RPC 호출 빈도 | < 33Hz (Player) / < 5Hz (AI) | |
| ServerMove RPC | 33Hz | CharacterMovement |
| RTT | < 200ms | Production |

### 3.2 측정 명령어

```cpp
stat net                    // 네트워크 통계
stat netserialization       // 직렬화 비용
stat charactermovement      // CMC 복제

// NetEmulation (Editor 시뮬)
NetEmulation.Lag 200        // 200ms Lag
NetEmulation.PacketLoss 5   // 5% 패킷 손실
NetEmulation.Jitter 50      // 50ms Jitter
```

### 3.3 점수 계산 (15점)

| 측정 | 만점 |
|------|------|
| Tx / Rx 임계값 | 5 |
| Replicated 정합성 (DOREPLIFETIME 등록 누락 0) | 4 |
| RPC 빈도 | 3 |
| Lag / PacketLoss 시뮬 통과 | 3 |

### 3.4 정책 cross-link

- 11_AssetLoadingPolicy — Replication 시 어셋 로드
- 10_ComponentPolicies — bReplicates 설정
- 15_EvaluatorRecipe Stage 6 — Replicated 정합성

---

## 4. Maintainability (25%) — 유지보수성

### 4.1 측정 항목

```
1. Naming (Epic 표준)
   - U/A/F/I/E 접두사 정확
   - SRP (한 클래스 = 한 역할)
   
2. File Organization
   - SKILL.md < 30KB (글 3 progressive disclosure)
   - 헤더 < 1000 라인
   - .cpp < 1500 라인
   
3. Documentation
   - 모든 public API = 주석
   - SKILL.md cross-link 정확
   - 정책 cross-link 의무
   
4. Code Quality
   - const 정확성
   - 헤더 최소 포함 (전방선언)
   - WITH_EDITOR 가드 정확 (05_EditorOnlyIndex)
   - TObjectPtr 사용 (Raw pointer X)
   
5. Test Coverage
   - 단위 테스트 (선택 — 5%)
   - 자동화 테스트 (선택 — 5%)
```

### 4.2 점수 계산 (25점)

| 측정 | 만점 |
|------|------|
| Naming + SRP | 5 |
| File Organization | 5 |
| Documentation | 5 |
| Code Quality | 5 |
| Cross-link 정확 | 3 |
| Test Coverage (선택) | 2 |

### 4.3 정책 cross-link

- 04_OverrideIndex — virtual + Super 호출
- 05_EditorOnlyIndex — WITH_EDITOR 가드
- 글 3 progressive disclosure — SKILL.md < 30KB

---

## 5. Few-shot 캘리브레이션 (글 1 패턴)

### 5.1 100점 만점 코드 예시

```cpp
// AMyOptimizedCharacter.cpp — Production 표준 (95+ 점)

// 1. Naming + SRP (Maintainability ✅)
// 2. WITH_EDITOR 가드 (Maintainability ✅)
// 3. UPROPERTY + TObjectPtr (Memory + Maintainability ✅)
// 4. Soft Reference + UAssetManager (Memory ✅)

UCLASS()
class AMyOptimizedCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    AMyOptimizedCharacter()
    {
        // Tier 1: bCanEverTick = false (Performance ✅)
        PrimaryActorTick.bCanEverTick = false;

        // Tier 2: GC 방어 — TObjectPtr (Memory ✅)
        Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
        // ...
    }

    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputAction> MoveAction;   // (Maintainability ✅)

    UPROPERTY(EditDefaultsOnly, Category="Asset", meta=(AssetBundles="Visual"))
    TSoftObjectPtr<USkeletalMesh> CharacterMesh;   // (Memory ✅)

    virtual void BeginPlay() override
    {
        Super::BeginPlay();   // (Tier 3: Super 호출 ✅)
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyChar::BeginPlay);   // (Performance ✅)

        // Significance 등록 (Performance ✅)
        if (auto* SigMgr = USignificanceManager::Get<USignificanceManager>(GetWorld()))
        {
            SigMgr->RegisterObject(this, ...);
        }
    }

    void OnMove(const FInputActionValue& Value)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyChar::OnMove);
        // ... (Performance + Maintainability ✅)
    }

    UFUNCTION(Server, Reliable, WithValidation)   // (Network ✅)
    void Server_Fire(FVector Direction);
};
```

→ **Performance: 33/35 / Memory: 24/25 / Network: 14/15 / Maintainability: 24/25 = 95/100**

### 5.2 50점 코드 예시 (수정 필요)

```cpp
// AMyBadCharacter.cpp — 다수 정책 위반 (50점 미만)

UCLASS()
class AMyBadCharacter : public ACharacter
{
public:
    AMyBadCharacter()
    {
        // ❌ Tier 1: bCanEverTick = true (Performance -5)
        PrimaryActorTick.bCanEverTick = true;

        // ❌ Tier 1: Constructor 안 LoadObject (Memory + Performance -10)
        Mesh = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/.../Mesh"));
    }

    // ❌ UPROPERTY 누락 — GC 방어 X (Memory -10)
    USkeletalMesh* Mesh;

    // ❌ Hard Reference (Memory -3)
    UPROPERTY()
    TObjectPtr<USkeletalMesh> AllWeapons[100];

    void Tick(float DT) override
    {
        // ❌ Super 호출 누락 (Tier 3 -5)
        // ❌ 프로파일링 스코프 누락 (Performance -3)
        for (TActorIterator<AEnemy> It(GetWorld()); It; ++It)   // ❌ TActorIterator (Performance -10)
        {
            // ...
        }
    }

    void OnMove()   // ❌ 시그니처 잘못 (Tier 3 -5)
    {
        // ❌ Move 에 Started 만 ETriggerEvent (Tier 3 -5)
    }
};
```

→ **Performance: 12/35 / Memory: 5/25 / Network: 5/15 / Maintainability: 10/25 = 32/100 — 거부**

---

## 6. 측정 자동화 (글 1 의 Playwright MCP 같은 외부 채널)

### 6.1 자동화 가능 항목

```bash
# 1. Build 검증 (Cooked)
RunUAT.bat BuildCookRun -project=... -platform=Win64 -clientconfig=Development -build -cook -package
→ 결과: Cook Error 0 / Package 정상 ✅

# 2. Static 분석
clang-tidy / cppcheck → Naming / const / 헤더 포함 검사

# 3. Memory 자동
memreport -full → 텍스트 파일 → 임계값 비교 스크립트

# 4. Insights 자동 캡처
"-trace=cpu,gpu,frame,memory" → .utrace 파일 → 분석 자동화
```

### 6.2 사용자 의무 (자동화 안 됨)

```
1. 실제 게임패드 / VR / Mobile 테스트
2. 실제 멀티플레이 (Listen Server + 2 Client)
3. QA 시나리오 통과
4. Production Telemetry 수집 + 분석
```

---

## 7. 점수 → 권장 결정

| 점수 | 권장 | 작업 |
|------|------|------|
| **90-100** | **통과** | Production 준비 |
| **80-89** | 통과 + Minor 수정 | 검토 후 머지 |
| **70-79** | 검토 필요 | Major 이슈 해결 |
| **50-69** | 수정 필요 | 큰 재작성 |
| **< 50** | 거부 | 처음부터 재작성 |

---

## 8. 안티패턴 (8종)

| # | 안티패턴 | 정답 |
|---|---------|------|
| 1 | "이 코드는 좋다" 주관적 평가 | 4기준 측정 + 점수 |
| 2 | Editor PIE 만 측정 + Cooked 안 함 | Cooked Development + Shipping 의무 |
| 3 | 한 플랫폼만 측정 | PC + Mobile + Console + VR (해당 시) |
| 4 | Performance 만 측정 + Memory / Network 무시 | 4기준 모두 |
| 5 | 자동화 가능 항목 수동 검증 | Build / Memreport / Insights 자동화 |
| 6 | 점수 기준 없이 "OK" 결정 | §7 권장 표준 적용 |
| 7 | Few-shot 예시 없이 평가 | §5 의 95점 / 32점 사례 비교 |
| 8 | Maintainability 가벼이 봄 (25%) | 5년 후 누가 본다는 가정 |

---

## 9. 관련 문서

- 🚨 [`15_EvaluatorRecipe.md`](./15_EvaluatorRecipe.md) — Stage 4 측정 (본 문서 기준 적용)
- 🎯 [`16_PolicyPriority.md`](./16_PolicyPriority.md) — Tier 4 정책 (본 문서 측정 채널)
- 모든 횡단 인덱스 (04~13) — 정책 위반 = 점수 감점

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 글 1 의 "주관적 품질 채점 가능화" 적용. **4기준** (Performance 35% / Memory 25% / Network 15% / Maintainability 25%) + 임계값 매트릭스 (PC / Mobile / Console / VR) + 측정 명령어 + 점수 계산 + **few-shot 캘리브레이션** (95점 vs 32점 사례) + 측정 자동화 (Build / Memreport / Insights) + 점수 → 권장 결정. |
