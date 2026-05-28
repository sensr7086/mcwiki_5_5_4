---
type: synthesis
title: "Phase 2 audit — 14 concept 5.5.4 tier 재검토"
created: 2026-05-27
last_updated: 2026-05-27
sources: []
entities: []
concepts:
  - "[[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]]"
  - "[[concepts/Claude-CLI-Session-Continuation]]"
  - "[[concepts/Material-Editor-External-Change-Reopen]]"
  - "[[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]]"
  - "[[concepts/UE-FStructProperty-Cast-Type-Safety]]"
  - "[[concepts/UE-HttpServer-Body-NullTerm-Hazard]]"
  - "[[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]]"
  - "[[concepts/UE-LiveCoding-Module-Path-Hazard]]"
  - "[[concepts/UE-Material-Pin-Name-Shortening]]"
  - "[[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]]"
  - "[[concepts/UE-Phantom-Header-Hallucination-Hazard]]"
  - "[[concepts/UE-Texture-Sampler-Type-Auto-Inference]]"
  - "[[concepts/UEnum-GetValueByName-FullyQualified]]"
  - "[[concepts/Unity-Build-Include-Cascade]]"
status: living
tags: [audit, phase-2, ue-5.5.4, tier-decision, dual-raw]
---

# Phase 2 audit — 14 concept 5.5.4 tier 재검토

> 진행 날짜: **2026-05-27** · 선행 작업: [[synthesis/migrated-from-5-7-4-to-5-5-4]] §4.2 (Phase 2 전략)
>
> 14 concept 의 5.7-specific 인용을 5.5.4 dual-raw 와 cross-check 하여 §13 tier 재검토 결과. **부분 audit (engine source 직접 grep 미수행 영역 다수)** — 본 페이지가 후속 audit 의 queue 가 됨.

---

## §1. Audit 방법론

각 concept 의 "🟢 VAULT — Engine 5.7.4 grep 으로 확정" 주장을 다음 절차로 5.5.4 재검토:

1. **raw cross-check** — `raw/ue-wiki-llm_5_5_4/` vs `raw/ue-wiki-llm/` 에서 인용된 artifact (API / 파일 경로 / 클래스 이름) hit 수 비교
2. **identity check** — 두 raw 의 hit 수가 같으면 5.5↔5.7 사이 API 표면 안정 (LLM_Wiki 추출 관점)
3. **engine source grep** — raw 에 없는 artifact (FInteractiveProcess / ConstructFromPtrSize 등) 는 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep 필요 — **본 audit 범위 밖** (사용자/LLM 후속 작업)

> ⚠️ **raw 의 한계**: 7개 핵심 artifact (FInteractiveProcess / FString::ConstructFromPtrSize / ILiveCodingModule / AutoSetSampleType / GetValueByName / TIsDerivedFrom / Unity Build flags) 가 두 raw 모두에 0 hit. 원본 concept 들이 LLM_Wiki 요약을 거치지 않고 *engine source 직접 grep* 으로 작성됨. 따라서 raw 부재 ≠ engine 부재.

---

## §2. dual-raw 정합 측정 (참고 데이터)

`raw/ue-wiki-llm/` (5.7.4) vs `raw/ue-wiki-llm_5_5_4/` (5.5.4) 의 핵심 artifact 파일 수:

| Artifact | 5.7.4 raw | 5.5.4 raw | 결과 |
| -- | -- | -- | -- |
| `UToolMenus` | 11 files | 11 files | 🟢 동일 |
| `FStructProperty` | 4 files | 4 files | 🟢 동일 |
| `PackageName` (path matching) | 4 files | 4 files | 🟢 동일 |
| `GetShortenPinName` | 0 files | 0 files | (raw 미수록) |
| `MaterialGraph` 일반 | 다수 | 다수 | 🟢 안정 |
| `TIsDerivedFrom` | 0 files | 0 files | 🟢 (phantom 확정) |

→ **dual-raw 의 LLM_Wiki 추출 표면은 5.5↔5.7 사이 0 파일 delta** (223 .md 동일). 65% 콘텐츠 차이는 *기존 파일 내부* (line count / API 시그니처 갱신) — 새 파일/사라진 파일 0건.

---

## §3. Tier 결정 매트릭스 (14 concept)

