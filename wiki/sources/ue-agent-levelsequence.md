---
type: source
title: "UE LevelSequence Specialist Agent (15번째)"
slug: ue-agent-levelsequence
source_path: raw/ue-wiki-llm/agents/ue-levelsequence-specialist.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-16
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, specialist, levelsequence, baseline-grep-cycle-5o, enriched-card]
citation_disclosure: "🟢 9 / 🟡 0 / 🔴 0 · plugin 미등록 (raw 만, G3 게이트 작업 후보) · Cycle 5o #1 Baseline Grep § 추가 — 다른 12 agent 카탈로그와 일관화"
---

# UE LevelSequence Specialist Agent 🎬

> Source: [[raw/ue-wiki-llm/agents/ue-levelsequence-specialist.md]] (250L)
> 15번째 agent (vault 신규) · plugin **미등록** (현재 13 agent 만 plugin 활성, raw 만 정의)
> Pair: [[sources/ue-levelsequence-skill]] (21번째 카테고리 main)
> 호출: `Task(subagent_type="ue-wiki-llm:ue-levelsequence-specialist", ...)` — plugin 재배포 후 가능
> Cycle 5o #1 (2026-05-16) — §Baseline Grep + §변경 이력 추가 (다른 12 agent 일관화)

## 1. Summary

UE 5.7.4 LevelSequence 카테고리 전문가 — 시네마틱 / 컷씬 / 영상 시스템. 10 sub-skill (MovieScene + Tracks 43종 + LevelSequencePlayer + Director + CineCamera + Sequencer 🛠 + MovieRenderPipeline 5.x + EntitySystemECS + SequencerScripting + TemplateSequence). `[LevelSequence]` prefix 호출.

## 2. Key claims

### 2.1 11 시나리오 매핑 🟢

| 시나리오 | sub-skill |
|---------|-----------|
| 런타임 컷씬 재생 ⭐⭐⭐ | LevelSequencePlayer + Tracks |
| BP Director Event Track | Director + Tracks/EventTrack |
| 시네마틱 카메라 (DoF) | CineCamera + Tracks/CameraCut |
| 캐릭터 애니메이션 시퀀스 | Tracks/SkeletalAnimationTrack |
| Sub Sequence (영화 안 영화) | Tracks/SubTrack |
| Movie Render Queue (영상 출력) | MovieRenderPipeline |
| 커스텀 트랙 (게임 전용) | MovieScene + Tracks 패턴 |
| Sequencer Editor 확장 🛠 | Sequencer + 4단 분리 |
| Python 자동화 | SequencerScripting |
| 재사용 가능 시퀀스 | TemplateSequence |
| 5.x ECS 깊이 / 성능 | EntitySystemECS |

### 2.2 자동 로드 7 파일 🟢

1. `skills/LevelSequence/SKILL.md` (메인)
2. `skills/LevelSequence/references/LevelSequencePlayer.md` ⭐⭐⭐
3. 사용자 요청 sub-skill (MovieScene/Tracks/Director/CineCamera/Sequencer/MovieRenderPipeline/etc)
4. 🚨 `references/07_ProfilingScopeRule.md`
5. 🚨 `references/11_AssetLoadingPolicy.md`
6. 🚨 `references/05_EditorOnlyIndex.md`
7. (페어) `skills/Animation/SKILL.md` (Skeletal Animation Track 시)

### 2.3 cross-category 통합 🟢

- AssetClasses/Camera — `UCameraAnimationSequence` (자손)
- UMG — `UWidgetAnimation` (동일 베이스)
- Animation/AnimInstance — `SkeletalAnimationTrack`
- Components/Audio + Camera + Rendering — 각 트랙 페어

### 2.4 4단 분리 의무 🟢

Runtime (`UMovieSceneTrack` 자손) vs Editor (`ISequencerTrackEditor` 자손). Build.cs 분기 + `#if WITH_EDITOR` 가드.

### 2.5 5.x ECS 표준 🟢

`FMovieSceneEntityManager` 4단계 (Instantiation / Evaluation / Blending / Application). Game Thread 안 멀티스레드 안전.

### 2.6 plugin 미등록 — G3 게이트 작업 후보 🟡

