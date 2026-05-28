---
type: source
title: "UE 5.7.4 Build Module — Main SKILL"
slug: ue-build-skill
source_path: raw/ue-wiki-llm/skills/Build/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UnrealBuildTool]]"
  - "[[entities/UnrealAutomationTool]]"
related_concepts:
  - "[[concepts/Build-Configurations]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, build, devops]
---

# UE 5.7.4 Build Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Build/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

빌드 / 패키징 / 배포 표준. [[entities/UnrealBuildTool]] (UBT, C# 빌드 시스템) + [[entities/UnrealAutomationTool]] (UAT, 패키징/배포) + Build.cs (모듈 의존) + Target.cs (타겟 종류) + Cooking + Pak/IoStore + 5 종 [[concepts/Build-Configurations]] (Debug/DebugGame/Development/Test/Shipping) + DLC/Patch + BuildGraph. Hot Reload vs Live Coding 차이. 모듈 의존 4단 분리.

## 2. Key claims

- Build.cs (`MyGame.Build.cs`) = 모듈 의존 정의. PublicDependencyModuleNames + PrivateDependencyModuleNames + Editor 전용 분기 (`if (Target.bBuildEditor) { ... }`).
- Target.cs (`MyGame.Target.cs`) = 타겟 종류 (Game / Editor / Server / Client / Program). bBuildAllModules / bWithServerCode 등.
- 5 종 빌드 구성: Debug (디버깅) / DebugGame (게임 코드만 디버그) / Development (기본 개발) / Test (자동 테스트) / Shipping (출시). [[concepts/Build-Configurations]]
- Cooking = Editor 자산 → 플랫폼별 Cooked 자산. Cooker process. [[concepts/Cooked-vs-Uncooked]]
- Pak vs IoStore — 5.x I/O Store 권장 (.utoc / .ucas) — 더 빠른 streaming.
- Hot Reload (deprecated) vs Live Coding (5.x 표준) — 런타임 코드 갱신.
- 모듈 4단 분리 (Editor only): Runtime 모듈 / Editor 모듈 / `Type=Editor` uplugin / `#if WITH_EDITOR` 가드. → [[concepts/Editor-Only-4-Tier-Separation]] · [[raw/ue-wiki-llm/references/05_EditorOnlyIndex.md]]
- DLC / Patch: BuildGraph 로 base + DLC pak 분리. ContentOnly 또는 CodeProject DLC.

## 3. Quotations

> "본 sub-skill 은 모듈 의존 / 빌드 구성 / 패키징 / 배포 표준 정리. Editor 전용 4단 분리는 references/05_EditorOnlyIndex.md 페어."

## 4. Open questions / next sources

- [ ] BuildGraph 의 표준 DLC 패턴
- [ ] Live Coding 의 UCLASS 변경 한계
