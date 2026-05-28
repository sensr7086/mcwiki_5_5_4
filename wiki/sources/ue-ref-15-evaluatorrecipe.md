---
type: source
title: "UE refs — 15 EvaluatorRecipe (8단계 회의적 평가 🔍)"
slug: ue-ref-15-evaluatorrecipe
source_path: raw/ue-wiki-llm/references/15_EvaluatorRecipe.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, evaluator, generator-evaluator-split]
---

# UE refs — 15 EvaluatorRecipe 🔍

> Source: [[raw/ue-wiki-llm/references/15_EvaluatorRecipe.md]] · Anthropic harness-design Article 1 의 *Generator + Evaluator 분리* 패턴 UE vault 적용

## 1. Summary

다른 Claude 인스턴스 / 사용자가 **코드 리뷰어 (Evaluator)** 역할 시 사용하는 회의적 평가 표준. **자기 평가 편향** (Generator 가 자기 결과 평가 시 무비판적 칭찬) 회피. 8단계 평가 (정책 위반 / 컴파일 / 런타임 / 성능 / Edge case / Replicated 정합성 / GC 누수 / 외부 검증) + 4기준 100점 채점. vault [[00_meta/03_EvaluatorRecipe]] 의 UE 특화 정밀판. CLAUDE.md §0.1.2 매핑.

## 2. 평가자의 마인드셋 🟢

| Generator | Evaluator (의무) |
| -- | -- |
| "이 코드는 정책 따랐다" | **"어떤 함정을 못 봤나?"** |
| "이 정도면 충분" | **"Cooked Build 에서 깨질 수 있나?"** |
| "테스트 안 해도 동작할 것" | **"5년 후 다른 사람이 이 코드 보면?"** |
| (Naïve 칭찬) | **"정책 충돌 가능?"** |
| | **"Edge case 모두 검토됐나?"** |

## 3. 평가 시점 매트릭스

| 시점 | 적합한 Evaluator |
| -- | -- |
| Sub-skill 작성 후 | 다른 Claude 인스턴스 (별도 세션) |
| 코드 작성 후 | 사용자 (UE 개발자 — 직접 빌드 가능) |
| 큰 작업 (3+ 단계) 종료 | 두 단계 — Claude 평가 → 사용자 검증 |
| Production 직전 | 사용자 (외부 검증 필수) |

## 4. ⭐ 8단계 평가 표준

### Stage 1 — 정책 위반 자동 검사 (Static)

| § | 정책 | vault 페이지 |
| -- | -- | -- |
| 1 | 6대 정책 (Mobility / NewObject / GC / GetOwner / Tick / CDO) | [[sources/ue-ref-10-componentpolicies]] |
| 2 | 어셋 로드 (Constructor 금지 / Soft vs Hard / Pin) | [[sources/ue-ref-11-assetloadingpolicy]] |
| 3 | 어셋 최적화 (Bone LOD / ScreenSize / Audio Cull / Niagara) | [[sources/ue-ref-12-assetoptimizationpolicy]] |
| 4 | Input (Enhanced Input / DefaultInput.ini / ETriggerEvent) | [[sources/ue-input-skill]] |
| 5 | 프로파일링 스코프 (Tick / Timer / 람다 / OnRep_*) | [[sources/ue-ref-07-profilingscopeRule]] |
| 6 | 전역 이터레이터 (TActorIterator 금지) | [[sources/ue-ref-09-globaliteratorpolicy]] |
| 7 | Override 규약 (Super 호출 위치) | [[sources/ue-ref-04-overrideindex]] |

### Stage 2 — 컴파일 검증 (의무)

```bash
# Development Editor
"<UE>/Engine/Build/BatchFiles/Build.bat" <Project>Editor Win64 Development -Project="<.uproject>"
# 결과: 0 Error, 0 Warning 표준

# Cooked Build (Development) — Article 1 핵심
"<UE>/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun -project="<.uproject>" \
  -platform=Win64 -clientconfig=Development -build -cook -package

# Cooked Build (Shipping) — Production 의무
... -clientconfig=Shipping ...
```

