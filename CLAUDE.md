# LLM Wiki Schema (CLAUDE.md / AGENTS.md)

> 본 파일은 Karpathy 의 LLM Wiki 패턴 ([gist 442a6bf](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) 을 Obsidian + Claude Code 환경에서 *그대로* 운영하기 위한 마스터 스키마.
>
> **읽는 순서**: §0.1 동행 정책 (UE 도메인 raw) → §1 미션 → §2 아키텍처 → §3 페이지 타입 → §4 wikilink 규약 → §5 워크플로 (Ingest/Query/Lint) → §6 index/log 포맷 → §7 충돌 해결 → §8 금기.
>
> 이 파일이 LLM 을 *generic chatbot* 이 아닌 *disciplined wiki maintainer* 로 만든다 (Karpathy gist 의 원문 표현). 사람과 LLM 이 공동 진화시킨다.

---

## §0. 사용 컨텍스트

- 사용자: "민철" (Korean). 본문/설명 한국어, 식별자/원문 인용 영어.
- 도구: Obsidian + Claude Code (또는 Codex / OpenCode 등 — `AGENTS.md` 가 본 파일의 alias).
- 명령 형태: 사용자가 자연어로 "ingest 해줘" / "query: ..." / "lint" 등을 발화. LLM 은 본 §5 워크플로를 따른다.

---

## §0.1. 동행 정책 — UE 도메인 raw 참조

본 vault 는 **dual-raw 구조** (2026-05-27 사용자 결정):

- **`raw/ue-wiki-llm_5_5_4/`** — *active raw* · UE 5.5.4 엔진 기준 LLM_Wiki 추출 (223 .md / 3.2 MB) · ingest/query 의 1차 출처
- **`raw/ue-wiki-llm/`** — *audit reference* · UE 5.7.4 vintage (E:\MCWiki 에서 인계, 동일 223 .md) · 5.5↔5.7 diff 비교 및 14 concept tier-demote audit 시 cross-check 용. 점진 deprecated 가능.

콘텐츠 측정 (2026-05-27): 78 .md identical (34% — version-stable 정책), 145 .md diff (65% — 실제 API delta).

**원본 위치**: `C:\Unreal\UnrealEngine\LLM_Wiki\` (5.5.4 엔진 기준 재생성 결과). **현재 vault 위치**: `E:\MCWiki_5_5_4\` (5.5.4 active). **이전 vault**: `E:\MCWiki\` (5.7.4 frozen — read-only archive).

원본 갱신 시 sync 명령 (5.5.4 폴더 갱신):
```powershell
cp -r C:\Unreal\UnrealEngine\LLM_Wiki\{skills,references,catalog,docs,meta,README.md,MANIFEST.md} E:\MCWiki_5_5_4\raw\ue-wiki-llm_5_5_4\
```

LLM 이 **UE 5.5.x 도메인 콘텐츠** 를 ingest/query/synthesis 할 때, 본 schema 의 일반 규칙 위에 다음 raw 정책을 *추가로* 따른다 — Karpathy 일반 패턴 (이 파일) + UE 특화 정밀판 (raw 링크).

> **인용 시 raw 경로 규약**: 신규/갱신 인용은 `[[raw/ue-wiki-llm_5_5_4/...]]` 사용. 기존 wiki/sources/ 등의 `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료를 가리킴 — Phase 2 audit 시 점진 redirect.

### §0.1.1. 메인 UE 프로젝트 가이드 (필수 1회 로드)

- [[raw/ue-wiki-llm/docs/CLAUDE.md|UE Project CLAUDE.md]] — 명명 규칙 (U/A/S/I/E/F/T/b 접두) · Render/Slate/Components 3분할 디렉토리 · 코드 스타일 (Tab/Allman/`#pragma once`/`nullptr`/`TWeakObjectPtr`/전방선언) · 카테고리별 작업 규칙
- [[raw/ue-wiki-llm/docs/INSTALL.md|UE Project INSTALL.md]] — 셋업 절차

### §0.1.2. Karpathy 메타 ↔ UE 특화 매핑

본 vault `00_meta/` 가 *일반론*, raw 의 다음 5개가 *UE 특화 정밀판*:

| 본 vault (일반) | UE 특화 (raw) | 차이 |
| -- | -- | -- |
| `00_meta/00_QualityCriteria.md` (4차원 100점) | [[raw/ue-wiki-llm/references/17_QualityCriteria.md]] | Performance 35% / Memory 25% / Network 15% / Maintainability 25% + PC High/Mid/Low/Console/Mobile/VR 플랫폼별 임계 |
| `00_meta/01_PolicyPriority.md` (Article 1~10) | [[raw/ue-wiki-llm/references/16_PolicyPriority.md]] | Tier 1 Compile / Tier 2 GC / Tier 3 Runtime / Tier 4 Performance / Tier 5 Maintainability + 5개 충돌 예시 |
| `00_meta/03_EvaluatorRecipe.md` (8단계) | [[raw/ue-wiki-llm/references/15_EvaluatorRecipe.md]] | Policy / Compile / Runtime / Performance + Cooked Build 검증 의무 |
| `00_meta/04_AuditPolicy.md` (분기별) | [[raw/ue-wiki-llm/references/18_ModelEvolutionAudit.md]] | 2축 (UE 진화 + Anthropic 모델 진화) + 6종 결정 (Continue/Update/Simplify/Merge/Deprecate/Remove) |
| `00_meta/05_HandoffProtocol.md` (cross-link) | [[raw/ue-wiki-llm/references/14_TaskHandoffTemplate.md]] | Sprint Contract / Decision Log / Progress / Evaluator Findings / Next Session Brief 5섹션 |

UE 콘텐츠 작업 시 LLM 은 본 vault 의 일반 규칙으로 *시작* 하되, 위 표 오른쪽 (UE 특화) 의 더 정밀한 기준을 *추가 적용*. 두 정책 충돌 시 §0.1.6 의 우선순위 표.

### §0.1.3. UE 횡단 의무 정책 (raw)

UE C++ 코드 또는 그 코드를 다루는 wiki 페이지를 만들 때 *항상* 적용:

- 🚨 [[raw/ue-wiki-llm/references/07_ProfilingScopeRule.md]] — 모든 Tick/Update/Notify/람다/UFunction/OnRep_* 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무
- 🚨 [[raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md]] — TActorIterator/TObjectIterator/TObjectRange 사용 금지 → 등록 패턴 / AssetRegistry 우선
- 🚨 [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]] — Components 6대 의무 (Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO)
- 🚨 [[raw/ue-wiki-llm/references/11_AssetLoadingPolicy.md]] — SpawnActor 히칭 방지 + Soft/Hard Reference + FStreamableManager + UAssetManager Primary Asset/Bundle + PreLoad 5대 정책
- 🎯 [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]] — Bone LOD + StaticMesh LOD + Actor Merging (HISM/HLOD/WorldPartition) + Audio Culling + Niagara Quality Scaling 5대 영역
- 📚 [[raw/ue-wiki-llm/references/19_ExternalSourcesGuide.md]] — 외부 출처 인용 가이드

