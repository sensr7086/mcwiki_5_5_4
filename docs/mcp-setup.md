# MCP Server 설치 — MCWiki 를 다른 프로젝트에서 참조

> 본 vault 를 MCP server 로 띄워서, 다른 Claude Code 프로젝트 / Claude Desktop / 다른 머신의 LLM 이 vault 의 sources/entities/concepts 를 *resource* 로 읽고, search/lint/ingest 를 *tool* 로 호출할 수 있게 한다.

## 0. 무엇이 노출되는가

`tools/mcp_server.py` 가 MCP STDIO server 로 띄워지면 클라이언트는 다음을 얻는다.

**Resources** (read-only — `wiki://` URI 로 접근):

- `wiki://index` / `wiki://log` — 인덱스 + append-only 로그
- `wiki://sources/<slug>` / `wiki://entities/<slug>` / `wiki://concepts/<slug>` / `wiki://synthesis/<slug>` — wiki 페이지
- `wiki://meta/<slug>` — 00_meta 의 거버넌스 페이지
- `wiki://raw/<rel-path>` — raw/ 의 원본 (read-only mirror, `..` 차단)

**Tools** (LLM 이 호출):

- `list_pages(kind)` — 한 카테고리의 slug 목록
- `search(query, scope?, limit?)` — wiki/ (또는 wiki+raw) 전반 substring 검색
- `lint()` — `tools/lint.py` 실행 결과 반환
- `stats()` — `tools/stats.py` 실행 결과 반환
- `ingest_seed(slug, source_path, title?)` — `templates/source.md` 로 새 source 페이지 scaffold

## 1. 의존성 설치 (한 번만)

```powershell
cd E:\MCWiki
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r tools\requirements.txt
```

> venv 권장 — 시스템 Python 의 site-packages 와 격리. mcp 패키지는 1MB 정도.

## 2. 동작 sanity check

```powershell
.venv\Scripts\python.exe tools\mcp_server.py
```

즉시 종료되지 않고 STDIN 을 기다리면 정상. 프로세스가 즉시 종료되거나 import 에러를 내면 .venv 활성화 또는 `pip install mcp` 재확인. 종료는 `Ctrl+C`.

## 3. Claude Code 등록

`~/.claude.json` (Windows: `%USERPROFILE%\.claude.json`) 의 `mcpServers` 섹션에 추가. `tools/mcp.example.json` 에 3가지 변형 (native python / venv / WSL) 을 둠.

권장 — venv 변형:

```jsonc
{
  "mcpServers": {
    "mcwiki": {
      "command": "E:\\MCWiki\\.venv\\Scripts\\python.exe",
      "args": ["E:\\MCWiki\\tools\\mcp_server.py"],
      "env": { "MCWIKI_ROOT": "E:\\MCWiki" }
    }
  }
}
```

Claude Code 재시작 → `/mcp` 또는 mcp tool list 에서 `mcwiki` 가 보이면 성공.

## 4. Claude Desktop 등록

`%APPDATA%\Claude\claude_desktop_config.json` 의 `mcpServers` 에 동일한 entry. 앱 재시작.

## 5. 다른 머신에서 사용

저장소를 GitHub 에서 clone (→ `docs/github-setup.md`):

```powershell
git clone --recurse-submodules git@github.com:<USER>/MCWiki.git E:\MCWiki
cd E:\MCWiki
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r tools\requirements.txt
```

`mcp.json` 은 머신마다 별도 (절대 경로). `tools/mcp.example.json` 을 base 로 복사.

## 6. 환경 변수

| 변수 | 기본 | 용도 |
| -- | -- | -- |
| `MCWIKI_ROOT` | `tools/` 의 부모 | vault 루트 (다른 위치에서 실행할 때) |

## 7. 트러블슈팅