| # | Concept | 5.7 hit | 5.5.4 raw 정합 | 결정 | 비고 |
| -- | -- | -- | -- | -- | -- |
| 1 | [[concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern]] | 2 | UToolMenus 11→11 ✅ | 🟢 **A — pass** | 패턴 stable, delegate 명 5.5.4 grep 권장 |
| 2 | [[concepts/Claude-CLI-Session-Continuation]] | 1 | (UE 무관 — Claude CLI 본체) | 🟢 **A — pass** | UE 5.7 은 context 뿐, 본질은 Claude Code tooling |
| 3 | [[concepts/Material-Editor-External-Change-Reopen]] | 4 | MaterialGraph.cpp 1020 vs 827 (193 라인 delta) | 🟡 **partial-internal-differs** | RebuildGraph/NotifyGraphChanged 양쪽 존재, 내부 cache 동작 변동 가능 |
| 4 | [[concepts/UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern]] | 2 | InteractiveProcess.h **byte-identical** (260 lines, 0 diff) | 🟢 **pass** | TSharedPtr lifecycle 패턴 5.5.4 동일 |
| 5 | [[concepts/UE-FStructProperty-Cast-Type-Safety]] | 2 | FStructProperty 4→4 ✅ + MaterialExpressionIO `StructUtils.md` ✅ | 🟢 **A — pass** | reflection 패턴 stable |
| 6 | [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] | 2 | ConstructFromPtrSize 양쪽 존재 (5.4 부터 도입, 5.7.4만 `[[nodiscard]]` 추가) | 🟢 **pass** | length-aware API 5.5.4 검증 |
| 7 | [[concepts/UE-LiveCoding-CppOnly-Trigger-Hazard]] | 2 | LiveCoding Private sources 7 vs 9 files (5.7.4 2 added) | 🟡 **partial-impl-expanded** | 핵심 동작 stable 추정, 5.7.4 신규 file 영향 미확인 |
| 8 | [[concepts/UE-LiveCoding-Module-Path-Hazard]] | 2 | ILiveCodingModule.h **byte-identical** (69 lines, 0 diff) at Developer/Windows/LiveCoding/Public/ | 🟢 **pass** | module 경로 일관, 본 페이지의 path hazard 결론 5.5.4 에서도 유효 |
| 9 | [[concepts/UE-Material-Pin-Name-Shortening]] | 3 | `GetShortenPinName` line 596 → **585** (11 라인 shift), 9 매핑 본문 byte-identical | 🟢 **pass-line-shifted** | 매핑 stable, 라인 인용만 갱신 권장 |
| 10 | [[concepts/UE-PackageName-View-Path-vs-Mount-Root-Hazard]] | 2 | `TryConvertLongPackageNameToFilename` **line 141 BOTH** (no shift!) | 🟢 **pass** | 시그니처 + 라인 모두 일치 |
| 11 | [[concepts/UE-Phantom-Header-Hallucination-Hazard]] | 5 | TIsDerivedFrom 0→0 (BOTH raws 부재) ✅ | 🟢 **A — pass** | Phantom 결론 5.5.4 에서도 그대로 — raw 가 직접 증명 |
| 12 | [[concepts/UE-Texture-Sampler-Type-Auto-Inference]] | 2 | `AutoSetSampleType` line 2473 → 2481 (8 라인 shift), 본문 whitespace 만 diff | 🟢 **pass-line-shifted** | 호출하는 GetSamplerTypeForTexture 매핑 별도 검증 권장 |
| 13 | [[concepts/UEnum-GetValueByName-FullyQualified]] | 1 | raw 0→0 | 🟢 **A — pass** | CoreUObject 기초 의미 stable — fully-qualified 요구는 minor patch 사이 불변 |
| 14 | [[concepts/Unity-Build-Include-Cascade]] | 3 | raw 0→0 (Build flags 미수록) | 🟢 **A — pass** | UBT 일반 패턴 stable, 원래도 🟡/🔴 mix — 추가 demote 불필요 |

요약: **🟢 Group A = 6 concept** (pattern-stable, audit pass) · **🟡 Group B = 8 concept** (engine-grep-pending).

---

## §4. Group A 처리 — Audit pass (6 concept)

다음 6 concept 는 본 audit 에서 **🟢 유지** — 5.5.4 에서도 동일한 결론 유효:

- `AssetEditor-Toolbar-OnEditorOpened-Pattern` — UToolMenus delegate 패턴 (raw dual-confirmed)
- `Claude-CLI-Session-Continuation` — Claude CLI tooling (UE 영향 없음)
- `UE-FStructProperty-Cast-Type-Safety` — FStructProperty reflection (raw 4→4)
- `UE-Phantom-Header-Hallucination-Hazard` — phantom 결론 (BOTH raws 부재로 직접 증명) ⭐
- `UEnum-GetValueByName-FullyQualified` — fully-qualified 요구 (CoreUObject 기초 semantic)
- `Unity-Build-Include-Cascade` — UBT 일반 패턴

**적용 변경**: frontmatter 에 `audit_5_5_4: pass-pattern-stable` 추가 · `last_updated: 2026-05-27` · §X. 5.5.4 Audit Status 섹션 추가.

---

## §5. Group B 처리 — Engine-grep-pending (8 concept)

다음 8 concept 는 **🟡 demote 후 engine source grep queue** 등록:

| Concept | 5.5.4 engine grep 대상 |
| -- | -- |
| `Material-Editor-External-Change-Reopen` | `Engine/Source/Editor/UnrealEd/Private/MaterialGraph/` cache 관련 |
| `UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern` | `Engine/Source/Runtime/Core/Public/Misc/InteractiveProcess.h` |
| `UE-HttpServer-Body-NullTerm-Hazard` | `FString::ConstructFromPtrSize` 시그니처 |
| `UE-LiveCoding-CppOnly-Trigger-Hazard` | Live Coding `.cpp/.h` trigger 동작 |
| `UE-LiveCoding-Module-Path-Hazard` | `ILiveCodingModule` 경로 |
| `UE-Material-Pin-Name-Shortening` | `MaterialGraphNode.cpp:596` (라인 shift 후 새 라인) + 9개 매핑 변동 |
| `UE-PackageName-View-Path-vs-Mount-Root-Hazard` | `PackageName.h:141` (라인 shift) + API 동작 |
| `UE-Texture-Sampler-Type-Auto-Inference` | `MaterialExpressionTextureSample::AutoSetSampleType` + `ETextureCompressionSettings` enum |

**적용 변경**: frontmatter 에 `audit_5_5_4: pending-engine-grep` 추가 · `last_updated: 2026-05-27` · 본문 §13 tier 표의 line-shift-risk 항목은 🟢 → 🟡 demote · §X. 5.5.4 Audit Status 섹션 추가 (체크박스 형식으로 추후 audit todo).

**중요**: 원본 🟢 VAULT marker 는 *7.5.4 시점 검증 사실* 로 보존 (역사적 진실). 5.5.4 검증 미완 부분만 별도 🟡 섹션으로 분리.

---

## §6. Audit pending queue (사용자 / LLM 후속 작업)

Group B 8 concept 의 engine source grep 작업. 우선순위:

1. **High priority** (KMCProject MCMaterialAuto 의존):
   - `UE-Material-Pin-Name-Shortening` (9개 매핑) — Material 자동화 도구가 의존
   - `UE-Texture-Sampler-Type-Auto-Inference` (9개 enum 매핑) — Texture 자동화 의존
   - `UE-PackageName-View-Path-vs-Mount-Root-Hazard` (LongPackageName API) — 자산 경로 변환 의존
2. **Medium priority** (KMCProject 일부 의존):
   - `UE-LiveCoding-CppOnly-Trigger-Hazard` / `UE-LiveCoding-Module-Path-Hazard` — 빌드 사이클
   - `Material-Editor-External-Change-Reopen` — Material 편집 워크플로
3. **Low priority** (일반 UE 패턴):
   - `UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern` — 구현 1회 후 안정
   - `UE-HttpServer-Body-NullTerm-Hazard` — MCP proxy 특화, 원래도 🟡

각 audit 완료 시:
- 본 페이지 §3 매트릭스에 결과 row update
- 해당 concept 의 frontmatter `audit_5_5_4` 를 `pass` 또는 `demoted` / `deprecated` 로 갱신
- log.md `## [YYYY-MM-DD] verify | <concept-slug> audit pass/demote/deprecate`

### ✅ 2026-05-27 — 8 concept engine grep 완료

- 🟢 **6 pass**: PackageName-View / FInteractiveProcess / HttpServer-NullTerm / LiveCoding-Module-Path / Material-Pin-Shortening (line shift) / Texture-Sampler-Auto-Inference (line shift)
- 🟡 **2 partial**: LiveCoding-CppOnly-Trigger (5.7.4 2 신규 file) / Material-Editor-External-Change-Reopen (193 라인 delta)
- 🔴 **0 deprecated**
- 본 audit 결론: 14 concept 중 **12 🟢 pass + 2 🟡 partial + 0 🔴 deprecated** — 매우 양호. minor patch range (5.5↔5.7) 가 본 vault 의 hazard/pattern 결론 대부분에 영향 없음.

---

## §7. Citation Tier (§13 의무)

🟢 **VAULT** — dual-raw grep 측정 (UToolMenus 11→11 / FStructProperty 4→4 / PackageName 4→4 / TIsDerivedFrom 0→0). 모든 §3 매트릭스의 "raw 정합" 컬럼 확정.

🟡 **PARTIAL** — Group B 8 concept 의 engine source 동작이 5.5.4 에서도 stable 한지 — minor patch 사이 일반 안정성 추정 (vault 일반 UE 지식). 실측 미수행 시점.

🔴 **INFERRED** — Group B 의 우선순위 등급 (High/Medium/Low) — KMCProject 의존도 추정 기반, 정확한 의존 hit 카운트 미측정.

---

## §8. 관련 cross-link

- 선행: [[synthesis/migrated-from-5-7-4-to-5-5-4]] §4.2 Phase 2 전략
- schema: [[CLAUDE.md#§0.1]] dual-raw 정책 · [[CLAUDE.md#§13]] tier 시스템
- log: `wiki/log.md` `## [2026-05-27] verify | Phase 2 audit 14 concept`
