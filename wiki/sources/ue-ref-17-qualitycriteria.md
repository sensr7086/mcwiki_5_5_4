---
type: source
title: "UE refs — 17 QualityCriteria (4 기준 100점 📊)"
slug: ue-ref-17-qualitycriteria
source_path: raw/ue-wiki-llm/references/17_QualityCriteria.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, quality, measurement]
---

# UE refs — 17 QualityCriteria 📊

> Source: [[raw/ue-wiki-llm/references/17_QualityCriteria.md]] · Anthropic Article 1 의 *주관적 품질의 채점 가능화* UE vault 적용

## 1. Summary

"이 코드는 좋다" = 주관적 → **측정 가능한 4 기준 + 정량 임계값** 으로 변환. Performance 35% + Memory 25% + Network 15% + Maintainability 25% = 100점. 플랫폼별 임계 매트릭스 (PC High/Mid/Low / Console / Mobile / VR 90fps). vault [[00_meta/00_QualityCriteria]] 의 UE 특화 정밀판. CLAUDE.md §0.1.2 매핑.

## 2. 4 기준 가중치 매트릭스 🟢

| 기준 | 가중치 | 만점 | 측정 도구 |
| -- | -- | -- | -- |
| **Performance** | 35% | 35 | `stat unit` / `profilegpu` |
| **Memory** | 25% | 25 | `memreport` / `obj refs` |
| **Network** | 15% | 15 | `stat net` / NetEmulation |
| **Maintainability** | 25% | 25 | 정적 분석 + Code Review |
| **합계** | 100% | **100** | |

**Production 통과 기준 = 80+** (Tier 1-3 정책 전부 만족 + Quality 80+).

## 3. Performance (35%) — 60fps 유지

### 3.1. 플랫폼별 임계 매트릭스 🟢

| 플랫폼 | 목표 FPS | Frame | Game | Draw | GPU |
| -- | -- | -- | -- | -- | -- |
| **PC High-End** | 60 | < 16.67ms | < 8ms | < 5ms | < 8ms |
| **PC Mid-Range** | 60 | < 16.67ms | < 10ms | < 6ms | < 12ms |
| **PC Low / Console** | 30 | < 33.33ms | < 16ms | < 10ms | < 18ms |
| **Mobile (High)** | 30 | < 33.33ms | < 18ms | < 10ms | < 20ms |
| **Mobile (Low)** | 30 | < 33.33ms | < 20ms | < 12ms | < 22ms |
| **VR (90fps)** | 90 | < 11.1ms | < 5ms | < 4ms | < 6ms |

### 3.2. 측정 명령어

```cpp
// Editor / Cooked Build 콘솔
stat unit / stat fps               // Frame / Game / Draw / GPU
stat scenerendering                // DrawCalls / Triangles
stat gpu / profilegpu              // GPU 단계별 / 1프레임 프로파일
stat slate / stat anim / stat input / stat physics / stat audio / stat ai
```

### 3.3. 점수 계산 (35점)

| 측정 | 만점 |
| -- | -- |
| Frame Time 임계값 | 15 |
| Game Thread | 5 |
| Draw Thread | 5 |
| GPU | 5 |
| DrawCalls (< 1500 PC / < 600 Mobile) | 3 |
| Triangles (< 5M PC / < 1M Mobile) | 2 |

### 3.4. 정책 cross-link

[[sources/ue-ref-12-assetoptimizationpolicy]] §6 (다수 NPC 매트릭스) · [[sources/ue-ref-09-globaliteratorpolicy]] (TActorIterator 금지) · [[sources/ue-ref-10-componentpolicies]] §5 (PrimaryComponentTick).

## 4. Memory (25%) — 메모리 한계 + 누수 방지

### 4.1. 플랫폼별 임계 매트릭스 🟢

| 플랫폼 | Total | Texture | Mesh | Audio | Animation |
| -- | -- | -- | -- | -- | -- |
| **PC High** | 8GB | 2GB | 1.5GB | 200MB | 500MB |
| **PC Mid** | 4GB | 1GB | 800MB | 150MB | 300MB |
| **Console (PS5)** | 12.5GB | 3GB | 2GB | 250MB | 500MB |
| **Mobile (High)** | 4GB | 600MB | 400MB | 80MB | 150MB |
| **Mobile (Low)** | 2GB | 300MB | 200MB | 50MB | 80MB |

