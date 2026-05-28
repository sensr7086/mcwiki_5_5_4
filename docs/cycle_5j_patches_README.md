# Cycle 5j Patch Bundle — mcwiki MCP server 도구 #2/#3/#4

> **목적**: Cycle 5h #3 PR 요청서 §6.6 의 후속 PR 시리즈 — Cycle 5i `find_cross_link_broken` (mcwiki v0.3.0) 적용 성공에 이어, 단계 3 자동화 도구 4종 중 남은 3종 PR 코드 작성.

## Cycle 5i 성과 회고

- **mcwiki v0.3.0 적용 완료** — `find_cross_link_broken` 도구 active vault 에 등록 (사용자 patch 적용 검증).
- Phase 1 검증: 6 핵심 페이지 208 wikilinks 검증 → **broken 1 (0.48%) — false positive 만**.
  - `ue-meta-baseline-grep-system` §5.1 의 `[[wikilink]]` literal 표기 — 도구가 코드 블록 안 wikilink 도 추출 (한계).

## Cycle 5j 도구 #2/#3/#4 (본 bundle)

| 파일 | 도구 | LOC | 우선도 | 의존 |
| -- | -- | -- | -- | -- |
| `suggest_missing_cross_link.py` | #2 | ~200 | ⭐⭐ | 도구 #1 wikilink 추출 로직 재사용 + **코드 블록 무시 fix** |
| `find_claim_conflict.py` | #3 | ~250 | ⭐⭐ | 휴리스틱 mode (LLM mode 별도 PR) |
| `find_stale_baseline.py` | #4 | ~200 | ⭐ | frontmatter parser + 의존 페이지 그래프 |

## 도구 #2 — `suggest_missing_cross_link`

**목적**: 전역 backlink 분석으로 누락 cross-link 추천.

**핵심 발전 (Cycle 5i false positive 회피)**:
- `strip_code_blocks()` — 코드 블록 + inline code 안 wikilink 무시 (도구 #1 의 false positive 패치)
- 도구 #1 의 wikilink 추출 / kind 추론 로직 재사용

**시그니처**:
```python
suggest_missing_cross_link(slug, kind=None, vault_root=None, min_inbound=1)
```

**반환**:
```json
{
    "slug": "...",
    "outbound_count": int,
    "inbound_count": int,
    "suggestions": [
        {
            "source_slug": "...",
            "source_kind": "...",
            "inbound_count": int,
            "confidence": "high|med|low",
            "is_reverse_linked": bool,
            "missing": bool
        }
    ]
}
```

**confidence 로직**:
- high: 카테고리 일치 + inbound 3+
- med: 카테고리 일치 또는 inbound 3+
- low: 그 외

## 도구 #3 — `find_claim_conflict`

**목적**: 두 페이지의 같은 키워드 claim 비교 (휴리스틱 mode).

**4 패턴 추출**:
1. **섹션 헤더** — `## §1 매트릭스` 등
2. **수치 claim** — `9 PURE_VIRTUAL` / `함정 13대` / `6 호스트` 등 (정규식 `\d+ (PURE_VIRTUAL|virtual|함정|...)`)
3. **tier 분포** — `🟢 4 / 🟡 1 / 🔴 0` (정규식 `🟢 \d+ / 🟡 \d+ / 🔴 \d+`)
4. **API 시그니처** — `FAssetEditorToolkit::GetEditingObjects` 등

**3 충돌 카테고리**:
- `numeric_mismatch` — 동일 키워드의 수치 불일치 (severity high/med)
- `tier_distribution_mismatch` — 분포 불일치
- `api_signature_conflict` — 공통 API 패턴 미발견 (확장 후속)

**LLM mode (후속 PR 5j #3.2)** — Claude Haiku 3.5 API 호출로 더 정교한 claim 비교. mcwiki extension 의 LLM provider 통합 필요.

## 도구 #4 — `find_stale_baseline`

**목적**: 페이지 `last_updated` 기준 + 의존 페이지 변경 추적 — staleness 검출.

**활용 케이스**:
- 분기별 audit (`18_ModelEvolutionAudit` 절차)
- ue-audit-agent 자동 호출 → ✅ 갱신 후보 분류

**시그니처**:
```python
find_stale_baseline(slug, kind=None, threshold_days=90, vault_root=None)
```

**반환**:
```json
{
    "slug": "...",
    "last_updated": "YYYY-MM-DD",
    "age_days": int,
    "is_stale": bool,
    "dependent_changes": [
        {
            "dep_kind": "...", "dep_slug": "...",
            "dep_last_updated": "YYYY-MM-DD",
            "change_after_baseline": true
        }
    ],
    "change_after_count": int
}
```

**Frontmatter 우선순위**: `last_updated` > `ingested` > `source_date`.

## 적용 절차

### 1. mcwiki extension server 모듈에 복사

```
%USERPROFILE%\AppData\Roaming\Claude\Claude Extensions\local.mcpb.x...\mcwiki\
└── server.py (또는 main entrypoint)
    └── (Cycle 5j 적용) 다음 import 추가:
        from .suggest_missing_cross_link import suggest_missing_cross_link_handler
        from .find_claim_conflict import find_claim_conflict_handler
        from .find_stale_baseline import find_stale_baseline_handler
```

### 2. server entrypoint 에 3 도구 등록

```python
@server.tool("suggest_missing_cross_link")
async def handle_suggest_missing_cross_link(slug: str, kind: str = None, min_inbound: int = 1):
    return suggest_missing_cross_link_handler(slug, kind, vault_root=VAULT_ROOT, min_inbound=min_inbound)

@server.tool("find_claim_conflict")
async def handle_find_claim_conflict(slug_a: str, slug_b: str, kind_a: str = None, kind_b: str = None):
    return find_claim_conflict_handler(slug_a, slug_b, kind_a, kind_b, vault_root=VAULT_ROOT)

@server.tool("find_stale_baseline")
async def handle_find_stale_baseline(slug: str, kind: str = None, threshold_days: int = 90):
    return find_stale_baseline_handler(slug, kind, threshold_days, vault_root=VAULT_ROOT)
```

### 3. mcwiki v0.4.0 배포 + Claude Desktop 재시작

```
ToolSearch 로 확인:
  mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__suggest_missing_cross_link
  mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__find_claim_conflict
  mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__find_stale_baseline
```

### 4. 검증 호출

```
suggest_missing_cross_link(slug="ue-coreuobject-uobject") → outbound/inbound + 추천
find_claim_conflict(slug_a="ue-editor-asseteditorapi", slug_b="ue-editor-personatoolkit") → 충돌 0 기대
find_stale_baseline(slug="ue-coreuobject-uobject", threshold_days=30) → age_days + dependent_changes
```

## false positive 회피 — 도구 #1 (find_cross_link_broken) 의 개선 후보

본 Cycle 5j 의 `strip_code_blocks()` 헬퍼를 **도구 #1 에도 적용** 권장 — Phase 1 검증의 false positive (`[[wikilink]]` literal) 회피.

→ mcwiki v0.3.1 patch:
```python
# find_cross_link_broken.py 의 본문 wikilink 추출 직전 추가
content = strip_code_blocks(content)
```

## 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-15 (Cycle 5j) | 도구 #2/#3/#4 PR 코드 + README + 적용 절차 + 도구 #1 false positive 회피 patch 제안 |
