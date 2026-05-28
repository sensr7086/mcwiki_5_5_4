# MCWiki MCP — 다른 에이전트에서의 사용법

> 본 vault 가 Cowork / Claude Code / Claude Desktop 어디든 mcwiki 로 install 되어있다는 전제. 설치 절차는 [`docs/mcp-setup.md`](mcp-setup.md). 본 가이드는 *install 후 어떻게 쓰는가* 만 다룬다.
>
> 대상 — KMCProject 같은 *다른 프로젝트* 의 Cowork 채팅, [Components] 같은 *specialist subagent*, 새 머신의 Claude Code 세션.

---

## 0. 한 줄 요약

```
mcwiki 의 read_page kind=concepts slug=Component-Policies-6 호출해서 6대 정책 정리
```

자연어 한 줄 — 이게 핵심 사용 패턴. agent 가 도구를 알아서 골라서 호출하지만, **도구 이름 + 인자** 를 명시하면 헛걸음이 없다.

---

## 1. 11개 도구 레퍼런스

### 1.1. 읽기 (Read — 가장 자주 씀)

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`read_index`** | 없음 | `wiki/index.md` 전문 — 168 sources / 79 entities / 40 concepts 카탈로그 | 어디서부터 시작할지 모를 때. 첫 진입점 |
| **`read_page`** | `kind` (sources/entities/concepts/synthesis/meta) + `slug` | 해당 페이지 markdown 전문 (frontmatter 포함) | 특정 페이지 본문이 필요할 때 |
| **`read_raw`** | `rel_path` (raw/ 기준 상대 경로) | raw 파일 본문. `..` traversal 차단 | wiki 가 아닌 *원본* (UE skills/references/catalog) 을 직접 인용할 때 |
| **`read_log`** | 없음 | `wiki/log.md` 전문 — 모든 작업 이력 | "언제 무슨 변경이 있었나" 추적 |

### 1.2. 탐색 (Discover)

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`list_pages`** | `kind` | 해당 카테고리의 slug 목록 (한 줄 1개) | 어떤 페이지가 있는지 카탈로그를 빠르게 훑을 때 |
| **`search`** | `query` + `scope` ("wiki" or "all") + `limit` (default 50) | grep 스타일 매치 (파일경로:라인번호:내용) | 키워드로 모든 페이지를 가로지를 때 |

### 1.3. 검증 / 통계

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`stats`** | 없음 | sources/entities/concepts 분포 + freshness + Top 10 hubs (inbound link count) | vault 의 전반적 건강 / 가장 중요한 페이지 파악 |
| **`lint`** | 없음 | `Lint: N pages, K issues.` + 이슈 목록 | 본문에 깨진 wikilink / 누락된 frontmatter 있는지 |

### 1.4. 쓰기 / Git

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`ingest_seed`** | `slug` + `source_path` (raw/...) + `title?` | 새 wiki/sources/<slug>.md scaffold 생성 (templates/source.md 기반) | 새 raw 자료를 wiki source 로 등록할 때 첫 단계 |
| **`write_page`** | `kind` (sources/entities/concepts/synthesis) + `slug` + `content` (frontmatter 포함 markdown) + `overwrite?` | 생성/갱신 결과 | agent 가 작성한 페이지를 vault 에 저장 (synthesis 작성의 핵심) |
| **`append_log`** | `op` + `title` + `body` | append 결과 | 작업 이력을 표준 헤더로 log.md 에 기록 |
| **`git_status`** | 없음 | branch / ahead-behind vs upstream / dirty 파일 수 | 다른 머신과의 sync 상태 확인 |
| **`git_pull`** | 없음 | `git pull --ff-only` 실행 결과 | startup autopull 외에 명시적으로 최신 갱신 받기 |

### 1.5. Synthesis 자동 파이프라인

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`synthesis_seed`** | `topic` + `slug?` + `extra_keywords?` | scaffold (frontmatter + 5섹션 outline + 자동 cross-link) — 디스크 변경 X | synthesis 작성 시작점. 토픽 키워드로 vault 자동 검색 |
| **`synthesis_finalize`** | `slug` + `status?` (draft/living/settled) + `summary?` | lint 검증 + index.md count 갱신 + log entry append | write_page 로 본문 저장 후 마무리 |