### §0.1.4. 시나리오 → sub-skill 묶음 (하네스)

UE 작업 ingest 시 어떤 sub-skill 들을 함께 읽을지의 매트릭스:

- [[raw/ue-wiki-llm/references/03_WikiHarness.md]] — 시나리오 → 필수 묶음 (예: "Render Pass 작성" → SlateCore/Drawing + RDG sub-skills)
- [[raw/ue-wiki-llm/references/00_README.md]] — UE 위키 진입 README
- [[raw/ue-wiki-llm/references/01_LayerMap.md]] — L1~L7 의존 계층
- [[raw/ue-wiki-llm/catalog/RuntimeIndex.md]] — Runtime 모듈 카탈로그 189개
- [[raw/ue-wiki-llm/catalog/EditorDevIndex.md]] — Editor/Developer 모듈 카탈로그
- [[raw/ue-wiki-llm/MANIFEST.md]] — raw 인벤토리 + ingest 우선순위
- [[sources/ue-manifest]] — wiki 측 4G 인덱스 (refs/catalog/docs/meta source 페이지 카탈로그)

### §0.1.5. 보조 인덱스 (raw)

- [[raw/ue-wiki-llm/references/04_OverrideIndex.md]] — virtual + RebuildWidget + Super 호출 통합 표
- [[raw/ue-wiki-llm/references/05_EditorOnlyIndex.md]] — 🛠 + 4단 분리 원칙
- [[raw/ue-wiki-llm/references/06_InvalidationHotspots.md]] — RichText/EditableText/Throbber 인밸리데이션 hotspot
- [[raw/ue-wiki-llm/references/08_OverlapHotspots.md]] — PrimitiveComponent Overlap 비용/핫스팟
- [[raw/ue-wiki-llm/references/02_VerificationLog.md]] — 검증 로그

