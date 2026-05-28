# Cycle 5k Patch Bundle — v0.3.1 patch + LLM mode PR + vault audit batch

> **목적**: Cycle 5j v0.4.0 적용 성공 후, 도구 #1 false positive 회피 + 도구 #3 LLM mode 보완 + vault 전체 audit 자동화 첫 실행.

## Phase 1 — v0.4.0 3 신규 도구 검증 ✅

`suggest_missing_cross_link` + `find_claim_conflict` + `find_stale_baseline` 핵심 페이지 호출 → 모두 정상 작동.

**주요 발견**:
- `uobject` outbound 25 / inbound **46** — vault 의 가장 인용되는 페이지 (UObject 베이스)
- `find_claim_conflict` 휴리스틱 false positive 1건 — keyword "종" (Cycle 5k Phase 3 LLM mode 보완 trigger)
- `find_stale_baseline` 정상 — 모든 페이지 age 0-3d (vault 매우 active)

## Phase 2 — `find_cross_link_broken` v0.3.1 patch ✅

**파일**: `find_cross_link_broken_v0.3.1.py`

**핵심 변경**:
- `strip_code_blocks_preserve_lines()` 헬퍼 — code block + inline code 안 wikilink 무시
- **라인 번호 보존** — 코드 블록 줄들을 빈 공백 + 줄바꿈으로 치환 (Cycle 5j suggest_missing_cross_link 의 단순 strip 보다 정밀)

**적용 효과**:
- Cycle 5j Phase 1 의 `ue-meta-baseline-grep-system` §5.1 `[[wikilink]]` literal false positive 회피
- broken 1 → **0** 격상 (예상)

**비고**: 도구 v0.3.1 description 에 이미 "strip_code_blocks() applied" 명시 — **사용자가 이미 적용한 가능성 높음**. 본 PR 코드는 *라인 번호 보존* 버전 (preserve_lines) — 향후 reference 적용 권장.

## Phase 3 — `find_claim_conflict` LLM mode PR ✅

**파일**: `find_claim_conflict_llm_mode.py`

**핵심 발전 (v0.4.0 → v0.4.1)**:
- `use_llm=True` 옵션 추가 — Claude Haiku 3.5 호출
- `LLM_VERIFICATION_PROMPT` — keyword + line context 2 페이지 → "is_real_conflict: bool + reason" JSON 응답
- 휴리스틱 충돌 detect 후 LLM 검증 → false positive 강등 (`severity="false_positive"` + `llm_filtered=True`)

**Cycle 5k Phase 4 false positive 시나리오**:
- `asseteditorapi vs toolmenus` keyword "개" (9개 vs 1/5개) — LLM 이 "다른 문맥" 판단 → 강등

**LLM provider 통합 요구**:
- 환경변수 `ANTHROPIC_API_KEY` 또는 mcwiki extension 의 `MCWIKI_LLM_API_KEY`
- 본 PR 코드는 `call_haiku_llm` stub — mcwiki extension 통합 시 anthropic SDK 호출로 대체
- 모델: `claude-haiku-4-5-20251001` (또는 v0.4.1 시점 최신)

## Phase 4 — vault 전체 audit batch ✅

핵심 8 페이지 4 도구 호출 — 결과 종합:

### A. suggest_missing_cross_link (4 페이지)

| 페이지 | missing reverse-link |
| -- | -- |
| uobject | 6 (improvement-roadmap 4x **high** + meta 4종 + synthesis 3) |
| asseteditorapi | 4 (hit-reaction 3x + combo 3x + unrealed-subsystems 2x + bp-scs 2x) |
| personatoolkit | 2 (combo 4x + assetuserdata 2x) |
| combo-editor (synthesis) | 1 (levelsequence-skill 1x) |
| **합계** | **13 missing — Cycle 5l 보강 후보** |

### B. find_claim_conflict (2 페어)

| 페어 | conflicts | 비고 |
| -- | -- | -- |
| asseteditorapi vs toolmenus | 1 ⚠ false positive | keyword "개" — LLM mode 필요 |
| uobject vs mc-asset-validation | 0 ✅ | 일관성 검증 |

### C. find_stale_baseline (threshold 90d)

| 페이지 | age | stale |
| -- | -- | -- |
| ue-ref-07-profilingscopeRule | 2d | false ✅ |
| ue-render-skill | 3d | false ✅ |

### D. ⚠ find_cross_link_broken — `00_meta/` broken 5건 발견

**baseline-grep-system §9 Cross-link** — 5 wikilinks 가 broken:
- `00_meta/00_QualityCriteria` / `03_EvaluatorRecipe` / `05_HandoffProtocol` / `06_VaultCitationRule` / `07_AgentBoundaryProtocol`

**`lint` 결과 (broken=0) 와 불일치** — 두 도구의 `00_meta/` 인식 로직 차이.

도구 description 은 `00_meta/` 인식 명시하나 실제 디렉토리 매핑이 다를 가능성. **Cycle 5l 도구 정합성 검증 후보**:
1. `00_meta/` 가 vault 실제 디렉토리인가? (vs sources/, entities/ 등의 *디렉토리 이름*)
2. `lint` 가 `00_meta/` 를 검사하지 않는가? (governance protected 영역으로 분류?)
3. `find_cross_link_broken` 의 `00_meta` 인식이 실제 file system path 와 다른가?

## 적용 절차

### Phase 2 v0.3.1 patch 적용 (선택 — 도구 이미 적용된 가능성 높음)

```bash
# mcwiki extension server 모듈 위치
# %USERPROFILE%\AppData\Roaming\Claude\Claude Extensions\local.mcpb.x...\mcwiki\

# 기존 find_cross_link_broken.py 백업 후 본 patch 로 교체
cp find_cross_link_broken_v0.3.1.py <mcwiki>/find_cross_link_broken.py

# manifest version: v0.3.0 → v0.3.1.lines_preserved (또는 사용자 시점 최신)
```

### Phase 3 LLM mode 적용

```bash
# 본 patch 는 mcwiki extension 의 LLM provider 통합 필요
# 1. anthropic SDK 의존성 추가 (requirements.txt 또는 pyproject.toml)
# 2. ANTHROPIC_API_KEY 환경변수 (또는 mcwiki 통합 키)
# 3. find_claim_conflict_llm_mode.py 의 call_haiku_llm() stub 을 실제 anthropic SDK 호출로 교체
# 4. mcwiki manifest version: v0.4.0 → v0.4.1.llm_mode

# 호출 시:
# find_claim_conflict(slug_a, slug_b, use_llm=true)
```

## Cycle 5l 후보 풀

1. **`00_meta/` broken 5건 정합성 검증** — lint vs find_cross_link_broken 차이 + 실제 governance 페이지 vault 안 존재 여부
2. **13 missing reverse-link 보강** (Cycle 5k Phase 4 A) — uobject/asseteditorapi/personatoolkit 페이지의 Cross-link § 보강
3. **find_claim_conflict LLM mode mcwiki extension 통합** — anthropic SDK 의존성 + API key 환경변수
4. **`find_cross_link_broken` v0.3.1 patch 정식 적용** (라인 번호 보존 버전)
5. **vault 전체 audit 자동화 (전체 222 페이지)** — Phase 4 의 8 페이지 → 222 페이지 확장. ue-audit-agent 통합 권장
6. KMCProject 코드 작업 잔여 (사용자 결정 대기)

## 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-15 (Cycle 5k) | Phase 1 검증 + Phase 2 v0.3.1 patch + Phase 3 LLM mode PR + Phase 4 audit batch (8 페이지) — `00_meta/` broken 5건 발견 |