### 1.6. Query Filing-back (CLAUDE.md §5.2 의 4~5단계 압축)

| 도구 | 인자 | 반환 | 언제 쓰나 |
| -- | -- | -- | -- |
| **`query_recap`** | `question` + `answer_summary?` + `mode` + 모드별 추가 인자 | mode 별 처리 결과 | 사용자 질문에 답한 직후 — *어떤 형태로 vault 에 보관할지* 결정점 |

**4 modes**:

- **`skip`** — 가치가 낮거나 일회성. 아무것도 안 함
- **`append_to_log`** — 가장 흔함. wiki/log.md 에 `## [date] query | <q>` + Q/A 본문 append
- **`append_to_page`** — 기존 페이지에 Q&A 보강 (`target_kind` + `target_slug` 필수). 해당 페이지 끝에 `## Q&A — <q> (date)` 섹션 + log 도 동시 기록
- **`propose_synthesis`** — 새 synthesis 가 정당화될 때. log 에 query 기록 + agent 에게 "다음 4단계는 synthesis_seed → read_page 들 → write_page → synthesis_finalize" 안내 반환

### 1.6.0. 🚨 Citation Discipline — vault 인용 vs 추론 (의무)

CLAUDE.md §13 / [[00_meta/06_VaultCitationRule]] 의무. agent 가 답변할 때 *모든 사실 주장* 을 3 tier 로 시각 분리해야 한다:

```markdown
**🟢 vault 인용**:
- [[wikilink]] 형식으로 명시.

**🟡 PARTIAL — vault 근거 + 외삽**:
- (vault 근거: [[...]] · 시그니처 등 일부는 외삽)

**🔴 INFERRED — vault 미확정 (일반 지식 / 코드 추론)**:
1. <항목> — vault 미확인
2. <항목> — 내 일반 UE 지식
```

`search` 0 hits 또는 read_page 에 답 없음 → **반드시 🔴 섹션 분리**. 자세한 예시는 `00_meta/06_VaultCitationRule.md` 참고.

위반 시 [[sources/ue-agent-evaluator]] 평가에서 감점. 🔴 가 가치 있으면 `query_recap mode=propose_synthesis` 로 vault 화 사이클 시작.

### 1.6.1. 자동 query workflow 흐름

```text
사용자: "다수 NPC 환경에서 anim 비용 어떻게 줄여?"

agent (자동):
  [1] read_index() → 카탈로그 훑기
  [2] search query="URO Significance Animation 다수 NPC" → 매치 좁히기
  [3] read_page (반복) → 관련 4-6개 페이지 본문 수집
  [4] (LLM 추론) 답변 작성 + [[wikilink]] 인용 → 사용자에게 응답
  [5] query_recap mode=append_to_log question="..." answer_summary="..."
      → wiki/log.md 에 query entry 자동 기록

또는 가치가 더 큰 경우:
  [5'] query_recap mode=propose_synthesis topic="다수 NPC 5중 최적화"
       → log entry + 다음 4단계 자동 시작 (synthesis_seed → ...)
```

이로써 **질문 한 번에 vault 가 갱신** 되는 살아있는 지식 베이스 동작 완성.

### 1.5.1. 자동 synthesis 4단계 흐름

```text
"synthesize 다수 NPC 5중 최적화" 한 자연어 명령 →

[1] synthesis_seed topic="다수 NPC 5중 최적화"
    → scaffold + 자동 발견된 sources/entities/concepts 목록 반환

[2] read_page 들 (각 관련 소스의 본문 모음)

[3] write_page kind=synthesis slug=multi-npc-5x content=<composed body>
    → wiki/synthesis/multi-npc-5x.md 저장

[4] synthesis_finalize slug=multi-npc-5x status=living summary="..."
    → lint 검증 + index.md `## Synthesis (1)` + log entry