| 증상 | 원인 / 해결 |
| -- | -- |
| `ImportError: mcp` | venv 활성화 안 함 또는 install 실패 → `pip install 'mcp>=1.0.0'` |
| 클라이언트 list 에 안 보임 | mcp.json 의 절대 경로 / 슬래시 escaping 확인. Windows 는 `\\` 이중 backslash |
| `lint()` 호출 시 stderr | `tools/lint.py` 가 0 issues 가 아닐 때 정상. 출력에 `[stderr]` prefix 표시 |
| `wiki://raw/...` 가 빈 응답 | raw/ 안의 path 가 실제로 없음. 또는 `..` traversal 차단 |
| 다른 머신에서 path 다름 | mcp.json entry 의 `command`/`args`/`MCWIKI_ROOT` 모두 그 머신 기준 절대 경로로 |

## 8. 보안 — 이 server 는 read 가 거의 전부

작성된 도구 중 *디스크 변경* 은 `ingest_seed` 한 가지 (templates/ 에서 새 source page scaffold). 그 외는 모두 read-only — search / lint / stats / list. raw/ 접근은 `..` traversal 차단으로 vault 바깥 탈출 불가.

추가로 변경 도구 (예: `update_source`, `append_log`) 가 필요하면 `tools/mcp_server.py` 의 `list_tools()` + `call_tool()` 에 핸들러 추가.

## 9. Cowork 에 연결 — Desktop Extension (.mcpb) 경로

Cowork (Claude Desktop) 는 일반 mcp.json 이 아니라 **Desktop Extension (.mcpb)** 패키지로 로컬 MCP 서버를 등록한다. 본 vault 루트의 `manifest.json` 이 그 메타데이터.

### 9.1. mcpb CLI 설치 (한 번만)

```powershell
npm install -g @anthropic-ai/mcpb
mcpb --version    # 0.x.x 출력 확인
```