### Stage 3 — 런타임 검증 (단계별)

| 단계 | 명령 | 검증 |
| -- | -- | -- |
| 1 | Editor PIE | 컴파일 통과 / 즉시 동작 |
| 2 | Standalone Game (`-game`) | Editor 캐시 없이 동작 |
| 3 | **Cooked Development** | **Article 1 핵심 — Editor PIE 와 다름** |
| 4 | Cooked Shipping | 최종 Production |

콘솔: `stat unit` / `stat fps` / `stat memory` / `stat scenerendering` / `memreport -full` / `profilegpu` / `showflag.X`.

### Stage 4 — 성능 측정 (4기준)

| 기준 | 목표 | 채널 |
| -- | -- | -- |
| **Performance** | Frame < 16.67ms (60fps) / Game < 8ms / Draw < 5ms / GPU < 8ms | `stat unit` / `stat scenerendering` (DrawCalls < 1500 PC / < 600 Mobile) |
| **Memory** | Total < 4GB PC / < 2GB Mobile · Texture < 800MB / < 200MB | `memreport -full` |
| **Network** | < 8 KB/s 전송 / < 16 KB/s 수신 (per Player) · ServerMove 33Hz (Player) / 5Hz (AI) | `stat net` · DOREPLIFETIME 검증 |
| **Maintainability** | Naming (U/A/F/I/E) · SKILL.md < 30KB · cpp < 1500 라인 · Doc / cross-link | 정적 검사 |

자세히 → [[sources/ue-ref-17-qualitycriteria]] (4 가중 100점).

### Stage 5 — Edge Case 매트릭스

| 케이스 | 명령 |
| -- | -- |
| Mobile (Forward) | `r.Mobile=1` + 빌드 + 런타임 |
| Mobile (Deferred 5.x) | `r.Mobile.SupportDeferredShading=1` |
| VR (OpenXR) | VR 모드 + 양안 + Foveated Rendering |
| Switch / Console | Console 빌드 + 메모리 한계 |
| Lumen 비활성 | `r.DynamicGlobalIlluminationMethod=0` |
| Nanite 비활성 | `r.Nanite=0` |
| 저사양 | Scalability 0 (Low) |
| Network Lag | NetEmulation 200ms |
| Network Loss | NetEmulation 5% loss |
| Couch Co-op | Player2 Gamepad 분리 |

### Stage 6 — Replicated 정합성

| 검사 | 의무 |
| -- | -- |
| `bReplicates = true` Actor | `GetLifetimeReplicatedProps` override + 모든 `UPROPERTY(Replicated)` 등록 |
| OnRep_* 함수 | `UFUNCTION()` + 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| Server RPC | `WithValidation` + `_Validate` 의무 |
| Client RPC | `bReplicates = true` 의무 |
| NetMulticast | 사용 신중 (lag · bandwidth) |
| 권한 검사 | `HasAuthority()` / `GetLocalRole()` 일관 |

### Stage 7 — GC 누수 검사

```cpp
// 1. obj list class=AYourActor — Spawn/Destroy 후 Count 0 복귀?
// 2. memreport -full — Spawn/Destroy 사이클 후 메모리 증가?
// 3. obj refs Class=YourClass — 누가 참조?
// 4. obj gc — GC 강제 실행
// 5. 의심: TStrongObjectPtr Reset / FGCObject AddReferencedObjects / Subsystem 정리
```

### Stage 8 — 외부 검증 (사용자 의무)

