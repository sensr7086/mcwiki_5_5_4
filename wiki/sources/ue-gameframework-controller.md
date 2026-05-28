---
type: source
title: "UE GameFramework — Controller sub-skill"
slug: ue-gameframework-controller
source_path: raw/ue-wiki-llm/skills/GameFramework/references/Controller.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AController]]"
  - "[[entities/APlayerController]]"
  - "[[entities/AAIController]]"
related_concepts:
  - "[[concepts/Possession]]"
  - "[[concepts/SeamlessTravel]]"
tags: [ue, runtime, gameframework]
---

# UE GameFramework — Controller sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/Controller.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/AController]] (420) + [[entities/APlayerController]] (2,377) + [[entities/AAIController]] (AIModule cross-link). [[concepts/Possession]] / Camera / InputMode / [[concepts/SeamlessTravel]] / Voice / Audio.

## 2. Key claims

- Possess(Pawn) → Pawn->PossessedBy(Controller) → ReceiveControllerChanged → SetupPlayerInputComponent.
- ControlRotation: Pawn 의 시점. Pawn->GetControlRotation() 으로 접근.
- Local / Remote / Authority — APlayerController 는 Server 와 OwningPlayer Client 에만 존재.
- InputMode 3 종 (PlayerController): GameOnly / UIOnly / GameAndUI.
- PlayerCameraManager: 카메라 효과 / 페이드. ClientSetCameraFade / ClientSetCameraMode.
- SeamlessTravel: 새 맵에서 PlayerController 새로 생성. PlayerState 일부 데이터 인계.
- AAIController (AIModule): BehaviorTree / Blackboard / EQS / Perception 통합 진입점.
- Voice: UVoiceManager + IVoiceModule (Plugin) 통합.

## 3. Open questions

- [ ] Listen Server 의 PlayerController 동작 (Client + Server 동시)
- [ ] PlayerState 의 SeamlessTravel 인계 표준
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 4 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/references/Controller.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/references/Controller.md`