(Node.js 18+ 필요. [https://nodejs.org/](https://nodejs.org/) 에서 LTS 설치)

### 9.2. .mcpb 패키지 빌드

```powershell
cd E:\MCWiki
mcpb pack . mcwiki-0.1.0.mcpb
```

vault 루트의 `manifest.json` 을 읽어 `tools/mcp_server.py` + 의존성 메타를 묶은 단일 `mcwiki-0.1.0.mcpb` 가 만들어진다 (~수십 KB).

### 9.3. Cowork 에 install

1. Claude Desktop 실행 → **Settings → Extensions**
2. **Advanced settings** 클릭 → **Extension Developer** 섹션 펼침
3. **"Install Extension..."** → `E:\MCWiki\mcwiki-0.1.0.mcpb` 선택
4. 설치 다이얼로그에서 `vault_root` 항목에 `E:\MCWiki` 입력 (manifest 의 user_config 가 자동 표시)
5. 설치 완료 후 새 채팅 시작 → 채팅 입력창의 **"+"** 버튼 → **Connectors** → `mcwiki` 가 보이면 성공

### 9.4. 동작 확인

새 Cowork 채팅에서:

```
@mcwiki list_pages kind=sources 의 결과를 보여줘
```

또는:

```
wiki://index 리소스를 읽어서 통계 부분만 인용해줘
```

### 9.5. Cowork vs Claude Code 차이

| 항목 | Claude Code (`~/.claude.json`) | Cowork (Desktop Extension) |
| -- | -- | -- |
| 설정 형태 | JSON 직접 편집 | `.mcpb` 패키지 + GUI |
| 의존성 | venv + pip install 수동 | manifest 의 runtime 선언 (자동 처리) |
| 업데이트 | 코드 변경 → 재시작 | 새 .mcpb 빌드 → 재설치 |
| 추천 | 개발/테스트 단계 | 일상 사용 (안정 버전) |

### 9.6. 트러블슈팅 (Cowork)

| 증상 | 해결 |
| -- | -- |
| .mcpb 설치 시 "manifest invalid" | `manifest.json` 의 `manifest_version` / `server.entry_point` 확인. JSON 문법 valid 여부 |
| 설치 후 Connectors 에 안 보임 | Claude Desktop 완전 재시작 (System tray 종료 → 재실행) |
| `vault_root` 가 매번 default 로 돌아감 | Settings → Extensions → mcwiki → 설정에 절대 경로 다시 입력 후 저장 |
| 도구 호출 시 `python: command not found` | manifest 의 `mcp_config.command` 가 `python` → 시스템 PATH 에 python 없는 경우. `py` 또는 절대 경로로 변경 후 재패킹 |

## 10. (대안) Custom Connector — Remote (HTTP/SSE) 모드

stdio_server 대신 `mcp.server.sse` 를 쓰면 Cloudflare Workers / fly.io 등에 deploy 가능. 이 경우 Cowork 의 **Settings → Connectors → Add custom connector** 에서 HTTPS URL 입력 (Anthropic 클라우드가 endpoint 에 접속하므로 *공개 인터넷에서 reachable* 해야 함 — localhost 안 됨).

`docs/github-setup.md` §6 참고. 다중 사용자 / 인증이 필요해지면 그쪽으로 확장.

## 11. Pattern X — GitHub-backed Local Server (다중 머신 sync)

vault 가 git repo 이고 GitHub remote 가 등록되어 있으면, mcp_server 가 **시작 시 자동 `git pull --ff-only`** 를 실행한다. 다른 머신에서 동일 server 를 띄울 때 항상 최신 main 콘텐츠를 본다.

### 11.1. 동작

- `_git_pull_if_repo()` 가 `_main()` 의 첫 줄에서 호출
- 조건: `ROOT/.git` 이 존재 + `MCWIKI_AUTOPULL` env 가 `"0"` 이 아님
- 실패 시 (오프라인 / merge conflict 등) 조용히 로컬 콘텐츠로 진행 — server 가 죽지 않음
- timeout 10초 — 네트워크 지연으로 server 가 안 뜨는 일 방지

### 11.2. opt-out

```jsonc
// mcp.example.json
"env": {
  "MCWIKI_ROOT": "E:\\MCWiki",
  "MCWIKI_AUTOPULL": "0"        // ← 추가하면 자동 pull 끔
}
```

또는 manifest.json 의 `mcp_config.env` 에 동일 키 추가.

### 11.3. 명시적 도구 — `git_status` / `git_pull`

LLM 이 직접 호출 가능한 두 도구가 추가됨:

- **`git_status`** — branch / ahead-behind / dirty 파일 수 출력
- **`git_pull`** — 명시적 fast-forward pull (autopull 결과 확인 후 수동 갱신할 때)

Cowork 채팅에서:

```
mcwiki 의 git_status 를 호출해서 다른 머신과 sync 됐는지 확인해줘
```

### 11.4. 다중 머신 워크플로

머신 A (주 갱신 머신):

```powershell
cd E:\MCWiki
# ... ingest 작업 ...
python tools\lint.py             # 0 issues 확인
git add wiki\sources\ wiki\index.md wiki\log.md
git commit -m "ingest: ..."
git push
```

머신 B/C (사용 머신):

```powershell
# 한 번만 — clone
git clone git@github.com:<USER>/MCWiki.git E:\MCWiki
python -m pip install mcp        # 또는 venv
# .mcpb 빌드 + Cowork install — docs/mcp-setup.md §9
```

이후 머신 B/C 의 Cowork 가 mcwiki 도구를 호출할 때마다 server 가 startup pull → 항상 머신 A 의 최신 commit 을 봄.

### 11.5. 충돌 — fast-forward 가 안 될 때

머신 B 가 *로컬에서* 도 commit 했다면 fast-forward 실패 → autopull 이 조용히 skip. 해결:

```powershell
cd E:\MCWiki
git status                       # 로컬 commit 확인
git pull --rebase                # 또는 git push 먼저
```

원칙: **머신 B/C 는 read-only**. ingest/edit 는 머신 A 한 곳에서만. 분산 commit 이 필요하면 패턴 Y (Remote MCP) 로 업그레이드하는 게 깔끔.

### 11.6. 보안

- repo 가 private → `git pull` 에 SSH 키 또는 HTTPS PAT 가 머신마다 등록되어 있어야 함 (`gh auth setup-git` 한 번)
- `MCWIKI_AUTOPULL=0` 으로 startup pull 끄고 사용자 명시 호출 (`git_pull` tool) 만 받게 하는 것도 옵션
- 업데이트 직후 lint 가 깨지면 — server 는 살아있고 기존 콘텐츠로 동작. 다음 startup 또는 `git_pull` 호출에서 다시 시도
