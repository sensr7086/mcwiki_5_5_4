---
title: "LLM Visual Reference Hallucination — 이미지 입력 없을 시 패턴 추측 hazard"
kind: concept
status: stable
severity: "★★★"
tags: [llm, claude, vision, hallucination, hazard, MMA-50, ue-574, integration]
created: 2026-05-22
last_updated: 2026-05-22
---

# LLM Visual Reference Hallucination — 이미지 입력 없을 시 패턴 추측 hazard

## 정의

LLM (Claude 등) 이 *시각 입력 없이* 시각 참조에 의존하는 작업 (예: 머티리얼 그래프 복제 / UI 클론) 을 수행할 때, **이름 패턴 / 도메인 convention / 통계적 prior 만으로 추측** 해 *원본과 다른 결과* 생성하는 hazard. 사용자가 *prompt 안 path 만 명시* 했고 *실제 vision input 으로 변환되지 않으면* 발생.

특히 PBR 머티리얼 영역에서 **ORM (Occlusion/Roughness/Metallic) / ARM (Ambient/Roughness/Metallic) 패킹 가정** 으로 *단순한 albedo+roughness+normal 머티리얼* 도 *packed mask* 로 잘못 해석.

## 자세히

### 사례: MCMaterialAuto NewMaterial5 → NewMaterial6 (MMA-50)

🟢 **VAULT** — MCMaterialAuto v0.30-v0.34 cycle 실측 사용자 사례.

**의도** (사용자가 paste 한 참조 스크린샷):
- TextureSample 1 (회색/돌) → BaseColor
- TextureSample 2 (피부톤) → Roughness 의 한 채널만 (G 또는 B)
- TextureSample 3 (Blue Normal) → Normal

**Claude 생성** (NewMaterial5 / NewMaterial6 — 두 번 동일 패턴):
- TextureSample 1 → BaseColor (✅)
- TextureSample 2 → **ARM/ORM packing 가정** — R→Metallic, G→Specular, B→Roughness, A→AO (❌)
- TextureSample 3 → Normal (✅)

**Claude 자체 인정** (응답 마지막 줄):
> "마스크 텍스처는 ORM 패킹용이 아닌 일반 알베도(T-A-Landscape-02) 라 실제 PBR 값은 의도와 다를 수 있어요"

→ LLM 이 *자신의 가정에 확신 없음* 을 표명 + 사용자 확인 요청. 그러나 *기본값* 으로 ORM 가정 채택.

### 근본 원인 — 3가지

#### 1. Vision 입력 실패 (가장 큰 원인)