### 4.2. 측정 명령어

```cpp
stat memory / memreport -full      // 카테고리별 + 풀 리포트
obj list class=AYourActor          // 특정 클래스 인스턴스
obj refs Class=YourClass           // 참조 보유처
obj gc                              // GC 강제
listusedtextures                    // 사용 중 Texture
```

### 4.3. GC 누수 검사 시나리오

```
1. Spawn 100 → Destroy → obj list 0 복귀?
2. Map 전환 → memreport → 이전 자산 unload?
3. TStrongObjectPtr 사용처 = 명시 Reset?
4. FGCObject 자손 = AddReferencedObjects 정확?
5. Subsystem 멤버 = Map 전환 시 정리?
```

### 4.4. 점수 계산 (25점)

| 측정 | 만점 |
| -- | -- |
| Total 메모리 임계 | 10 |
| 카테고리별 (Texture/Mesh/Audio/Anim) | 8 |
| GC 누수 없음 | 5 |
| Map 전환 시 메모리 정리 | 2 |

### 4.5. 정책 cross-link

[[sources/ue-ref-11-assetloadingpolicy]] (Soft Reference + Streaming) · [[sources/ue-ref-10-componentpolicies]] §3 (GC 방어) · [[sources/ue-ref-12-assetoptimizationpolicy]] §3 (Actor Merging).

## 5. Network (15%) — 멀티플레이 효율

### 5.1. 임계 (Player 1명 기준)

| 항목 | 표준 |
| -- | -- |
| 전송 (Tx) | < 8 KB/s per Player |
| 수신 (Rx) | < 16 KB/s |
| Replicated 멤버 수 | < 30 per Actor |
| RPC 호출 | < 33Hz (Player) / < 5Hz (AI) |
| ServerMove RPC | 33Hz (CMC) |
| RTT | < 200ms |

### 5.2. 측정 + 시뮬

```cpp
stat net / stat netserialization / stat charactermovement

// NetEmulation (Editor)
NetEmulation.Lag 200          // 200ms Lag
NetEmulation.PacketLoss 5     // 5% 손실
NetEmulation.Jitter 50        // 50ms Jitter
```

### 5.3. 점수 계산 (15점)

| 측정 | 만점 |
| -- | -- |
| Tx / Rx 임계값 | 5 |
| Replicated 정합성 (DOREPLIFETIME 누락 0) | 4 |
| RPC 빈도 | 3 |
| Lag / PacketLoss 시뮬 통과 | 3 |

## 6. Maintainability (25%) — 유지보수성

### 6.1. 측정 항목 매트릭스

| # | 항목 | 기준 |
| -- | -- | -- |
| 1 | Naming (Epic 표준) | U/A/F/I/E 접두사 + SRP |
| 2 | File Organization | SKILL.md < 30KB / 헤더 < 1000라인 / .cpp < 1500라인 |
| 3 | Documentation | public API 주석 + SKILL.md cross-link |
| 4 | Code Quality | const 정확 / 헤더 최소 + 전방선언 / WITH_EDITOR 가드 / TObjectPtr |
| 5 | Test Coverage (선택) | 단위 테스트 / 자동화 |

### 6.2. 점수 계산 (25점)

| 측정 | 만점 |
| -- | -- |
| Naming + SRP | 5 |
| File Organization | 5 |
| Documentation | 5 |
| Code Quality | 5 |
| Cross-link 정확 | 3 |
| Test Coverage (선택) | 2 |

### 6.3. 정책 cross-link

[[sources/ue-ref-04-overrideindex]] (Super 호출) · [[sources/ue-ref-05-editoronlyindex]] (WITH_EDITOR 가드) · progressive disclosure (SKILL.md < 30KB).

## 7. ⭐ Few-shot 캘리브레이션 (Article 1 패턴) 🟢

### 7.1. Good (95점) — Production 표준