### §0.1.6. 우선순위 충돌 시

본 vault `CLAUDE.md` (이 파일) 의 *일반 schema* vs `raw/ue-wiki-llm/` 의 *UE 특화 정책* 이 충돌:

| 충돌 종류 | 우선 | 이유 |
| -- | -- | -- |
| schema 형식 (frontmatter 필드 / wikilink 규약 / page type) | 본 vault `CLAUDE.md` | 이게 schema. raw 는 content. |
| content 정책 (코드 작성 규칙 / 정책 Tier / 명명 규칙) | UE 특화 (raw) | 도메인 권위 — Epic 표준 + UE 5.5.x 검증. |
| 둘 다 (예: synthesis 페이지의 UE 코드 스니펫 양식) | 사용자 확인 | 결정 후 본 §0.1 또는 §3 갱신. |

원칙: **schema = "어떻게 wiki 를 운영하는가" (이 파일) / UE raw = "wiki 가 다루는 콘텐츠의 도메인 규칙" (참조)**. 두 layer 가 깔끔히 분리.

---

## §0.2. Plugin-less Agent Emulation Pattern

> **결정**: 2026-05-15 — ue-wiki-llm Claude Code plugin 시스템 **사용 안 함**. agent prompt 본문이 plugin 측 ZIP 안 packed 되는 구조는 .md 변경 시 매번 재패키지 + uninstall + install + Desktop 재시작 부담. → mcwiki MCP 의 `read_raw` 도구로 agent .md 본문을 **main Cowork 가 직접 흡수** 하는 패턴으로 대체.

### §0.2.1. 호출 흐름

사용자가 `[GameFramework]` / `[Render]` / `[LevelSequence]` 등 카테고리 prefix 사용 시:

1. **main Cowork** 가 `mcwiki: read_raw raw/ue-wiki-llm/agents/ue-{category}-specialist.md` 호출 → agent 정의 본문 흡수
2. 본 본문 안 "자동 로드" 명시된 sub-skill 도 `read_raw` 로 추가 로드 (`skills/<Category>/SKILL.md` + 횡단 정책 `references/*.md`)
3. 흡수된 컨텍스트를 *system prompt 처럼* 사용하여 specialist 역할 수행 — `Task(subagent_type=)` 위임 X (main 직접 처리)
4. `## Baseline Grep 의무` § (raw/agents/*.md 안 등재) 의 pre/post-write 도구 호출 의무 자동 따름

### §0.2.2. SSoT (Single Source of Truth)

agent .md 본문의 진짜 source = **`E:\MCWiki_5_5_4\raw\ue-wiki-llm_5_5_4\agents\`** (vault active raw, 2026-05-27 — 5.5.4 fork 와 함께 canonical 이전). build source `C:\Unreal\UnrealEngine\LLM_Wiki\agents\` 는 mirror 또는 폐기.

병행 위치 `E:\MCWiki_5_5_4\raw\ue-wiki-llm\agents\` (5.7.4 vintage) 는 **frozen audit 사본** — 직접 수정 금지. §0.1 의 dual-raw 결정 일관성 유지. 향후 5.7.4 폴더 deprecate 시 함께 제거.

→ §8.1 "`raw/` 수정 금지" 원칙의 **예외 1건**: `raw/ue-wiki-llm_5_5_4/agents/` (canonical SSoT) 디렉토리는 LLM 도 수정 허용 (governance 작업 — Baseline Grep § append / orchestrator §5.4 본문 추가 / 신규 agent 정의 등).

### §0.2.3. 비교 (이전 vs 본 패턴)

| 항목 | Plugin (이전) | Emulation (본 패턴) |
| -- | -- | -- |
| Agent 정의 위치 | plugin ZIP 안 `agents/*.md` | vault `raw/ue-wiki-llm/agents/*.md` |
| 호출 방식 | `Task(subagent_type=)` | main 이 `read_raw` 흡수 |
| .md 변경 반영 | 재패키지 + install + Desktop 재시작 | 즉시 (main 이 매번 read_raw) |
| Isolated context window | ✅ subagent 별 | ❌ main context 안 누적 |
| Baseline Grep § append | 15 .md (plugin) + ZIP 재패키지 | 15 .md (vault raw) 직접 편집 |
| 권한 매트릭스 | plugin agent runtime + mcwiki MCP 분리 | mcwiki MCP 단독 (read_raw + 17 tools 모두) |

### §0.2.4. 한계

- main context window 누적 — 큰 작업 (코드 + 다수 라운드) 시 context 부담. 별도 Task subagent 호출 필요한 경우 = `general-purpose` 같은 generic subagent 에 컨텍스트 압축해서 위임.
- specialist 의 강제 의존성 분리 (예: `evaluator` 가 `specialist` 의 작업물을 평가하는 Article 1 분리) 시뮬레이션 불완전 — `[Evaluator]` prefix 사용 시 main 이 evaluator agent .md 흡수해서 self-eval bias 회피 시도하지만 진짜 분리는 아님.
- 본 한계 인지 후 사용 — Phase II G3+G4 게이트 시 plugin 시스템 복원 검토 옵션.

---

## §1. 미션

> 사용자의 raw 소스 위에, **누적·압축·교차 참조**되는 markdown wiki 를 LLM 이 유지보수한다.

- **누적**: 새 소스가 들어올 때마다 기존 wiki 가 풍부해지고, 모순은 명시적으로 드러난다.
- **압축**: 한 주제 = 한 페이지 (SSoT). 다른 페이지에서는 `[[wikilink]]` 만.
- **교차 참조**: 모든 핵심 주장에 `[[source]]` 또는 `[[entity]]` 인용.
- **사람의 역할**: sourcing, 탐구 방향, 좋은 질문. **LLM 의 역할**: 그 외 *모든* 잡일 (요약/cross-ref/일관성/maintenance).

---

## §2. 아키텍처 (3 layers)

| Layer | 경로 | 소유 | 변경 권한 |
| ----- | ---- | ---- | ------ |
| **Raw sources** | `raw/` | 사용자 | 사용자만 추가/삭제. **LLM 은 절대 수정 금지.** |
| **Wiki** | `wiki/` | LLM | LLM 이 자유롭게 생성/수정. 단 `§8 금기` 준수. |
| **Schema** | `CLAUDE.md` (이 파일), `AGENTS.md` (alias) | 사람 + LLM 공동 | 컨벤션 변경 시에만. 변경 시 `log.md` 에 schema-change 로 기록. |

```
MCWiki/
├── CLAUDE.md          ← 본 파일 (schema)
├── AGENTS.md          ← CLAUDE.md 의 1:1 사본 (Codex 호환)
├── README.md          ← 사용자용 quickstart
├── raw/               ← 불변 원본 (사용자만 손댐)
│   ├── README.md
│   ├── assets/        ← Obsidian 이 다운받은 이미지
│   ├── articles/      ← Web Clipper 등으로 클립한 글
│   ├── papers/        ← PDF 등
│   ├── youtube/       ← 자막 + 메타
│   ├── notes/         ← 자유 형식 메모
│   ├── ue-wiki-llm_5_5_4/   ← UE 5.5.4 active raw (223 md, §0.1)
│   └── ue-wiki-llm/         ← UE 5.7.4 audit reference (223 md, §0.1)
├── wiki/              ← LLM 이 만들고 유지
│   ├── index.md       ← 카탈로그 (§6)
│   ├── log.md         ← 시간순 append-only (§6)
│   ├── sources/       ← 1 raw 1 page (요약 + 인용)
│   ├── entities/      ← 사람/조직/논문/제품 등
│   ├── concepts/      ← 아이디어/프레임워크
│   └── synthesis/     ← 비교/오버뷰/진화하는 thesis
├── templates/         ← Templater 호환 스켈레톤
├── tools/             ← 운영 스크립트 (lint/stats/search/...)
└── docs/              ← Obsidian 셋업 등 부가 문서
```

---

## §3. 페이지 타입 (4종) + frontmatter 의무 필드

모든 wiki 페이지는 **YAML frontmatter** 로 시작한다. 누락 1개당 Quality 점수 -2.

### §3.1. source — `wiki/sources/<slug>.md`

원본 1개당 1 페이지. Ingest 시 항상 생성.

```yaml
---
type: source
title: <human-readable title>
slug: <kebab-case-id>
source_path: raw/<relative path>
source_kind: pdf | url | youtube | text | image | audio | video
source_date: YYYY-MM-DD
ingested: YYYY-MM-DD
related_entities: ["[[entities/...]]", ...]
related_concepts: ["[[concepts/...]]", ...]
tags: []
---
```

본문 4 절: 요약 / 핵심 주장 (인용 포함) / 인용할 만한 원문 / 열린 질문.

### §3.2. entity — `wiki/entities/<canonical-name>.md`

사람·조직·논문·제품·모델·데이터셋·장소·이벤트.

```yaml
---
type: entity
title: <canonical name>
aliases: [...]
kind: person | org | paper | product | model | dataset | place | event | other
sources: ["[[sources/...]]", ...]
tags: []
last_updated: YYYY-MM-DD
---
```

### §3.3. concept — `wiki/concepts/<slug>.md`

아이디어/프레임워크/기법.

```yaml
---
type: concept
title: <concept name>
aliases: []
sources: ["[[sources/...]]", ...]
related_concepts: ["[[concepts/...]]", ...]
tags: []
last_updated: YYYY-MM-DD
---
```

### §3.4. synthesis — `wiki/synthesis/<slug>.md`

비교·오버뷰·논점 정리.

```yaml
---
type: synthesis
title: <thesis or question>
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
sources: [...]
entities: [...]
concepts: [...]
status: draft | living | settled
tags: []
---
```

---

## §4. Wikilink 규약 (Obsidian 표준)

- **항상** `[[...]]` 사용. 마크다운 링크 (`[text](path)`) 는 외부 URL 에만.
- 형식 우선순위:
  1. **명시 경로**: `[[entities/Andrej Karpathy]]`
  2. **basename**: `[[Andrej Karpathy]]` (vault 내 unique 일 때만)
  3. **alias 표시**: `[[entities/Andrej Karpathy|Karpathy]]`
  4. **anchor**: `[[concepts/RLHF#PPO]]`
- frontmatter 의 `sources` / `related_*` 안에서는 따옴표로 감싼 wikilink 문자열: `["[[sources/foo]]"]`.
- 깨진 링크 = `tools/lint.py` 가 BROKEN_LINK 로 보고.

---

## §5. 운영 (3 operations)

### §5.1. INGEST workflow (10 steps)

**트리거**: 사용자가 `raw/` 에 파일을 떨어뜨리고 "ingest <path>" 또는 "이 글 흡수해줘".

1. **소스 읽기** (전체).
2. **slug 결정** (kebab-case).
3. **엔터티/컨셉 후보 추출**.
4. **기존 wiki 와 매칭**.
5. **사용자 확인** — OK 받기 전 파일 변경 금지.
6. **`wiki/sources/<slug>.md` 생성**.
7. **각 신규 entity/concept 페이지 생성/갱신**.
8. **`wiki/index.md` 갱신**.
9. **`wiki/log.md` append**: `## [YYYY-MM-DD] ingest | <title> | source: <slug> | touched: <N pages>`
10. **요약 보고**.

### §5.2. QUERY workflow (5 steps)

1. **`wiki/index.md` 먼저 읽기**.
2. **후보 페이지 전체 읽기**. wikilink 1-hop 추적.
3. **답변 작성** — 모든 핵심 주장에 `[[wikilink]]` 인용. **§13 Citation Rule 의무** — vault 인용 (🟢) / 외삽 (🟡) / 일반 지식 추론 (🔴) 을 항상 시각적으로 분리.
4. **filing-back 제안**: `wiki/synthesis/<slug>.md`.
5. **로그**.

### §5.3. LINT workflow

1. `python tools/lint.py` (기계적 점검).
2. LLM 의미적 점검 6종: contradictions / stale / mentioned-but-missing / orphan / underdeveloped / refactor candidates.
3. `wiki/synthesis/lint-<YYYY-MM-DD>.md` 보고서.
4. 사용자와 함께 처리.
5. `log.md` append: `## [YYYY-MM-DD] lint | <N issues>`.

### §5.4. AGENT BOUNDARY protocol (main ↔ specialist)

> 정밀판: [[00_meta/07_AgentBoundaryProtocol]]. 본 절은 마스터 schema 의 *의무 1단락 요약*.

**원칙**: vault 와 통신하는 도구(`mcwiki` MCP)는 **main Cowork 대화** 만 보유. `Task` tool 로 호출되는 specialist (`ue-wiki-llm:*` 등) 는 raw/wiki 파일 시스템만 접근 가능 → §5.2 QUERY 를 specialist 안에서 시행할 수 없다.

따라서 **main 이 boundary 마다 §5.2 를 wrap** 한다:

1. **PRE-DELEGATE** (specialist 호출 직전) — `read_index` + `search "<주제>"` → vault 에 이미 있는 것을 specialist 에 컨텍스트로 주입.
2. **DELEGATE** — `Task(subagent_type, prompt)`. specialist 는 작업물(코드/sub-skill 본문) 만 반환.
3. **POST-RECEIVE** (specialist 반환 직후) — (a) §13 Citation tier 분해 → 🟢 부분 인용 강화 / 🟡 부분 vault 갱신 후보 / 🔴 부분 `synthesis_seed` 후보. (b) **5-tier 카운트 정합 검사** (자산 추가/제거 cycle 일 때) — index.md 의 헤더 통계 / 섹션 헤더 / 카탈로그 항목 / 진척도 표 / 하단 통계 5 위치 cross-check. 자세히 [[00_meta/07_AgentBoundaryProtocol#§2.4]].
4. **FILE-BACK** — 사용자 OK 시 `write_page` / `synthesis_finalize`.
5. **LOG** — `append_log(op="query"|"synthesis"|...)` 자동.

**위반 = vault staleness**. specialist 호출 후 boundary §5.4 미적용 시 vault 가 자동 누적되지 않음. lint 가 잡지 못하는 *조용한* 부패.

**Phase II — C 점진 (선택)**: orchestrator agent (`ue-wiki-llm:ue-orchestrator`) 에 mcwiki MCP 권한을 추가하면 main 의 wrap 부담이 줄어듦. 단 plugin 재배포 필요 → 도구 변경 빈도 안정화 후 적용. detail = [[00_meta/07_AgentBoundaryProtocol#§3]].

---

## §6. index.md 와 log.md 포맷

### §6.1. `wiki/index.md`

```markdown
# Wiki Index

> Last updated: YYYY-MM-DD

## Sources (N)
- [[sources/...]] — 한 줄 설명 — N ingest

## Entities (N)
### People
### Organizations
### Papers
### Models
### Datasets

## Concepts (N)

## Synthesis (N)
```

### §6.2. `wiki/log.md`

Append-only. `grep "^## \[" log.md | tail -20`.

**op enum** ∈ {init, ingest, query, synthesis, lint, refactor, fix, feature, verify, doc, schema-change, note, bulk-import, bulk-seed, scaffold}.

#### §6.2.1 표준 entry 양식 (의무)

```markdown
## [YYYY-MM-DD] op | Title (1줄, 80자 이내 권장)

- 핵심 변경 1 (slug 또는 §X cross-link)
- 핵심 변경 2
- 검증 결과 (lint N issues / broken N / 등)
→ 자세히 [[synthesis/...]] §X 또는 [[sources/...]] §Y
```

**의무 항목**:
- ✅ 1줄 헤더 — `## [YYYY-MM-DD] op | Title`
- ✅ 3-5 bullet (간결, slug + cross-link 위주)
- ✅ verbose detail (코드 / 매트릭스 / 논의) → **synthesis/sources 페이지에 작성** + log 는 cross-link 만
- ✅ entry 크기 권장 **≤ 500 bytes (~10 라인)** — 큰 작업도 entry 는 짧게, 본문은 페이지에

#### §6.2.2 안티패턴 (금기)

```markdown
## [2026-05-13] feature | Big work — Phase 2a + 2b + 2c (9.3 KB)

(수십 라인 상세 보고)

### Sub-section A
(코드 블록 50+ 라인)

### Sub-section B
(매트릭스 표 / 함정 카탈로그 / 권위 인용 7건)
```

🔴 **위반** — log entry 가 9 KB 짜리 보고서가 됨. Karpathy schema 의 *append-only cross-ref index* 원칙 위반. 표준 대비 30x 비대.

→ **정정**: 본문은 `synthesis/big-work-phase-2-postmortem` 페이지로 이관, log 는:

```markdown
## [2026-05-13] feature | Big work Phase 2 (a/b/c) — refactor 2회 / synthesis 신규

- Phase 2a/2b/2c specialist 9 호출 (touched: 21 파일)
- refactor 사이클 2회 (시간 손실 ~390s)
- synthesis 신규: [[synthesis/big-work-phase-2-postmortem]]
- lint: 396 pages, 0 issues
```

#### §6.2.3 entry 크기 가이드

| 작업 규모 | entry 크기 권장 |
| -- | -- |
| 단일 변경 (1 파일 enrich / 1 typo fix) | ~200 bytes (5-7 라인) |
| 다중 변경 (cycle 1 phase / N 파일 patch) | ~400 bytes (8-10 라인) |
| 큰 작업 (multi-phase / synthesis 신규) | ~500 bytes (10-12 라인) + synthesis cross-link |
| **상한 (예외)** | **~1 KB** — 이 이상은 synthesis 페이지 의무 |

#### §6.2.4 filing-back 의무

verbose detail 이 발생하는 작업 (multi-step feature / refactor / postmortem) 은:

1. **synthesis 페이지 신규 작성** — 상세 본문 (코드 / 매트릭스 / 권위 인용 / 함정 카탈로그)
2. **log entry 는 cross-link 만** — synthesis slug + 1줄 요약

→ log = *index 역할*. detail = *synthesis* / *sources* 의 책임.

#### §6.2.5 압축 / archive 정책

log.md 가 **~500 KB 초과** 시 archive 검토:

- 오래된 날짜 부분 → `wiki/archive/log-YYYY-MM-weekN.md`
- archive 페이지는 `is_log_or_archive()` lint skip 대상 (lint.py 자동 적용 — Cycle 5p+1)
- active log.md 헤더에 archive pointer 명시
- 정책 페어: [[00_meta/04_AuditPolicy]] 의 분기별 audit 와 통합 (90일+ entry archive 후보)

---

## §7. 충돌 해결 (Conflict resolution)

| 상황 | 처리 |
| -- | -- |
| 새 source 가 기존 페이지의 주장과 모순 | **둘 다 보존**. `## Contradictions` 절에 두 주장 + 각 source. 사용자 결정. |
| 두 entity 가 같은 사물로 보임 | 자동 병합 금지. 사용자에게 alias 후보 제시. |
| concept 의 정의가 source 마다 다름 | `### As used in ...` 다중화. |
| 사용자 직접 편집 vs LLM 자동 갱신 충돌 | **사용자 항상 우선**. LLM 은 자기 갱신 되돌리기. |
| frontmatter `last_updated` 본문 변경 없이 갱신 | cross-link 추가만 했어도 OK. log.md 한 줄. |

---

## §8. 금기 (NEVER)

1. **`raw/` 수정 금지**. — 단 §0.2.2 **예외 1건**: `raw/ue-wiki-llm/agents/` 디렉토리는 LLM 도 수정 허용 (Plugin-less Agent Emulation 전제).
2. **wiki 페이지 무단 삭제 금지**. soft-delete: `deprecated: true` + redirect 1줄.
3. **출처 없는 주장 금지**. 모든 핵심 진술에 `[[source]]` 또는 `[[entity]]` 인용.
4. **마크다운 링크로 내부 페이지 가리키기 금지**. 항상 `[[wikilink]]`.
5. **인용 위조 금지**.
6. **자가 평가 금지** (Article 1).
7. **확실하지 않은 entity 합병 금지**.
8. **시간 의존 표현 금지** ("최근", "현재 최강" 등). `last_updated` + source date 로 묶음.
9. **slug ↔ 본문 언어 일관성 깨기 금지**. slug 는 영어 kebab-case, 본문은 한국어 권장.

---

## §9. 도구 cheat-sheet

```bash
python tools/lint.py            # 기계적 점검
python tools/stats.py           # 페이지 수 / 허브 / 고아 / freshness
python tools/search.py "BPE"    # naive grep search
python tools/ingest_seed.py "Title" raw/articles/x.md url
python tools/bulk_seed.py raw/ue-wiki-llm/skills/Animation/
python tools/youtube_to_raw.py https://www.youtube.com/watch?v=...
```

---

## §10. Co-evolution

본 파일은 *변경* 된다. 변경 절차:

1. 변경 이유를 한 줄로.
2. `python tools/lint.py` 전체 vault. 깨지는 페이지 식별.
3. 깨진 페이지 일괄 갱신.
4. `log.md` append: `## [YYYY-MM-DD] schema-change | <description>`
5. 사용자 알림.

---

## §11. 빠른 의사결정 표

| 상황 | LLM 행동 |
| -- | -- |
| 사용자가 raw 새 파일 두고 "ingest" | §5.1 INGEST 10단계. step 5 사용자 확인. |
| 사용자가 자연어 질문 | §5.2 QUERY 5단계. filing-back 제안. |
| 사용자가 "lint" / "건강 진단" | `tools/lint.py` → §5.3 의미 점검 → 보고서. |
| **UE 5.5.x 콘텐츠 작업** | **§0.1 동행 정책 추가 적용**. UE 특화 raw 정책의 정밀도 우선. |
| **`Task` tool 로 specialist 호출** | **§5.4 AGENT BOUNDARY**. PRE-DELEGATE QUERY → DELEGATE → POST-RECEIVE §13 분해 → FILE-BACK → LOG. main 이 wrap. |
| entity 이름 모호 | 사용자에게 후보 제시, 자동 병합 금지. |
| source 의 주장이 기존과 모순 | 두 주장 보존 + `## Contradictions`. |
| wikilink 가 없는 페이지를 만들고 싶을 때 | OK. lint 가 ORPHAN 으로 잡을 것 — 사용자 확인. |
| raw vs wiki/sources 헷갈림 | 원본은 raw, 요약/추출/재해석은 wiki/sources. *둘 다*. |

---

## §12. 부록 — 참고 패턴

- Karpathy gist (원전): <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Vannevar Bush 1945, "As We May Think"

---

## §13. Vault Citation & Inference Disclosure Rule

> 정밀판: [[00_meta/06_VaultCitationRule]]. 본 절은 마스터 schema 의 *의무 1단락 요약*.

mcwiki MCP 로 vault 를 읽고 답변하는 모든 agent (Cowork / Claude Code / specialist subagent) 는 답변에 포함된 *모든 사실 주장* 을 다음 3 tier 로 시각 분리해야 한다:

| Tier | 의미 | 마커 |
| -- | -- | -- |
| 🟢 **VAULT** | `read_page` / `read_raw` 로 직접 확인 | `[[wikilink]]` 인용 |
| 🟡 **PARTIAL** | vault 근거 일부 + 외삽 | "(vault 근거: [[…]] · 외삽)" |
| 🔴 **INFERRED** | vault 없음 — 일반 지식 / 코드 추론 | "**추론 (vault 미확정)**" prefix 또는 별도 섹션 |

**§13 위반 = 거짓 인용과 동등**. 사용자가 어느 주장이 검증된 vault 자산이고 어느 것이 LLM 의 추측인지 한 줄로 구별 가능해야 한다.

특히 `search` 가 0 hits 였거나 read_page 에 답이 없으면 그 부분은 **반드시 🔴 INFERRED 섹션** 으로 분리:

```markdown
### vault 검색했지만 결과 없음 — 추론에 의존한 부분
- <항목> ... — vault 미확인 / 내 일반 UE 지식
```

[[sources/ue-agent-evaluator]] 의 평가에 §13 위반 시 감점. filing-back 결정 (`query_recap` mode) 도 §13 결과에 따라 — 🔴 가 가치 있으면 `mode=propose_synthesis` 로 vault 화 사이클 진입.

🔴 → 검증 → 🟢 사이클이 *살아있는 vault* 의 핵심.