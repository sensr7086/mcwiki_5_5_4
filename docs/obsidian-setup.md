# Obsidian 셋업 — 본 vault 를 위한 설정

> 본 가이드는 vault 를 처음 여는 시점에 한 번 한다 (~10 분).

## 1. Vault 열기

1. Obsidian 실행 → **"Open folder as vault"** 클릭.
2. 본 폴더 (`E:\MCWiki\`) 선택.
3. "Trust author" 묻는 다이얼로그 → **Trust** (Templater / Dataview 가 자기 코드 실행하므로 필요).

## 2. 핵심 설정 4가지

### 2.1. 첨부 파일 위치 → `raw/assets/`

`Settings → Files and links → Default location for new attachments`

→ **"In the folder specified below"** → `raw/assets`

이미지 붙여넣기 / Web Clipper 의 "Download attachments" 가 모두 여기로 떨어진다.

### 2.2. 새 노트 위치 → 현재 폴더

`Settings → Files and links → Default location for new notes`

→ **"Same folder as current file"**

(LLM 이 wiki/entities/ 안에서 새 페이지 만들 때 자동으로 그 폴더 안에 생성)

### 2.3. 링크 형식 → "Relative path"

`Settings → Files and links → New link format`

→ **"Relative path to file"**

CLAUDE.md §4 의 명시 경로 스타일 (`[[entities/Andrej Karpathy]]`) 과 일치.

### 2.4. wikilink 사용 → ON

`Settings → Files and links → Use [[Wikilinks]]`

→ **ON**.

## 3. 권장 코어 플러그인 ON

`Settings → Core plugins`:

- **Templates** — `templates/` 폴더 지정 (`Settings → Templates → Template folder location` → `templates`)
- **Daily notes** — 매일 노트 (선택, `raw/notes/daily/` 권장)
- **Backlinks** — 모든 페이지에 inbound link 패널 표시
- **Outline** — 좌측 목차
- **Graph view** — 위키 형태 시각화 (Karpathy gist 이 강조)

## 4. 권장 커뮤니티 플러그인

`Settings → Community plugins → Browse`:

| 플러그인 | 용도 | 설정 |
| -- | -- | -- |
| **Templater** | `{{date:YYYY-MM-DD}}` 같은 dynamic placeholder | `Template folder location` = `templates` · `Trigger Templater on new file creation` ON |
| **Dataview** | frontmatter 쿼리 (예: `TABLE FROM "wiki/entities" WHERE kind = "person"`) | 기본값 사용 |
| **Marp** | wiki/synthesis/ 페이지를 슬라이드로 (선택) | 기본값 |
| **Obsidian Git** | 자동 커밋 (선택) | 30분 간격 권장 |

## 5. Obsidian Web Clipper (브라우저 확장)

웹 글을 raw/articles/ 로 한 클릭 클립.

1. <https://obsidian.md/clipper> 에서 확장 설치 (Chrome/Firefox/Safari).
2. 확장 설정 (`톱니바퀴 → Settings`):
   - **Vault**: `MCWiki`
   - **Folder**: `raw/articles`
   - **Note name**: `{{title}}` (또는 `{{date}} {{title}}`)
   - **Properties** (frontmatter): `source: {{url}}`, `clipped: {{date}}`
3. 사용: 웹 페이지에서 확장 클릭 → "Add to vault".

## 6. 권장 단축키

`Settings → Hotkeys`:

| 동작 | 단축키 (권장) |
| -- | -- |
| Download attachments for current file | `Ctrl+Shift+D` |
| Open Templater: Open Insert Template modal | `Ctrl+T` |
| Open graph view | `Ctrl+G` |
| Quick switcher | `Ctrl+O` (기본) |
| Search in all files | `Ctrl+Shift+F` (기본) |

## 7. (선택) 외부 도구

- **qmd** (Karpathy gist 추천) — 로컬 hybrid BM25/vector 검색. <https://github.com/tobi/qmd>
  - 본 vault 의 `tools/search.py` 가 충분치 않아질 때 (페이지 ~수백 이상) 검토.
- **Marp CLI** — wiki/synthesis 를 PPT 로 export.
- **Pandoc** — 다른 포맷 변환.

## 8. 첫 작동 검증

```bash
# vault 루트에서:
python tools/lint.py
# → "Lint: 0 pages, 0 issues." (스캐폴드 직후엔 wiki 페이지가 0)

python tools/stats.py
# → 카테고리별 카운트 + freshness 표시.
```

Obsidian 의 좌측 사이드바에서 `wiki/` 와 `raw/` 가 보이고, `CLAUDE.md` 가 루트에 있으면 정상.

## 9. 자주 보이는 막힘

| 증상 | 원인 / 해결 |
| -- | -- |
| `[[entities/X]]` 가 회색이고 클릭하면 새 파일 생성 | 아직 생성된 페이지 없음. `lint.py` 가 BROKEN_LINK 로 잡아낸다. |
| Templater 의 `{{date}}` 가 그대로 남음 | 새 파일 생성 시 Templater 자동 트리거가 OFF 거나, 템플릿이 templates/ 밖에 있음. |
| 그래프 뷰가 비어 보임 | 페이지 간 wikilink 가 아직 없음. ingest 첫 source 후 다시 보면 점들이 등장. |
| frontmatter 의 list 가 깨짐 | `["[[A]]", "[[B]]"]` 형식 (각 항목 따옴표). 따옴표 빠지면 YAML 파서가 실패. |
| `lint.py` 가 ORPHAN 으로 모든 페이지를 잡음 | index.md 가 카탈로그 갱신 안 된 상태. LLM 에게 "index 갱신" 요청. |
