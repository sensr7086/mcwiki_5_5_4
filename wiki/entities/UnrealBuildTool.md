---
type: entity
title: "UnrealBuildTool (UBT)"
aliases: [UnrealBuildTool, UBT, Build.cs, Target.cs]
kind: tool
sources:
  - "[[sources/ue-build-skill]]"
tags: [ue, build, tool]
last_updated: 2026-05-09
---

# UnrealBuildTool (UBT)

## 요약

UE 의 C# 빌드 시스템. `Build.cs` (모듈 의존) + `Target.cs` (타겟 종류) 정의를 읽어 MSBuild / Make / Xcode 프로젝트 생성 + 컴파일 명령. PCH / Unity Build / IWYU (Include What You Use) 통합.

## 관계

- 페어: [[entities/UnrealAutomationTool]] (UAT, 패키징 — UBT 위 layer)
- 입력: *.Build.cs / *.Target.cs

## 핵심 주장

- Build.cs: 모듈 의존 정의. PublicDependencyModuleNames + PrivateDependencyModuleNames + 분기 (`Target.bBuildEditor` / `Target.Type == TargetType.Server`).
- Target.cs: 타겟 종류 — Game / Editor / Server / Client / Program. bBuildAllModules / bWithServerCode / bUsesSlate.
- PCH (Precompiled Header): 자주 쓰는 헤더 미리 컴파일. PCHUsage = UseExplicitOrSharedPCHs (5.x 권장).
- Unity Build: 여러 .cpp 합쳐서 컴파일 — 빌드 시간 ↓ (CI). 디버깅 시 IWYU 모드 권장.
- 5 종 빌드 구성: Debug / DebugGame / Development (default) / Test / Shipping.
- 5.x BuildGraph: 복잡한 빌드 파이프라인 (DLC / Patch / 다중 플랫폼) 의 표준.

## 열린 질문

- [ ] Live Coding (5.x) 의 UBT 통합
- [ ] Modular vs Monolithic 빌드 결정 트리
