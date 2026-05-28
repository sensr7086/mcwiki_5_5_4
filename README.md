# LLM Wiki Vault

Karpathy 의 [LLM Wiki 패턴](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 을 Obsidian + Claude Code 환경에서 그대로 운영하기 위한 vault 스캐폴드.

> **핵심 명제** (Karpathy 원문):
> _"the wiki is a persistent, compounding artifact. The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read."_

LLM 이 읽고 합성하고 cross-link 를 유지한다. 사람은 sourcing, 탐구 방향, 좋은 질문을 담당한다.

---

## 0. 무엇이 들어있는가

```
MCWiki/
├── README.md                 ← 본 파일
├── CLAUDE.md                 ← 스키마 마스터 — LLM 이 가장 먼저 읽는 파일
├── AGENTS.md                 ← CLAUDE.md alias (Codex 호환)
├── .gitignore
├── raw/                      ← 사용자만 추가. LLM 은 읽기 전용.
│   ├── README.md
│   ├── articles/  papers/  youtube/  notes/  assets/
├── wiki/                     ← LLM 이 만들고 유지.
│   ├── index.md              ← 콘텐츠 카탈로그
│   ├── log.md                ← 시간순 append-only 로그
│   ├── sources/  entities/  concepts/  synthesis/
├── templates/                ← Templater 호환 (source/entity/concept/synthesis)
├── tools/                    ← stdlib Python 운영 스크립트
│   ├── lint.py               ← 기계적 점검
│   ├── stats.py              ← 분포 / 허브 / 고아 / freshness
│   ├── ingest_seed.py         ← source stub 생성
│   ├── search.py             ← grep + (선택) BM25
│   ├── youtube_to_raw.py     ← YouTube 자막 → raw/youtube
│   ├── mcp_server.py         ← MCP STDIO server (다른 LLM 이 vault 참조)
│   ├── mcp.example.json      ← Claude Code/Desktop/WSL 등록 예시
│   └── requirements.txt      ← mcp>=1.0.0 (MCP server 만 venv 필요)
└── docs/
    ├── obsidian-setup.md     ← Obsidian 설정 절차 (10분)
    ├── mcp-setup.md          ← MCP server 설치 / 등록 / 트러블슈팅
    ├── mcp-usage.md          ← 다른 에이전트에서 사용하는 11개 도구 가이드
    └── github-setup.md       ← GitHub private repo push + submodule
```

---

## 1. 오늘 30분 안에 실행하기 (Quickstart)

### Step 1 — 환경 (5분)

```bash
# 1. Python 3.10+ 확인
python --version

# 2. (선택) YouTube 자막 모듈
pip install youtube-transcript-api

# 3. (선택) BM25 검색
pip install rank-bm25

# 4. git 초기화 (변경 이력 필수)
cd E:\MCWiki
git init && git add . && git commit -m "init: vault scaffold"
```

### Step 2 — Obsidian 연결 (10분)

`docs/obsidian-setup.md` 의 §1~§6 그대로:

1. Obsidian 실행 → "Open folder as vault" → 본 폴더 선택.
2. Settings → Files and links:
   - Default location for new attachments → `raw/assets`
   - New link format → "Relative path to file"
   - Use [[Wikilinks]] → ON
3. Settings → Templates → Template folder location → `templates`
4. Community plugins: Templater, Dataview 설치 ON.
5. 단축키: `Download attachments for current file` → `Ctrl+Shift+D`.
6. 브라우저: <https://obsidian.md/clipper> 설치 → vault = 본 폴더, folder = `raw/articles`.

### Step 3 — AGENTS.md 동기화 (1분)

```bash
# Linux/macOS:
ln -sf CLAUDE.md AGENTS.md

# Windows:
mklink /H AGENTS.md CLAUDE.md
```

### Step 4 — 첫 ingest 시연 (10분)

#### 4-A. 웹 글로

1. 브라우저에서 좋아하는 글 (블로그/뉴스) 한 개 선택.
2. Obsidian Web Clipper → "Add to vault" → `raw/articles/<title>.md` 생성됨.
3. Claude Code (또는 Codex) 를 vault 루트에서 열기.
4. 발화: `"raw/articles/<title>.md 를 ingest 해줘. CLAUDE.md §5.1 의 10단계를 따라."`
5. LLM 이 entity / concept 후보를 보여줌 → 사용자가 OK.
6. LLM 이 `wiki/sources/<slug>.md` + 관련 entity/concept 페이지 생성, `index.md` / `log.md` 갱신.

#### 4-B. YouTube 영상으로

```bash
python tools/youtube_to_raw.py https://www.youtube.com/watch?v=kCc8FmEb1nY
# → raw/youtube/<slug>.md (자막 + 메타) 생성

python tools/ingest_seed.py "Let's build GPT" raw/youtube/<slug>.md youtube
# → wiki/sources/<slug>.md stub 생성, log.md entry 추가
```

LLM 에 발화: `"wiki/sources/<slug>.md 를 ingest 마무리해줘 (entity/concept 발견 + index 갱신)"`.

### Step 5 — 검증 (5분)

```bash
python tools/lint.py
# → 0 issues (또는 작은 issue 들. 보고 처리)

python tools/stats.py
# → 페이지 분포, hub, orphan, freshness

python tools/stats.py --update-index
# → wiki/index.md 의 통계 블록 갱신
```

Obsidian 의 그래프 뷰 (`Ctrl+G`) 를 열어 첫 페이지들이 점으로 보이면 셋업 완료.

---

## 2. 운영 cheat-sheet

### Ingest

```
사용자 ──drop file──▶ raw/<path>/<file>
사용자 ──"ingest <path>"──▶ LLM
                            │
                            ▼
                    LLM 이 §5.1 10단계
                    ├── wiki/sources/<slug>.md (생성)
                    ├── wiki/entities/<...>.md (생성/갱신)
                    ├── wiki/concepts/<...>.md (생성/갱신)
                    ├── wiki/index.md (한 줄 +)
                    └── wiki/log.md (entry +)
```

### Query

```
사용자 ──"질문"──▶ LLM
                  │
                  ▼
            LLM 이 §5.2 5단계
            ├── index.md 읽기
            ├── 후보 페이지 drill-in
            ├── [[citations]] 포함 답변
            └── (선택) wiki/synthesis/ 로 filing-back
```

### Lint (분기별 또는 페이지 ~50 마다)

```bash
python tools/lint.py
# → BROKEN_LINK / ORPHAN / MISSING_FIELD / STALE 등

# 그 후 LLM 발화:
# "lint 결과 보고 contradictions / mentioned-but-missing / underdeveloped 점검."
# LLM 이 wiki/synthesis/lint-YYYY-MM-DD.md 보고서로 작성.
```

---

## 3. 자주 묻는 것

**Q. 기존 노트가 많은데 어떻게 마이그레이션?**

기존 노트를 `raw/notes/` 로 복사 (또는 symlink) → LLM 에 "raw/notes/ 를 한 번에 ingest" 요청 → batch ingest 모드. 모든 노트가 entity/concept 으로 흩뿌려진 *압축본* 이 wiki/ 에 만들어진다. 원본은 raw/ 에 그대로.

**Q. 기존 RAG 파이프라인을 써야 할까?**

vault 가 ~수백 페이지 이하면 `tools/search.py` 와 `index.md` 만으로 충분 (Karpathy gist 의 입장). 그 이상이면:

- `tools/search.py --bm25` 로 BM25 추가 (`pip install rank-bm25`).
- 또는 외부 도구 [qmd](https://github.com/tobi/qmd) 도입 (gist 추천).

**Q. 한국어 본문 + 영어 식별자가 깨지지 않나?**

Obsidian wikilink 는 유니코드 OK. 단 `tools/ingest_seed.py` 의 slugify 가 한글을 보존하므로 일관성 유지.

**Q. raw 의 PDF 는 LLM 이 직접 읽나?**

Claude Code / Codex 는 PDF 읽기를 자체 지원. 단 큰 PDF 는 분할 읽기. raw/papers/ 의 PDF 옆에 같은 이름의 .txt (텍스트 추출본) 를 두면 LLM 이 더 안정적.

**Q. 다른 vault 와 분리?**

본 vault 는 *이 도메인 1개* 에 헌신 (Karpathy gist 의 권장). 다른 도메인 (개인 일기, 회사 wiki 등) 은 별도 vault 를 같은 패턴으로 복제.

**Q. 자매 폴더 `../karpathy-llm-wiki/` 와의 관계?**

`karpathy-llm-wiki/` 는 본 패턴으로 만들어진 *예시 wiki* (Korean, Karpathy 영상 콘텐츠를 다루는). 본 vault 는 그 *시스템 자체*. 둘은 독립.

`karpathy-llm-wiki/` 의 콘텐츠를 본 vault 의 wiki/ 에 통합하려면:

```bash
# 단순 복사 (스키마 일치 가정)
cp -r ../karpathy-llm-wiki/30_Transformer wiki/
# 그리고 LLM 에 "frontmatter 를 본 vault 의 §3 표준에 맞춰 마이그레이션"
```

권장은: 둘을 별개로 두고, 본 vault 에서 새로 ingest 하면서 자연스럽게 entity/concept 페이지가 생기도록.

---

## 4. 다음에 해볼 것

- 한 주 동안 매일 1 source ingest (블로그 글 / 논문 1개 / YouTube 1개).
- 7 source 쌓이면 `python tools/lint.py` + `python tools/stats.py` 로 건강 점검.
- 100 source 즈음에서 `qmd` 도입 또는 `tools/search.py --bm25` 로 검색 강화.
- synthesis 페이지 ≥ 10 개가 되면 Marp 로 슬라이드 export 시도.

---

## 5. 참고

- Karpathy gist (원전): <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Vannevar Bush 1945 "As We May Think" — Memex 의 원전.
- Obsidian docs: <https://help.obsidian.md/>
- 본 vault 의 schema: [`CLAUDE.md`](./CLAUDE.m