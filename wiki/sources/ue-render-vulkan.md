---
type: source
title: "UE Render — Vulkan / RHI 벤더 sub-skill"
slug: ue-render-vulkan
source_path: raw/ue-wiki-llm/skills/Render/references/Vulkan.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
tags: [ue, render, gpu, vulkan]
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
