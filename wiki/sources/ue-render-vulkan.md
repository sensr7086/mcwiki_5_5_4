---
type: source
title: "UE Render — Vulkan / RHI 벤더 sub-skill"
slug: ue-render-vulkan
source_path: raw/ue-wiki-llm/skills/Render/references/Vulkan.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
tags: [ue, render, gpu, vulkan]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Render — Vulkan / RHI 벤더

> Source: [[raw/ue-wiki-llm/skills/Render/references/Vulkan.md]]
> Parent: [[sources/ue-render-skill]]

## 1. Summary

RHI 벤더 차이 — DX12 / Vulkan / Metal / OpenGL ES. 플랫폼 분기 + 셰이더 호환성 + 5.x Vulkan 전용 함정 (Render Pass / Pipeline Barrier / Descriptor Set) + Driver 디버그. Cross-Platform 셰이더 작성 표준.

## 2. Key claims

- DX12: Windows / Xbox 기본. Bindless resource. PSO 가 가장 정교.
- Vulkan: Linux / Android / Switch. Render Pass / Subpass + Pipeline Barrier 명시 — 5.x 의 디버그 핫스팟.
- Metal: macOS / iOS. MSL (Metal Shading Language) 변환.
- OpenGL ES: Mobile fallback — 5.x 에서 deprecated 진행 중.
- HLSLcc / DXC: 셰이더 변환 (HLSL → SPIR-V → MSL).
- 5.x Vulkan 함정: Pipeline Barrier 누락 → race condition. Descriptor Set 한계 → 빈번한 rebind.
- Driver 디버그: RenderDoc + Vulkan Validation Layers + GPU Crash Dump.

## Cross-link

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-render-rhi]] (inbound=3, suggest_missing_cross_link high confidence)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 0
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 12
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 0

**주요 시그니처 변경**:
_(없음)_

**5.5.4 표현 (5.7.4 에 없음)**:
- `namespace ERHIFeatureLevel`
- `{`
- `enum Type`
- `{`
- `ES2_REMOVED,        // 5.x — 제거됨 (placeholder)`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/Render/references/Vulkan.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/Render/references/Vulkan.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **0 변경** (12 라인 추가)
- 정합 후 tier: **pass-body-no-direct-cite**
