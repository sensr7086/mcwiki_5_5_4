---
type: synthesis
title: "UE 5.7.4 → 5.5.4 vault fork 기록 (migration synthesis)"
created: 2026-05-27
last_updated: 2026-05-27
sources: []
entities: []
concepts: []
status: living
tags: [migration, schema-change, vault-fork, ue-5.5.4]
---

# UE 5.7.4 → 5.5.4 vault fork 기록

> Fork 일자: **2026-05-27** · Source: `E:\MCWiki` (5.7.4 frozen) · Target: `E:\MCWiki_5_5_4` (5.5.4 active, this vault)
>
> 본 페이지는 log.md `## [2026-05-27] schema-change` entry 의 verbose detail. §6.2.4 filing-back 의무 — 큰 작업의 상세는 synthesis 페이지에, log 는 cross-link 만.

---

## §1. 마이그레이션 배경

사용자 (sensr7086@naver.com) 의 UE 엔진을 **5.7.4 → 5.5.4 로 downgrade migrate**. 5.7.4 기준 누적된 vault (`E:\MCWiki`) 를 통째 보존 (frozen archive) 하고, 5.5.4 active vault 를 `E:\MCWiki_5_5_4` 에 fork.

선택 옵션 평가 (대화 2026-05-27):

| 옵션 | 결과 |
| -- | -- |
| 1: vault 전체 5.5.4 로 in-place 전환 | 거부 — 5.7.4 역사 / mc- case study 손실 risk |
| 2-a: 단일 vault 에 5.5.4 raw 병행 추가 | 거부 — schema 복잡도 폭증 (모든 claim version qualifier 의무) |
| **2-b: 5.7.4 완전 분리 + selective harvest (채택)** | E:\MCWiki frozen + E:\MCWiki_5_5_4 fork |
| 실행: PowerShell rename vs Ctrl+C/V | **사용자 Ctrl+C/V 채택** — 원본 무손상, mcwiki MCP 서버 유지 |

---

## §2. 인계된 자산 (Ctrl+C/V 전체 복사)

| 영역 | 상태 | 비고 |
| -- | -- | -- |
| `CLAUDE.md` / `AGENTS.md` | ✅ identity 라벨 5.5.4 로 치환 완료 | 5.7-historical context 5건 잔존 (의도) |
| `wiki/index.md` | ✅ §0 scope identity 5.5.4 로 갱신 | 통계 (227/97/75/59) 는 5.7.4 vintage 라벨로 보존 |
| `wiki/log.md` (15,347 라인) | ✅ §6.2 append-only — 5.7.4 역사 그대로 보존 + schema-change entry append | 향후 archive 정책 (§6.2.5 — 500 KB 초과) 별도 검토 필요 |
| `wiki/00_meta/` (10 페이지) | ✅ 그대로 — schema 메타는 version 무관 | — |
| `wiki/entities/` (97) | ⚠️ 인계 — 대부분 version-agnostic, 일부 audit 필요 | — |
| `wiki/sources/` (227) | ⚠️ 인계 — 5.7.4 raw 요약, raw sync 후 재인용 검증 필요 | — |
| `wiki/concepts/` (75) | ⚠️ 인계 — **14개 5.7-specific 명시 → tier-demote audit 대기** | 목록 §3 |
| `wiki/synthesis/` (59) | ⚠️ 인계 — 5.7 시대 thesis 일부 stale 가능 | — |
| `raw/ue-wiki-llm_5_5_4/` (active) | ✅ 5.5.4 추출 완료 (2026-05-27) — 223 .md / 3.2 MB | sync 명령: §0.1 |
| `raw/ue-wiki-llm/` (audit ref) | ⚠️ 5.7.4 vintage 보존 — Phase 2 diff 비교용 | Phase 4 에서 선택적 deprecate |
| `raw/{articles,papers,youtube,notes,assets}/` | ✅ 그대로 — UE version 무관 | — |
| `tools/` · `templates/` · `README.md` | ✅ 그대로 | — |