🟡 **PARTIAL** — Claude Code CLI `-p` non-interactive 모드:
- 사용자가 prompt 에 image path 삽입 — Claude Code 인터랙티브 모드는 *자동 inline attach* (vision 변환)
- 그러나 `-p` 모드의 path 자동 attach 는 **미검증 / 불안정** (GitHub Issue #35866 / #18588)
- → image path 가 *plain text* 로 prompt 에 남아 LLM 이 vision 으로 인식 안 함

#### 2. 도메인 convention prior

🟢 **VAULT**:
- PBR 머티리얼 = "BaseColor + ORM packed + Normal" 이 *학습 데이터의 다수* 표준
- LLM 이 *그 패턴을 default* 로 가정 → 사용자 의도와 무관하게 채택

#### 3. 텍스처 이름 패턴 매칭

🟡 **PARTIAL**:
- `T_*_Specular` / `T_*_ARM` / `T_*_ORM` 같은 이름 — LLM 이 *packing 의도* 로 해석
- `T-A-Landscape-02` 처럼 ambiguous 한 이름 — *albedo* 인지 *mask* 인지 추측에 의존

## 회피 패턴

### Fix 1 — Vision 입력 확실히 강제

🟡 **PARTIAL** (검증 미완):
- prompt 안에 *`Read tool 로 <path> 이미지 분석해줘`* 명시 — Claude Code 의 image-aware Read 강제 호출
- 또는 `--image <path>` CLI 인자 사용 (지원 시)
- 또는 base64 inline (`![](data:image/png;base64,...)`)

### Fix 2 — Prompt 에 명시적 채널 매핑 정보 추가

🟢 **VAULT** — MCMaterialAuto session followup 사례:
```
참조 머티리얼의 *정확한* 매핑:
- T1 (RGB) → BaseColor
- T2 의 G 채널만 → Roughness (다른 채널 unused)
- T3 (RGB) → Normal
ORM/ARM 패킹 가정 폐기.
```

→ 추측 hazard 차단 + 즉시 fix 가능.

### Fix 3 — 도구 측 *prompted 확인* 강제

🟢 **VAULT** — vault [[concepts/MCP-Async-UI-Bridge-Pattern]] (v0.32):
- LLM 이 ambiguous texture 만나면 → `ask_user_choice` 도구로 사용자에게 확인
- 예: `ask_user_choice("T-A-Landscape-02 의 채널 매핑?", ["G→Roughness only", "ARM packing", "ORM packing", ...])`

→ LLM 추측 회피 + 사용자가 명시 결정.

### Fix 4 — 텍스처 메타데이터 자동 노출

🟢 **VAULT** — vault [[concepts/UE-Texture-Sampler-Type-Auto-Inference]] (v0.34) 후속:
- `list_textures` 응답에 *채널별 *평균값* / *분산* / *histogram* 노출 → LLM 이 *데이터 기반* 추론 가능
- 예: "R 채널 평균 0.5 + 분산 낮음 → constant" / "G 채널 분산 큼 → 의미 있는 데이터"

## 진단 (Hazard 발생 확인)

증상:
- LLM 응답이 "ARM 패킹용으로 가정했어요" / "ORM 가정" 같은 *추측 단어* 포함
- 생성된 머티리얼이 원본과 *채널 매핑* 다름
- 결과에 *불필요한 추가 연결* (Metallic / Specular 등 원본 없음)

진단 절차:
1. 풀 로그에서 image content 확인 (`[raw]` 또는 `[user]` 라인의 stream-json) — vision input 변환 여부
2. LLM 응답 중 "가정했어요" / "ARM" / "ORM" / "추측" 키워드 grep
3. 생성된 머티리얼 vs 참조 비교 — 추가/누락 연결

## 변형 사례

1. **UI 클론 작업**: LLM 이 *스크린샷 보고 UI 만들기* — vision 없으면 *대중적 layout* (Material Design / Tailwind preset) 추측
2. **데이터 시각화**: chart 참조 이미지 — vision 없으면 *bar chart default* 추측
3. **3D Asset 분류**: thumbnail 참조 — vision 없으면 *이름 prefix* 로 분류 (`SM_*` = StaticMesh, `T_*` = Texture)

## 관련 entity

- [[Claude-Code-CLI]] (`-p` 모드 vision input 한계)
- [[MCP-Protocol]] (`tools/call` content 의 image 지원)

## 열린 질문

1. ❓ Claude Code `-p` 모드의 *정확한 vision input* 변환 조건 — image path 자동 attach 의 한계 (현재 GitHub issue 다수).
2. ❓ `Read` tool 의 image vision 변환 — UE MCMaterialAuto 의 풀 로그에서 *실측 검증* 필요.
3. ❓ Vision 입력 성공 시 LLM 의 hallucination 감소 정량 측정 — 측정 metric 정의 필요.

## Cross-link

- `concepts/MCP-Async-UI-Bridge-Pattern` (Fix 3 — ask_user_choice 로 확인 강제)
- `concepts/UE-Texture-Sampler-Type-Auto-Inference` (Fix 4 — 메타데이터 자동 노출)
- `concepts/Claude-Code-Cowork-ToolSearch-Bypass` (같은 Claude integration 계열)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` § 시나리오 검증 매트릭스

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| LLM 의 ORM/ARM 패킹 가정 hazard | 🟢 VAULT | MCMaterialAuto NewMaterial5/6 실측 (두 번 동일 패턴) |
| Claude Code `-p` 모드 vision input 미검증 | 🟡 PARTIAL | GitHub Issue #35866 / #18588 — 진행 중 hazard |
| 도메인 convention prior 영향 | 🟢 VAULT | LLM 학습 데이터의 PBR 표준 (industry standard ORM packing) |
| Fix 3 (ask_user_choice 강제) 효과 | 🟢 VAULT | v0.32 도구로 가능 — 실측 적용 미완 |
| Fix 4 (메타데이터 자동 노출) 효과 | 🔴 INFERRED | 가설 단계 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-50 / MCMaterialAuto NewMaterial5/6 두 차례 동일 패턴 사용자 보고)
