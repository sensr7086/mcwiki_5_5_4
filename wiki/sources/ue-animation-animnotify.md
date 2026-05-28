---
type: source
title: "UE Animation — AnimNotify sub-skill"
slug: ue-animation-animnotify
source_path: raw/ue-wiki-llm/skills/Animation/references/AnimNotify.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UAnimNotify]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, animation]
---

# UE Animation — AnimNotify sub-skill

> Source: [[raw/ue-wiki-llm/skills/Animation/references/AnimNotify.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

[[entities/UAnimNotify]] (점) vs UAnimNotifyState (구간) + FAnimNotifyEvent + Branch Point + Notify Queue. 발자국·VFX·HitBox·Combo 윈도우·무기 트레이스 표준 패턴 + Pool / AutoRelease 의무.

## 2. Key claims

- UAnimNotify (점): NotifyImpl 한 번 호출. 발자국 / 폭발 / 사운드 트리거.
- UAnimNotifyState (구간): NotifyBegin → NotifyTick → NotifyEnd 3 단. Combo 윈도우 / 무기 trail / HitBox 활성화.
- Notify Queue: AnimGraph Update_AnyThread → Notify Queue 모음 → Game thread 에서 발화.
- Branch Point Notify (Montage): Section 분기 결정 — Combo / Hit reaction.
- Pool / AutoRelease 의무: Notify 객체 매 호출마다 NewObject 시 GC 부담 → UE 가 풀링 관리. Custom Notify 의 멤버 캐싱은 짧게 (Pool 재사용 시 stale 위험).
- Profiling 의무 ([[concepts/Profiling-Scope-Rule]]): Notify::Notify / NotifyBegin / NotifyEnd / NotifyTick 첫 줄 SCOPE.
- 표준 자손: UAnimNotify_PlaySound / UAnimNotify_PlayParticleEffect / UAnimNotifyState_Trail / UAnimNotifyState_TimedNiagaraEffect.

## 3. Open questions

- [ ] AnimNotify Pool 정확한 동작 — 멤버 변수 사용 시 함정
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 0 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Animation/references/AnimNotify.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Animation/references/AnimNotify.md`