추가 인계 (vault 본 구조 외 아티팩트 — 향후 정리 고려):

- `mcwiki-0.X.X.mcpb` (7 파일 ~16 MB) — 빌드 산출물
- `dist/` · `_check/` · `_check_mcpb/` · `audit_results/` · `backup/` · `outputs/` · `.venv/` — 빌드/런타임
- `.obsidian/` · `manifest.json` · `.mcpbignore`

→ 이들은 본 vault 작업과 직접 관계 없음. 향후 `git status` 등으로 사용자 확인 후 정리 권장.

---

## §3. Audit 대기 목록 — 14개 5.7-specific concept

5.7.x API / 시그니처 / 동작을 **명시 인용** 하는 concept 페이지 — 5.5.4 raw sync 후 §13 tier 재검토 (🟢 유지 / 🟡 demote / 🔴 deprecate) 의무.

- `AssetEditor-Toolbar-OnEditorOpened-Pattern`
- `Claude-CLI-Session-Continuation`
- `Material-Editor-External-Change-Reopen`
- `UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern`
- `UE-FStructProperty-Cast-Type-Safety`
- `UE-HttpServer-Body-NullTerm-Hazard`
- `UE-LiveCoding-CppOnly-Trigger-Hazard`
- `UE-LiveCoding-Module-Path-Hazard`
- `UE-Material-Pin-Name-Shortening`
- `UE-PackageName-View-Path-vs-Mount-Root-Hazard`
- `UE-Phantom-Header-Hallucination-Hazard`
- `UE-Texture-Sampler-Type-Auto-Inference`
- `UEnum-GetValueByName-FullyQualified`
- `Unity-Build-Include-Cascade`

추가 hit 가능 (검색 limit 50 으로 캡됨 — sources/ synthesis/ entities/ 영역 전수 grep 미수행). Task #7 검증에서 보강.

---

## §4. Phase 로드맵 — 5.5.4 vault 정상화

### Phase 0 — Fork 직후 (✅ 2026-05-27 완료)

- E:\MCWiki_5_5_4 Ctrl+C/V 완료
- CLAUDE.md / wiki/index.md 라벨 갱신
- log.md schema-change entry append
- 본 MIGRATED_FROM.md 작성

### Phase 1 — raw 추출 (✅ 사용자 완료, 2026-05-27)

5.5.4 엔진 기준 LLM_Wiki 추출 완료. **사용자 결정**: cp -r overwrite (단일 raw) 대신 **dual-raw 병행 구조** 선택 —

```
E:\MCWiki_5_5_4\raw\
├── ue-wiki-llm_5_5_4\    ← 신규 active raw (5.5.4) · 223 .md · 3.2 MB
└── ue-wiki-llm\           ← 인계 audit reference (5.7.4) · 223 .md · 3.2 MB
```

콘텐츠 측정 결과 (2026-05-27):

| 영역 | 동일 | 차이 | 비고 |
| -- | -- | -- | -- |
| 전체 .md 223 | **78 (34%)** | **145 (65%)** | file 누락/추가 0 |
| references/ (정책) | 다수 동일 | 일부 라벨 (5.7.4 → 5.5.4) | 패턴 자체 안정 |
| skills/ (API) | 소수 | 다수 | line count / 시그니처 delta 다수 |
| agents/ (SSoT) | 15 전부 동일 | 0 | byte-identical (timestamp 만 다름) |

대표 delta 예시:
- `references/07_ProfilingScopeRule.md` — "5.7.4 트리" → "5.5.4 트리" + 검증 일자 (정책 자체 stable)
- `skills/Animation/SKILL.md` — `UAnimInstance` 1,776 lines → **1,705 lines** (실제 engine source 축소)

### Phase 2 — wiki/ audit (🟡 다음 단계, LLM 작업)

dual-raw 활용 audit 전략:

1. **broken_link 검사** — `tools/lint.py` 또는 `find_cross_link_broken` 으로 raw 인용 무결성 확인. 현재 모든 인용이 `[[raw/ue-wiki-llm/...]]` (5.7.4) 로 작동 → 자연스럽게 통과.
2. **14 concept tier-demote audit** — 위 §3 목록의 5.7-specific concept 페이지 각각:
   - 동일 주제 raw 페어 (`ue-wiki-llm/...` vs `ue-wiki-llm_5_5_4/...`) diff
   - 차이 발견 → §13 tier 갱신 (🟢 → 🟡 또는 🔴) + 5.5.4 grep 으로 재검증
   - 차이 없음 → 🟢 유지 (정책 stable)
3. **sources/ 227 페이지 점진 redirect** — audit 통과 시 `[[raw/ue-wiki-llm_5_5_4/...]]` 로 인용 갱신. §0.1 의 raw 경로 규약 따름.
4. **MANIFEST.md sync** — 신규 `[[sources/ue-manifest]]` 페이지를 5.5.4 raw 카탈로그로 재생성 (현 sources/ue-manifest 는 5.7.4 vintage).
5. **synthesis/ stale 검토** — 5.7 시대 thesis 중 5.5.4 에서 무효화된 것 deprecate 마커.

### Phase 3 — 5.5.4 신규 ingest (지속)

5.5.4 엔진의 신규 사례 / KMCProject 5.5.4 빌드 회기 등을 §5.1 INGEST 워크플로 따라 누적. 신규 인용은 모두 `[[raw/ue-wiki-llm_5_5_4/...]]` 사용.

### Phase 4 — 5.7.4 audit reference deprecate (장기, 선택)

Phase 2 완료 후 사용자가 5.5↔5.7 diff 필요 없다고 판단하면 `raw/ue-wiki-llm/` 폴더 삭제 가능. 5.7.4 자료는 `E:\MCWiki` frozen archive 에 영구 보존되어 있으므로 무손실. 현재 시점에서는 audit 진행 중 — 유지.

---

## §5. 5.7.4 frozen archive (E:\MCWiki) 정책

- **read-only** 취급. 직접 편집 금지 (선언적).
- mcwiki MCP 서버는 현재 `E:\MCWiki` 를 root 로 가정 — 5.7.4 vault read-only reference 로 그대로 사용 가능. `read_page` / `read_raw` / `search` 모두 5.7.4 vault 대상.
- 향후 5.5.4 vault 용 mcwiki MCP 서버 별도 설정 시 — 두 서버 공존 (5.7.4 read-only + 5.5.4 active read-write).
- 사용자가 원하면 `E:\MCWiki\ARCHIVED.md` 수동 추가 (read-only 정책 명시) — 본 vault 측에서 직접 쓰기 불가 (mount 미포함).

---

## §6. Citation Tier (§13 의무)

🟢 **VAULT** — 본 페이지의 모든 사실 (인계 자산 카운트 / 14 concept 목록 / 옵션 결정 시퀀스) 은 2026-05-27 대화 + 직접 vault 측정 (`grep "5\.7"` / `ls raw/ue-wiki-llm/`) 기반.

🟡 **PARTIAL** — §4.2 의 14 concept 가 audit 후 어떤 tier 로 분류될지의 예측 — 5.5.4 raw 미보유 상태 정량 불가.

🔴 **INFERRED** — §2 의 "5.7-historical context 5건 잔존 (의도)" 의 *정확한 5건 위치* — 본 페이지 작성 시점 grep 5건 정확 일치는 확인했으나 본문 인용은 본 페이지에 미수록 (CLAUDE.md / wiki/index.md grep 결과로 cross-check 권장).

---

## §7. 관련 cross-link

- log entry: `wiki/log.md` § `## [2026-05-27] schema-change | UE 5.7.4 → 5.5.4 vault fork`
- schema: [[CLAUDE.md#§0.1]] (UE 도메인 raw 참조 정책)
- citation tier: [[CLAUDE.md#§13]] · [[00_meta/06_VaultCitationRule]]
- audit policy: [[00_meta/04_AuditPolicy]] · [[CLAUDE.md#§10]]
