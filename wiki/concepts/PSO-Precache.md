---
type: concept
title: "PSO Precache (Pipeline State Object 사전 컴파일)"
aliases: ["PSO Precache", "r.PSOPrecache", "Bundled PSO Cache"]
sources:
  - "[[sources/ue-render-material]]"
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-mobile]]"
  - "[[sources/ue-render-vr]]"
  - "[[sources/ue-render-rhi]]"
  - "[[synthesis/pso-streaming-livepatch-tools]]"
related_concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [render, gpu, pso, cooked, precache, hitching, mobile, vr]
last_updated: 2026-05-13
---

# PSO Precache

## 정의

Pipeline State Object (PSO) 의 *런타임 첫 사용 시점* 컴파일은 GPU 동기 stall → **Cooked Build 첫 Render 히칭** 의 주요 원인. UE 5.x 의 **PSO Precache 시스템** 은 다음 3축:

1. **`r.PSOPrecache=1` CVar** — `DefaultEngine.ini` 에서 활성. Material 등록 시 PSO 후보 미리 컴파일
2. **Bundled PSO Cache** — Cooked Build 시 `-BuildPSOCache` UAT 옵션으로 `.upipelinecache` 생성, Cooked 첫 Frame 전 일괄 로드
3. **ShaderPipelineCache** — 런타임 Frame 별 PSO 추적 + 다음 Cook 에 feedback (지속적 학습)

## 권위 출처 (vault SSoT)

⭐ **[[sources/ue-render-material]] §2.5** — `r.PSOPrecache=1` CVar 권위 출처 (raw Material.md L93).

다른 source 의 PSO 언급은 *부분 페어*:
- [[sources/ue-render-shader]] §1 — Shader.md L268 "Cooked Build 안 컴파일 (DDC 미스)" 표현만, CVar 직접 명시 X
- [[sources/ue-render-mobile]] — Quest Bundled PSO Cache 통합 패턴
- [[sources/ue-render-vr]] — 90/120 fps 시작 hitch 회피 필수
- [[sources/ue-render-rhi]] — FRHICommandList PSO state binding 차원

## 적용 매트릭스

| 플랫폼 | 의무도 | 이유 |
|--------|--------|------|
| PC (DX12/Vulkan) | 권장 | Permutation 폭증 시 첫 히칭 |
| Mobile (iOS/Android) | **의무** | Mali/Adreno PSO 캐시 부재 + Vulkan ES 컴파일 비용 큼 |
| Quest VR | **의무** | 90 fps 유지 + 시작 hitch 차단 |
| Console (PS5/XSX) | 권장 | 빠른 GPU 라도 첫 cooked PSO 비용 ↑ |

## 함정

- ❌ `r.PSOPrecache=1` 만 켜고 Bundled cache 미생성 → 런타임 추적만, 첫 실행 히칭 그대로
- ❌ Material × Shader Permutation × VertexFactory 조합 폭증 → PSO 수 만 개, 컴파일 시간 ↑
- ✅ `-BuildPSOCache` UAT + 대표 playthrough 캡처 → 실제 사용 조합만 캐시

## Cross-link

- 권위 source: [[sources/ue-render-material]] §2.5
- 페어: [[sources/ue-render-shader]] · [[sources/ue-render-mobile]] · [[sources/ue-render-vr]] · [[sources/ue-render-rhi]]
- 도구 synthesis: [[synthesis/pso-streaming-livepatch-tools]] (Sub-level Streaming + Live Patch + RenderDoc/PIX)
- Cooked 빌드: [[concepts/Cooked-vs-Uncooked]] · [[sources/ue-coreuobject-cooking]]