Claude 가 못 하는 검증 — 사용자 / QA 가 의무:
- [ ] 실제 게임패드 / VR / Mobile 디바이스 테스트
- [ ] 실제 멀티플레이 (Listen Server + 2 Client)
- [ ] Cooked Build Shipping 패키징 + 디바이스 설치
- [ ] QA 시나리오 테스트
- [ ] 디자이너 협업 (BP 자식 / 자산 변경)
- [ ] Production Telemetry 분석

## 5. Evaluator 보고서 표준 🟢

### 5.1. 보고서 구조

```markdown
# Evaluator Report — {작업명} ({날짜})

## 평가 요약
- 종합 점수: X / 100
- Critical 이슈: N개 / Major: N개 / Minor: N개
- 권장: 통과 / 수정 필요 / 거부

## §1-7. Stage 결과 (각 단계 표)
## §8. 외부 검증 의무 (사용자)
## 권장 수정 (우선순위 P0~P3)
```

### 5.2. 점수 계산

| 영역 | 가중치 | 만점 |
| -- | -- | -- |
| 정책 위반 | 30% | 30 |
| 컴파일 (Cooked 포함) | 20% | 20 |
| 런타임 동작 | 20% | 20 |
| 성능 4기준 | 20% | 20 |
| Edge Case | 10% | 10 |
| **합계** | 100% | **100** |

| 점수 | 권장 |
| -- | -- |
| 90+ | 통과 (Production 준비) |
| 70-89 | 통과 — Minor 수정 후 |
| 50-69 | 수정 필요 — Major 이슈 해결 |
| < 50 | **거부** — 재작성 또는 큰 재구조화 |

## 6. 멀티 Claude 협업 패턴 (Article 1)

```
Session A (Generator):
  1. Wiki Read → Sprint Contract (<외부>/{날짜}_*_generator.md)
  2. 코드 작성 + Decision Log
  3. 종료 → 사용자에게 handoff

Session B (Evaluator — 별도 Claude):
  1. _generator.md Read
  2. 본 문서 Stage 1-7 자동 검사
  3. Stage 8 (외부 검증) — 사용자 의무 명시
  4. Evaluator Report (<외부>/{날짜}_*_evaluator.md)

Session C (Generator — 수정 Pass):
  1. _evaluator.md Read
  2. Critical / Major 수정
  3. <외부>/{날짜}_*_v2.md 작성
```

## 7. 안티패턴 (8대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | "이 정도면 통과" 안일한 평가 | 회의적 마인드셋 의무 |
| 2 | Generator 가 자기 평가 | 별도 Claude 또는 사용자 |
| 3 | Stage 1 (정적) 만 통과 → 통과 | Stage 2 (Cooked Build) 까지 의무 |
| 4 | "Cooked Build 검증 의무" 적기만 | 실제 빌드 + 결과 첨부 |
| 5 | Edge Case 무시 (Mobile / VR) | Stage 5 매트릭스 의무 |
| 6 | 점수만 + 권장 수정 안 함 | 우선순위별 수정 사항 명시 |
| 7 | Major 회피 — Minor 만 분류 | 심각도 기준 엄격 |
| 8 | 외부 검증 의무 명시 안 함 | Stage 8 (사용자) 명시 |

## 8. Cross-link

- 자매 governance hub: 📋 [[sources/ue-ref-14-taskhandofftemplate]] (§4 Evaluator Findings 페어) · ⚖ [[sources/ue-ref-16-policypriority]] (정책 충돌 해결) · 📊 [[sources/ue-ref-17-qualitycriteria]] (4 기준 100점 채점)
- Stage 1 정책 cross-link: 🚨 [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-04-overrideindex]]
- vault meta: [[00_meta/03_EvaluatorRecipe]] (vault 일반판) · [[00_meta/00_QualityCriteria]] · [[00_meta/01_PolicyPriority]] · [[00_meta/05_HandoffProtocol]]
- KMCProject 측 측정: [[sources/ue-measure-summary]] · [[sources/ue-measure-instancedsubobject-2026-05-12]] ⭐⭐ (외부 Claude 평가 사례)
