---
title: "LLM Assumption Hazard Family — UE 자동화 시 추측 함정 통합"
kind: synthesis
status: stable
tags: [synthesis, llm, claude, mcp, hazard-family, assumption, ue-574]
related_concepts:
  - "[[concepts/LLM-Visual-Reference-Hallucination]]"
  - "[[concepts/UE-Material-Pin-Name-Shortening]]"
  - "[[concepts/MCP-Tool-Schema-LLM-Friendly-Design]]"
  - "[[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]"
created: 2026-05-25
last_updated: 2026-05-25
---

# LLM Assumption Hazard Family — UE 자동화 시 추측 함정 통합

## 1. 정의

LLM (Claude / GPT 등) 이 UE Editor 자동화 (MCMaterialAuto 등) 수행 시, **명시적 정보 부재 / 도메인 prior / 학습 데이터 statistical bias** 로 인해 *실제 사용자 의도와 다른 결과* 를 생성하는 **추측 hazard 의 통합 family**. MMA-45 (단일 input 추측) / MMA-48 (Pin Name Shortening 추측) / MMA-50 (Visual Reference Hallucination) — 3 hazard 가 *동일 메커니즘* 의 변형.

핵심 원리: **LLM 은 *모르는 정보* 를 *그럴듯한 prior* 로 채움** → 사용자 입력에서 명시 부족 / 도구 응답에서 메타데이터 부족 / vision 입력 정밀도 한계 등 *정보 격차* 가 발생하면 추측으로 보강. 추측 정확도가 낮은 경우 silent failure (사용자 인지 못 함) 또는 brute-force retry.

## 2. 3 Hazard 비교 매트릭스

🟢 **VAULT** — MCMaterialAuto v0.21-v0.34 cycle 실측:

| Hazard | 원인 | LLM 의 추측 | 정확도 | Fix 채택 |
|---|---|---|---|---|
| **MMA-45** (단일 input dst_input) | tool valid_inputs 응답이 *property name* 만 (UE 축약 미반영) | "Input" → dst_input 으로 그대로 시도 → 실패 후 brute-force | 0% (모두 실패) | server 측 자동 정규화 (Pin Name Shortening) |
| **MMA-48** (Pin Name Shortening) | tool description 부족 — `ConnectMaterialExpressions` 의 내부 GetShortenPinName 매핑 비공개 | "Exponent" / "Coordinates" 등 9개 property name 그대로 전달 → 실패 | 0% (특정 9개에서) | server 측 자동 정규화 (caller 측 매핑) |
| **MMA-50** (Visual Reference Hallucination) | vision 인식 정밀도 한계 + 도메인 prior (PBR = ORM packing) | "ORM/ARM packing" 으로 *임의의 채널 분배* (예: T2.R→Metallic, T2.G→Specular, T2.B→Roughness, T2.A→AO) | ~30% (학습 prior 일치 시만) | (1) 명시 prompt / (2) ask_user_choice / (3) 메타데이터 자동 노출 |

### 공통 메커니즘 (3 hazard 동일)

```
LLM 입력 시점에 *정보 격차* 발생
    ↓ (격차 채움)
도메인 prior 또는 학습 데이터의 statistical bias 활용
    ↓
"그럴듯한 default 답" 생성 — 검증 없이 채택
    ↓ (검증 실패 시)
- silent failure (MMA-50): 사용자가 비교해야 발견
- explicit failure (MMA-45/48): tool 응답으로 실패 알림
    ↓ (LLM 의 다음 행동)
- brute-force retry (MMA-45/48): 다른 변형 시도
- uncertainty 표명 후 우회 (MMA-50): "ARM 가정인지 확인해주세요"
```

## 3. Vision 인식 실측 검증 (MMA-50 evidence)

🟢 **VAULT** — MCMaterialAuto run-20260525-145408.log 분석:

```log
[tool] Read(file_path)
[tool_result]
[claude] 머티리얼 그래프 이미지를 분석했습니다. 3개의 TextureSample 노드가
         BaseColor / Roughness(또는 ORM) / Normal 으로 연결된 표준 PBR 셋업이군요.
```

→ Claude Code 가 **`Read` tool 자동 호출** — image file path 받아서 *vision input 으로 변환*. 즉 vision 인식 *자체* 는 성공.

그러나 응답 안 "**Roughness(또는 ORM)**" — *세부 채널 매핑* 까지는 *정밀도 부족*. 결국 *학습 prior* (ORM packing) 채택.

**MMA-50 정확한 메커니즘 — 가설 정정**:
- ❌ 이전 가설: vision 인식 자체 실패 → text path 만 보고 추측
- ✅ 실측 결론: **vision 인식 성공** + *세부 매핑 정밀도 한계* → LLM prior 로 채움

이는 더 *fundamental hazard* — vision 인식 fix 만으로는 해결 안 됨. 메타데이터 / 사용자 확인 / 명시 prompt 모두 필요.

## 4. 회피 패턴 — 4 Layer Defense

🟢 **VAULT** — MCMaterialAuto v0.21-v0.34 누적 채택:

