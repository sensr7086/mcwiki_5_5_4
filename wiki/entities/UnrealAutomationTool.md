---
type: entity
title: "UnrealAutomationTool (UAT)"
aliases: [UnrealAutomationTool, UAT, BuildCookRun]
kind: tool
sources:
  - "[[sources/ue-build-skill]]"
tags: [ue, build, tool, devops]
last_updated: 2026-05-09
---

# UnrealAutomationTool (UAT)

## 요약

UE 의 패키징 + 배포 자동화. C# 스크립트 기반. BuildCookRun (Build + Cook + Stage + Pak + Archive) 명령이 표준. CI / CD 표준 진입점.

## 관계

- 페어: [[entities/UnrealBuildTool]] (UBT, 컴파일 — UAT 가 호출)
- 입력: BuildGraph XML / 명령행 인자

## 핵심 주장

- BuildCookRun 명령: 모든 빌드 단계 통합 — `RunUAT.bat BuildCookRun -project=MyGame -platform=Win64 -configuration=Development -cook -stage -pak -archive`.
- Cook: Editor 자산 → 플랫폼별 Cooked 자산. Cooker process 실행.
- Stage: 빌드 결과를 staging 디렉토리에 모음.
- Pak / IoStore: 자산을 .pak / .iostore 로 묶음. 5.x I/O Store 권장.
- Archive: ZIP / 디스크 빌드 출력.
- BuildGraph (5.x 권장): 복잡한 multi-step / multi-platform 빌드의 XML 정의. CI 표준.
- DLC / Patch: BuildCookRun 의 DLC / Patch 옵션 — base build 위에 추가 pak.

## 열린 질문

- [ ] BuildGraph XML 의 표준 패턴
- [ ] Incremental Cook (5.x) 활용
