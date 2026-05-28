# GitHub 셋업 — MCWiki 를 private repo 로 push & 다른 머신에서 sync

> 본 vault 를 GitHub 의 private 저장소로 push 한다. 목적: (1) 변경 이력 보존, (2) 다른 머신/팀원이 clone 으로 동일 vault 사용, (3) MCP server 코드와 콘텐츠를 한 묶음으로 배포.

## 0. 전제

- `git` 설치 + `gh` CLI 설치 (`https://cli.github.com/`) — 둘 다 옵션이지만 `gh` 가 가장 간편
- vault 루트가 git repo 이미 init 되어 있음 (`E:\MCWiki\.git\` 존재)
- 첫 commit 만들기 전이라면 §1, 이미 있다면 §2 부터

## 1. 첫 commit

```powershell
cd E:\MCWiki
git status                              # tracked / untracked 확인
git add CLAUDE.md AGENTS.md README.md .gitignore
git add raw\ wiki\ tools\ docs\ templates\ 00_meta\
git commit -m "init: vault scaffold + UE 5.7.4 ingest (Phase 1~4H)"
```

## 2. GitHub repo 생성 + 1번에 push

**옵션 A — `gh` CLI (권장)**:

```powershell
gh auth login                           # 한 번만
gh repo create MCWiki --private --source=. --remote=origin --push
```

repo 생성 + remote 등록 + push 까지 한 번에. URL 은 `gh repo view --web` 로 확인.

**옵션 B — 수동**:

1. <https://github.com/new> 에서 `MCWiki` private repo 생성. README/.gitignore/license 모두 *체크 해제* (이미 있으니 conflict 방지).
2. PowerShell:

   ```powershell
   git remote add origin git@github.com:<USER>/MCWiki.git
   git branch -M main
   git push -u origin main
   ```

> SSH 키 미설정이면 `https://github.com/<USER>/MCWiki.git` URL 로도 됨 (push 시 PAT 입력).

## 3. raw/ue-wiki-llm/ 분리 — submodule 권장

raw/ue-wiki-llm/ 은 *원본 (C:\Unreal\UnrealEngine\LLM_Wiki) 의 sync 스냅샷* 이라 본 vault 와 갱신 주기가 다르다. 별도 repo + submodule 로 분리하면:

- vault commit 가벼움
- raw 갱신은 submodule pointer 만 bump
- 권한을 분리 가능 (raw 는 더 폐쇄적)

```powershell
# A) raw 를 별도 repo 로
cd C:\Unreal\UnrealEngine\LLM_Wiki
git init && git add . && git commit -m "snapshot: UE 5.7.4 LLM Wiki (skills/refs/catalog/docs/meta)"
gh repo create UE-LLM-Wiki-Raw --private --source=. --remote=origin --push

# B) MCWiki 에 submodule 로 끼움
cd E:\MCWiki
git rm -r --cached raw\ue-wiki-llm
Remove-Item -Recurse -Force raw\ue-wiki-llm
git submodule add git@github.com:<USER>/UE-LLM-Wiki-Raw.git raw/ue-wiki-llm
git commit -m "raw/ue-wiki-llm -> submodule"
git push
```

다른 머신에서 clone 시:

```powershell
git clone --recurse-submodules git@github.com:<USER>/MCWiki.git E:\MCWiki
```

> 분리 안 하고 한 repo 에 다 넣어도 동작은 한다 — 본 vault 가 ~3 MB / 508 파일이라 크기 문제 거의 없음. 분리는 *권한 구분* 이 주된 이유.

## 4. 일상 워크플로

```powershell
cd E:\MCWiki
# ingest 후
git add wiki\sources\ wiki\index.md wiki\log.md
git commit -m "ingest: <category> sub-skills (Phase X)"
git push

# raw 갱신했다면 submodule 도
cd raw\ue-wiki-llm
git add . && git commit -m "raw: re-sync from C:\Unreal\UnrealEngine\LLM_Wiki" && git push
cd ..\..
git add raw\ue-wiki-llm                 # submodule pointer bump
git commit -m "raw: bump pointer" && git push
```

## 5. (선택) GitHub Actions — lint CI

`.github/workflows/lint.yml`:

```yaml
name: lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python tools/lint.py
```

push 마다 0 issues 보장. lint.py 가 자체적으로 exit code 비-0 을 내도록 추후 확장 가능.

## 6. (선택) Remote MCP — Cloudflare Workers

local STDIO 가 아니라 *remote SSE/HTTP* MCP 서버를 GitHub Actions 로 자동 deploy:

1. `tools/mcp_server.py` 의 `stdio_server` 를 `mcp.server.sse` 로 분기 (또는 두 entry-point 분리)
2. `wrangler.toml` 작성 + `npm i -g wrangler` + `wrangler login`
3. `.github/workflows/deploy.yml` 에 `wrangler deploy` 추가
4. push → Cloudflare 가 24/7 라이브 endpoint 호스팅
5. 클라이언트 mcp.json 은 `command`/`args` 대신 `url: "https://mcwiki.<USER>.workers.dev"` 형태

vault 콘텐츠는 R2 / KV 에 mirror 필요 (worker 는 디스크가 없음). 본 단계는 *팀/모바일/외부 공유* 가 필요해질 때만.

## 7. 보안 / 시크릿

- repo 는 **private** 로. 본 vault 에 사용자 학습 메모 / API key / personal note 들어갈 수 있음
- `.gitignore` 에 `.env`, `*.key`, `*.pem` 추가 (이미 있으면 OK)
- raw/ 의 PDF/논문 — 저작권 있으면 submodule 도 private 로
- GitHub Actions secrets 는 Settings → Secrets and variables → Actions

## 8. 트러블슈팅

| 증상 | 해결 |
| -- | -- |
| `git push` 가 reject — large file | `git lfs install && git lfs track "*.pdf"` 후 재시도 |
| submodule 이 비어보임 | `git submodule update --init --recursive` |
| Windows line-endings warning | `git config --global core.autocrlf true` (한 번만) |
| Obsidian 의 `.obsidian/workspace.json` 이 매번 commit 됨 | `.gitignore` 에 `.obsidian/workspace*` 이미 있음 — 이미 tracked 면 `git rm --cached .obsidian/workspace.json` |
| clone 후 lint.py 가 fail | Python 3.10+ 확인. 의존성 없는 stdlib 만 쓰므로 보통은 venv 필요 X (MCP server 만 venv 필요) |