### Layer 1 — Server 측 자동 정규화 (가장 robust)

LLM 의 입력을 *변환 후* UE API 호출 → LLM 추측 무관하게 동작.

| 패턴 | 사례 |
|---|---|
| 식별자 양식 양쪽 허용 | `expression_class` short/full UClass name |
| Pin name 자동 축약 | `dst_input` GetShortenPinName 미러 (MMA-48) |
| SamplerType 자동 추론 | CompressionSettings + SRGB → EMaterialSamplerType |
| Multi-source ID resolver | local_id + GUID + path 통합 lookup |

### Layer 2 — Valid-list error response

실패 시 *정확한 valid 값 리스트* 반환 → LLM 이 다음 turn 에 정확한 입력. brute-force retry 회피.

```cpp
return MakeError(FString::Printf(
    TEXT("ConnectMaterialExpressions failed. Valid dst_input on %s: [%s].%s"),
    *DstClass, *Join(ValidInputs, TEXT(", ")), *Hint));
```

### Layer 3 — 메타데이터 자동 노출

tool 응답에 *추론 가능한 모든 메타데이터* 포함 → LLM 추측 회피.

| 도구 | 추가 메타데이터 |
|---|---|
| `read_material` | input_pins 배열 (all valid 이름) + is_single_input + input_count |
| `list_textures` | recommended_sampler_type + compression + srgb |

### Layer 4 — 사용자 확인 강제 (ambiguity 가 fundamental 인 경우)

vault [[concepts/MCP-Async-UI-Bridge-Pattern]] 의 `ask_user_choice` 활용 — LLM 이 ambiguous texture / 결정 필요 시 *사용자에게 확인* 강제.

```
ask_user_choice("T-A-Landscape-02 의 채널 매핑?",
    ["G→Roughness only", "ARM packing", "ORM packing", "단일 albedo only"])
```

→ LLM 추측 *원천 차단*.

## 5. 채택 효과 — Turn Budget 비교

🔴 **INFERRED** — 정량 측정 미수집, 추정값:

| Hazard fix 채택 | 평균 Turn 소비 | 비고 |
|---|---|---|
| 적용 전 (LLM 추측 + brute-force retry) | 8-12 turn | warped diffuse / Ambient Cube 사례 |
| Layer 1 (자동 정규화) 만 | 5-7 turn | v0.21-v0.23 누적 |
| Layer 1+2+3 (현재 v0.34) | 3-5 turn | run-20260525-145408 — 시도 횟수 감소 관찰 |
| Layer 1+2+3+4 (ask_user_choice 강제 — 미적용) | 2-3 turn (추정) | future cycle 검증 |

## 6. 다른 도메인 적용 가능성

본 hazard family 는 *Material Editor* 한정이 아닌 — *모든 LLM-driven UE 자동화* 에 일반화 가능:

| 도메인 | 추측 hazard 후보 | 대응 Layer |
|---|---|---|
| Animation 자동화 | Anim Notify 채널 / Curve 이름 추측 | Layer 1 (이름 정규화) + Layer 3 (메타데이터) |
| Niagara 자동화 | Module / Renderer 파라미터 추측 | Layer 1 (UClass full name) + Layer 4 (ask_user_choice for renderer mode) |
| Blueprint 자동화 | Variable / Function 이름 추측 | Layer 1 (BP reflection) + Layer 2 (valid list) |
| Sequencer 자동화 | Track type / Section 파라미터 추측 | Layer 3 (read_sequence 응답 메타) |

## 7. Cross-link

- `concepts/UE-Material-Pin-Name-Shortening` (MMA-48 — Layer 1 사례)
- `concepts/LLM-Visual-Reference-Hallucination` (MMA-50 — vision 정밀도 한계)
- `concepts/MCP-Tool-Schema-LLM-Friendly-Design` (4 패턴 — Layer 2/3 일반화)
- `concepts/MCP-Async-UI-Bridge-Pattern` (Layer 4 — ask_user_choice)
- `concepts/UE-Texture-Sampler-Type-Auto-Inference` (Layer 1 — SamplerType 자동 추론)
- `concepts/UEnum-GetValueByName-FullyQualified` (Layer 1 — UEnum prefix 자동)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` (master blueprint)

## 8. Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 3 hazard family (MMA-45/48/50) 공통 메커니즘 | 🟢 VAULT | MCMaterialAuto v0.21-v0.34 cycle 누적 |
| Vision 인식 성공 + 세부 정밀도 한계 | 🟢 VAULT | run-20260525-145408.log line 19-22 직접 확인 |
| 4-Layer Defense 패턴 | 🟢 VAULT | v0.21-v0.34 실측 채택 |
| Turn budget 효과 정량 | 🔴 INFERRED | 측정 미수집 |
| 다른 도메인 적용 가능성 | 🔴 INFERRED | 미검증 |

## 9. 변경 이력

- 2026-05-25: 초안 작성 (MMA-50 evidence 보강 + MMA-45/48/50 통합 family 정리)