```

agent 가 4 단계를 *한 자연어 명령* 으로 multi-step 처리. 사용자는 "synthesize <토픽>" 만.

---

## 2. 자주 쓰는 워크플로 6가지

### 2.1. "이 vault 에 뭐가 들어있지?" — 처음 진입

```
mcwiki 의 read_index 호출해줘
```

→ 19 카테고리 (CoreUObject / Components / ... / Render) 의 main + sub-skill 목록 + entities 79 + concepts 40 + 통계가 한 페이지로 들어옴.

### 2.2. "특정 주제 찾기" — search → read_page

```
mcwiki 의 search 로 "AnimNotify" 검색하고, 가장 관련 깊은 페이지 두세 개를 read_page 로 본문 가져와서 정리해줘
```

→ agent 가 search → 매치된 페이지 식별 → read_page 들 호출 → 종합. 한 번의 자연어로 multi-step 처리.

### 2.3. "이 클래스 / 정책 알려줘" — read_page 직접

```
mcwiki 의 read_page kind=entities slug=AActor 호출해서 라이프사이클 11단계 정리
mcwiki 의 read_page kind=concepts slug=Asset-Loading-Policy 호출해서 5대 정책 인용
```

→ slug 을 알면 가장 빠른 경로. 모를 땐 `list_pages kind=entities` 로 먼저 목록 보고 고름.

### 2.4. "원본 raw 인용 필요" — read_raw

```
mcwiki 의 read_raw rel_path="ue-wiki-llm/references/10_ComponentPolicies.md" 호출해서 6대 정책 *원본 정밀판* 인용
```

→ wiki 의 요약본이 아닌 *raw 의 정밀판* (Tier/예시 코드 포함) 이 필요할 때.

### 2.5. "vault 건강 체크" — lint + stats

```
mcwiki 의 lint 와 stats 둘 다 호출해서 현재 상태 한 줄 요약해줘
```

→ ingest 작업 후 / 다른 머신에서 sync 후 / 정기 점검.

### 2.6. "다른 머신에서 갱신 받기" — git_pull → 다시 작업

```
mcwiki 의 git_pull 호출해서 최신으로 동기화 후, read_log 로 최근 entries 5개 보여줘
```

→ Pattern X 의 startup autopull 외에 명시적 갱신 + 변경사항 확인.

---

## 3. 자연어 프롬프트 패턴 (다른 프로젝트 채팅에서)

```text
# UE 작업 중 정책 인용
mcwiki 의 wiki 에서 "Tick" 관련된 모든 페이지 검색하고 핵심 5줄로 요약해줘

# 클래스 비교
mcwiki 의 read_page 로 entities/UActorComponent 와 entities/USceneComponent 둘 다 읽어서 차이점 표로 정리

# 카테고리 진입
mcwiki 의 list_pages kind=sources 로 Render 카테고리 페이지들만 골라서 read_page 로 본문 다 가져와

# 정책 위반 검증
지금 작성한 코드 (스니펫 첨부) 가 mcwiki 의 concepts/Component-Policies-6 의 6대 정책에 부합하는지 점검

