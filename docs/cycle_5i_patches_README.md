# Cycle 5i Patch Bundle — README

## 배경

- **Cycle 5h #3+#4** (2026-05-15) — vault 안 `ue-meta-baseline-grep-system` §6 (PR 요청서) + §7 (agent prompt 패치 명세) 완성.
- **Cycle 5i** — 명세를 실제 코드/agent prompt 에 적용.

## 제약

- **read-only mount**: main file tools (Read/Write/Edit) 가 `.remote-plugins/` 및 Claude Extensions 에 접근 가능하나 **write 불가** (`Read-only file system`).
- → main 이 직접 patch 적용 불가 — 본 outputs bundle 을 사용자가 수동 적용.

## 파일

| 파일 | 용도 |
| -- | -- |
| `README.md` | 본 파일 — 적용 가이드 |
| `AGENT_PATCH_GUIDE.md` | 11 agent prompt patch + 적용 절차 + 카테고리 키워드 매트릭스 |
| `find_cross_link_broken.py` | mcwiki MCP server 도구 #1 — Python 구현 (Cycle 5h #3 PR 코드) |

## 적용 절차

### 1. agent prompt patch 적용 (11 agent)

대상 path (Windows):
```
%USERPROFILE%\AppData\Roaming\Claude\local-agent-mode-sessions\11afa6ca-099c-461d-91ad-c4ce8c45ecff\3e9ec507-52ef-4d6f-92ee-3b9186b79803\rpm\plugin_019SPM4GSPfAfagqWFsrexY4\agents\
```

각 agent (.md) 파일의 본문 끝에 `AGENT_PATCH_GUIDE.md` Part 1 의 patch block 추가 + Part 2 의 카테고리 키워드 치환:

- `ue-animation-specialist.md`
- `ue-asset-specialist.md`
- `ue-audit-agent.md`
- `ue-components-specialist.md`
- `ue-editor-specialist.md`
- `ue-gameframework-specialist.md`
- `ue-input-specialist.md`
- `ue-plugin-specialist.md`
- `ue-render-specialist.md`
- `ue-slate-umg-specialist.md`
- `ue-wiki-maintainer.md`

**미적용 2 agent** (사유 명시):
- `ue-orchestrator.md` (라우팅 전용)
- `ue-evaluator.md` (평가 전용 — read 한정 활용)

### 2. mcwiki MCP server `find_cross_link_broken` 도구 추가

#### 2a. extension path 확인 (Windows)

```
%USERPROFILE%\AppData\Roaming\Claude\Claude Extensions\local.mcpb.x087fe52107ab1be95aa0732fe9345569.mcwiki\
```

내부 구조 (예상):
- `server.py` 또는 `server.js` — MCP server entrypoint
- `manifest.json` — extension 메타데이터
- `tools/` 또는 `lib/` — 도구 모듈

#### 2b. 도구 코드 복사

`find_cross_link_broken.py` 를 extension 의 server 모듈 디렉토리 (예: `lib/` 또는 `tools/`) 에 복사.

#### 2c. server entrypoint 에 등록

예 (Python 가정):

```python
# server.py 또는 main entrypoint
from .find_cross_link_broken import find_cross_link_broken_handler

@server.tool("find_cross_link_broken")
async def handle_find_cross_link_broken(slug: str, kind: str = None):
    """find_cross_link_broken — wikilink 존재 검증."""
    return find_cross_link_broken_handler(slug, kind, vault_root=VAULT_ROOT)
```

#### 2d. extension restart

Claude Desktop 재시작 또는 extension reload → mcwiki MCP server 가 `find_cross_link_broken` 도구를 노출.

### 3. 검증

#### 3a. 단계 2 검증 (agent prompt patch)

임의 specialist agent (예: ue-editor-specialist) 호출 → 작성 전 `mcwiki.list_pages` + `mcwiki.read_page` + `mcwiki.search` 자동 호출하는지 확인.

#### 3b. 단계 3 검증 (mcwiki MCP 도구)

```
ToolSearch 로 mcwiki MCP 의 새 도구 확인:
  mcp__MCWiki___UE_5_7_4_Knowledge_Vault__find_cross_link_broken
```

도구 호출 테스트:
```
find_cross_link_broken(slug="ue-editor-asseteditorapi") →
{
  "slug": "ue-editor-asseteditorapi",
  "kind": "sources",
  "total_wikilinks": 30+,
  "broken_count": 0,
  "broken_links": []
}
```

## 한계 / 후속 작업

1. **agent prompt path 정확 확인 필요** — 위 path 가 실제 active path 인지 사용자 직접 검증 (Claude 가 access 못함)
2. **mcwiki extension 구조 미확인** — server 코드 언어 (Python? Node?) + entrypoint 형식 미확인. 본 `find_cross_link_broken.py` 는 Python 가정 — 실제 mcwiki 가 Node.js 라면 TypeScript 로 변환 필요
3. **단계 3 후속 도구** (find_claim_conflict / find_stale_baseline / suggest_missing_cross_link) — Cycle 5j+ 별도 PR

## vault cross-link

- [[sources/ue-meta-baseline-grep-system]] §6 (PR 요청서) + §7 (agent prompt 패치 명세)
- [[sources/ue-editor-asseteditorapi]] §3.1 + §11.4 (테스트 대상)

## 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-15 (Cycle 5i) | 최초 작성 — agent prompt patch bundle + mcwiki MCP server 도구 #1 PR 코드 |