```cpp
UCLASS()
class AMyOptimizedCharacter : public ACharacter
{
public:
    AMyOptimizedCharacter()
    {
        PrimaryActorTick.bCanEverTick = false;         // Tier 1 ✅ Performance
        Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));  // Tier 2 ✅
    }

    UPROPERTY(EditDefaultsOnly, Category="Asset", meta=(AssetBundles="Visual"))
    TSoftObjectPtr<USkeletalMesh> CharacterMesh;       // Memory ✅

    virtual void BeginPlay() override
    {
        Super::BeginPlay();                            // Tier 3 ✅
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyChar::BeginPlay);  // Performance ✅
    }

    UFUNCTION(Server, Reliable, WithValidation)        // Network ✅
    void Server_Fire(FVector Direction);
};
```

→ Performance 33 / Memory 24 / Network 14 / Maintainability 24 = **95/100**

### 7.2. Bad (32점) — 거부 사례

```cpp
UCLASS()
class AMyBadCharacter : public ACharacter
{
    AMyBadCharacter()
    {
        PrimaryActorTick.bCanEverTick = true;          // ❌ Performance -5
        Mesh = LoadObject<USkeletalMesh>(nullptr, ...); // ❌ Tier 1 + Memory -10
    }
    USkeletalMesh* Mesh;                                // ❌ UPROPERTY 누락 — GC -10
    UPROPERTY() TObjectPtr<USkeletalMesh> AllWeapons[100];  // ❌ Hard ref -3

    void Tick(float DT) override
    {
        // ❌ Super 누락 / 스코프 누락
        for (TActorIterator<AEnemy> It(GetWorld()); It; ++It) {}  // ❌ -10
    }
};
```

→ Performance 12 / Memory 5 / Network 5 / Maintainability 10 = **32/100 — 거부**

## 8. 점수 → 권장 결정 🟢

| 점수 | 권장 | 작업 |
| -- | -- | -- |
| **90-100** | **통과** | Production 준비 |
| **80-89** | 통과 + Minor 수정 | 검토 후 머지 |
| **70-79** | 검토 필요 | Major 이슈 해결 |
| **50-69** | 수정 필요 | 큰 재작성 |
| **< 50** | **거부** | 처음부터 재작성 |

## 9. 측정 자동화 vs 사용자 의무

### 9.1. 자동화 가능

```bash
# 1. Build 검증
RunUAT.bat BuildCookRun -project=... -clientconfig=Development -build -cook -package

# 2. Static 분석
clang-tidy / cppcheck → Naming / const / 헤더 검사

# 3. Memory 자동
memreport -full → 텍스트 → 임계값 비교 스크립트

# 4. Insights 자동 캡처
-trace=cpu,gpu,frame,memory → .utrace → 분석
```

### 9.2. 사용자 의무 (자동화 X)

- 실제 게임패드 / VR / Mobile 디바이스
- 실제 멀티플레이 (Listen Server + 2 Client)
- QA 시나리오
- Production Telemetry

## 10. 안티패턴 (8대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | "이 코드는 좋다" 주관적 평가 | 4 기준 측정 + 점수 |
| 2 | Editor PIE 만 측정 + Cooked X | Cooked Development + Shipping |
| 3 | 한 플랫폼만 측정 | PC + Mobile + Console + VR (해당 시) |
| 4 | Performance 만 측정 + Memory/Network 무시 | 4 기준 모두 |
| 5 | 자동화 가능 항목 수동 검증 | Build / Memreport / Insights 자동화 |
| 6 | 점수 기준 없이 "OK" 결정 | §8 권장 표준 |
| 7 | Few-shot 예시 없이 평가 | §7 의 95점 / 32점 사례 비교 |
| 8 | Maintainability 가벼이 봄 (25%) | 5년 후 누가 본다는 가정 |

## 11. Cross-link

- 자매 governance hub: 📋 [[sources/ue-ref-14-taskhandofftemplate]] · 🔍 [[sources/ue-ref-15-evaluatorrecipe]] (Stage 4 측정 — 본 페이지 기준) · ⚖ [[sources/ue-ref-16-policypriority]] (Tier 4 측정 채널) · 🕰 [[sources/ue-ref-18-modelevolutionaudit]] (정책 stale 감사)
- vault meta: [[00_meta/00_QualityCriteria]] (vault 일반판)
- 모든 횡단 인덱스 (04-13) — 정책 위반 = 점수 감점
- KMCProject 측정: [[sources/ue-measure-summary]] · [[sources/ue-measure-instancedsubobject-2026-05-12]] ⭐⭐