# 학습용
mcwiki 에서 GAS 관련 페이지 모두 찾아서 학습 순서대로 정렬해줘 (basic → advanced)
```

---

## 4. Cross-project 활용 팁

### 4.1. 같은 Cowork 의 다른 채팅

Desktop Extension 은 **앱 레벨** 설치라 모든 채팅에서 자동 인식. 새 채팅 열면 바로 11개 도구 사용 가능. 별도 등록 / 설정 불필요.

### 4.2. Specialist subagent (ue-wiki-llm:*)

specialist agent (예: `ue-components-specialist`) 가 mcwiki 도구를 쓰려면 frontmatter 의 `tools:` 필드에 명시되어 있어야 한다. 만약 specialist 호출 시 "도구 없음" 응답이 오면:

1. specialist .md 파일 (`%USERPROFILE%\AppData\Roaming\Claude\local-agent-mode-sessions\.../skills/...`) 의 frontmatter 확인
2. `tools:` 에 `mcp__MCWiki___UE_5_7_4_Knowledge_Vault__*` 와일드카드 또는 개별 도구 추가
3. Claude Desktop 재시작

또는 — orchestrator 채팅에서 직접 mcwiki 호출해서 결과를 specialist 에게 전달 (간단).

### 4.3. 다른 머신 (Pattern X)

```powershell
git clone https://github.com/<USER>/MCWiki.git E:\MCWiki   # 또는 다른 경로
cd E:\MCWiki
python -m pip install mcp
mcpb pack . mcwiki-0.1.5.mcpb
# Cowork: Settings → Extensions → Install Extension → 새 .mcpb (vault_root = 그 머신 기준)
```

이후 그 머신의 Cowork 도 동일한 11개 도구 사용 가능. mcp_server 시작 시 자동 git pull → 머신 A 의 ingest 가 자동 sync.

### 4.4. 모바일 / claude.ai 웹

로컬 STDIO MCP 는 본 머신 안에서만 동작. 외부 클라이언트가 접근하려면 **패턴 Y (Cloudflare Workers Remote MCP)** — `docs/mcp-setup.md` §10 / `docs/github-setup.md` §6 참고. 본 가이드 범위 밖.

---

## 5. 도구 선택 의사결정 표

| 시나리오 | 첫 도구 | 후속 |
| -- | -- | -- |
| 무엇이 있는지 모름 | `read_index` | `list_pages` → `read_page` |
| 키워드는 있음, 페이지는 모름 | `search query=...` | 매치된 파일 → `read_page` |
| 슬러그/페이지명을 정확히 안다 | `read_page` 바로 | — |
| 원본 raw 가 필요 | `read_raw rel_path=...` | — |
| 클래스 라이프사이클이 궁금 | `read_page kind=entities slug=...` | `read_page kind=concepts slug=...-Lifecycle` |
| 정책/규약이 궁금 | `read_page kind=concepts slug=...-Policy` | `read_raw` 로 정밀판 보강 |
| vault 가 healthy 한가 | `lint` + `stats` | issues 있으면 `read_page` 로 해당 페이지 점검 |
| 다른 머신과 sync? | `git_status` | 차이 있으면 `git_pull` |

---

## 6. 트러블슈팅

| 증상 | 원인 / 해결 |
| -- | -- |
| agent 가 "도구 없음" 응답 | (a) 옛 채팅이 캐시된 도구 목록 사용 — 새 채팅 열기. (b) Cowork 재시작 (system tray Quit) |
| `read_page` 가 "page not found" | slug 오타. `list_pages kind=...` 로 정확한 slug 확인 |
| `read_raw` 가 "rejected" | rel_path 에 `..` 포함되거나 절대경로. raw/ 기준 *상대경로* 만 |
| `search` 결과가 0 | scope=wiki (default) 라 raw/ 미포함. `scope=all` 로 raw 까지 검색 |
| `git_status` 가 "(no upstream)" | GitHub remote 등록 + 첫 push 안 함. `gh repo create MCWiki --private --push` |
| `git_pull` 이 변경사항 안 받음 | (a) remote 없음, (b) fast-forward 불가 (로컬 commit 충돌). PowerShell 에서 `git status` |
| `lint` 가 issues 보고 | 보고된 페이지 → `read_page` 로 본문 점검 → frontmatter / wikilink 수정 |
| 도구 호출 즉시 timeout | mcp server 행함. PowerShell 에서 `python tools\mcp_server.py` 직접 실행해 진단 |
| Specialist subagent 가 도구 못 봄 | §4.2 참고 — frontmatter 의 tools 필드 점검 |

---

## 7. 빠른 시작 — 처음 채팅에서 한 번만

새 프로젝트 / 새 머신에서 처음 mcwiki 를 쓸 때 검증 시퀀스:

```
1. mcwiki 의 stats 호출 → 168 sources / 79 entities / 40 concepts 출력 확인
2. mcwiki 의 lint 호출 → "Lint: 289 pages, 0 issues." 확인
3. mcwiki 의 read_index 호출 → 카탈로그 한 번 훑기
4. mcwiki 의 read_page kind=concepts slug=Component-Policies-6 호출 → 본문 잘 나오는지 확인
```

네 단계 모두 정상이면 vault 가 어디서든 살아있는 상태. 이후 자연어 프롬프트로 자유롭게 인용 / 검색 / 학습 가능.

---

## 8. 참고

- 설치 / 등록 — [`docs/mcp-setup.md`](mcp-setup.md)
- GitHub 연동 — [`docs/github-setup.md`](github-setup.md)
- Obsidian 셋업 — [`docs/obsidian-setup.md`](obsidian-setup.md)
- 작업 이력 — [`wiki/log.md`](../wiki/log.md)
- 카탈로그 — [`wiki/index.md`](../wiki/index.md)
- 이번 세션 셋업 노트 — [`raw/notes/2026-05-10_mcp-github-setup.md`](../raw/notes/2026-05-10_mcp-github-setup.md)