현재 Cowork plugin agent 목록에 `ue-levelsequence-specialist` 미존재 (13 agents 만 활성). raw 만 정의 → **plugin 재배포 필요**. G3 게이트 (ue-spatial-partition-specialist + orchestrator §5.4) 와 동시 작업 후보.

## 3. ⭐⭐⭐ Baseline Grep 의무 (Cycle 5h #4 + Cycle 5o #1 적용) 🟢

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세. main 이 본 agent .md 를 read_raw 로 흡수한 후, vault 일관성 자동 검증 의무 (mcwiki MCP v0.5.1 4 Baseline Grep 도구 활용).

### 3.1 Pre-write (3 단계)

1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → stub vs enriched + § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증

### 3.2 Post-write (3 단계)

4. `mcwiki: lint` — broken cross-link / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. `mcwiki: find_cross_link_broken` — `{slug: target_slug, kind: sources}` → broken_count == 0 (mcwiki v0.3.0+)
6. `mcwiki: append_log` — `{op: feature|fix|verify|note|refactor, title: ..., body: ...}` → log.md 기록 의무

### 3.3 본 agent 함정 키워드 (search 의무)

`UMovieScene` / `UMovieSceneSequence` / `UMovieSceneTrack` / `UMovieSceneSection` / `FFrameNumber` / `FFrameRate` / `Sequencer` / `ULevelSequencePlayer` / `ALevelSequenceActor` / `CineCamera` / `MovieRenderPipeline` / `FMovieSceneEntityManager` / `ISequencerTrackEditor`

### 3.4 governance §8.4 와의 매트릭스 통합 🟢

| §8.4 5단 의무 | 본 § 매핑 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` + `general-purpose` Task 위임 |
| 5. Audit | post-write `lint` |

### 3.5 KMCProject MCComboEditor 사례 (Cycle 5d) — 본 agent 첫 실측

[[synthesis/mc-combo-editor-levelsequence-lite]] — LevelSequence 데이터 모델 *lite* 차용 (UMovieSceneSequence 풀스택 X + AnimNotify Track 스타일 자체 Slate). 21 파일 빌드 통과. 본 agent 의 차용 시나리오 매트릭스 — **데이터 모델만 사용** vs **Sequencer 풀스택 통합** 결정 첫 사례.

### 3.6 신규 도구 활용 (mcwiki v0.5.1 — Cycle 5j+)

분기별 또는 cycle 진행 시 추가 도구 사용 권장:
- `suggest_missing_cross_link` — outbound/inbound + 누락 reverse-link 추천
- `find_stale_baseline` — 90일 임계 staleness 검출
- `find_claim_conflict` — 페어 페이지 일관성 검증 (heuristic, 한국어 단위 명사 false positive 회피 필요)

## 4. Cross-link

- Pair: [[sources/ue-levelsequence-skill]] (21번째 카테고리 main)
- 다른 agents (메타 4): [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-spatial-partition]] (14번째, plugin 미등록 동일 — G3 게이트 동시 작업) · [[sources/ue-agent-animation]] (SkeletalAnimationTrack) · [[sources/ue-agent-asset]] (UCameraAnimationSequence) · [[sources/ue-agent-slate-umg]] (UWidgetAnimation 동일 베이스)
- 정책: [[concepts/Profiling-Scope-Rule]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Editor-Only-4-Tier-Separation]]
- KMCProject 실측: [[synthesis/mc-combo-editor-levelsequence-lite]] (LevelSequence 데이터 모델 lite — Cycle 5d, 21 파일 빌드 통과)
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 5. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-14 | 15번째 agent slim card 작성 (Cycle #12 카테고리 신설 동시 — 정밀 9 claims) |
| **2026-05-16 (Cycle 5o #1)** | ⭐⭐⭐ **§3 Baseline Grep 의무 § 신규 추가** (Cycle 5h #4 patch + Cycle 5o 일관화) — Pre-write 3단 + Post-write 3단 + 본 agent 함정 키워드 13종 + governance §8.4 매트릭스 통합 + §3.5 KMCProject MCComboEditor 실측 cross-link (Cycle 5d) + 신규 도구 v0.5.1 활용. + §5 변경 이력 §추가. last_updated 갱신 (2026-05-14 → 2026-05-16) |
