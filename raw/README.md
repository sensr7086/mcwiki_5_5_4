# raw/ — Source of Truth

> **불변 (Immutable).** 사용자만 추가/삭제. LLM 은 절대 수정하지 않는다.

Karpathy 의 LLM Wiki 패턴 §아키텍처 layer 1.

## 무엇이 들어오는가

| 종류 | 위치 | 도입 방법 |
| -- | -- | -- |
| 웹 글 (markdown 변환) | `raw/articles/` | Obsidian Web Clipper |
| PDF (논문/책 챕터) | `raw/papers/` | 수동 복사 |
| YouTube 자막 + 메타 | `raw/youtube/` | `python ../tools/youtube_to_raw.py <url>` |
| 텍스트 노트 | `raw/notes/` | 수동 |
| 이미지 | `raw/assets/` | Obsidian 의 "Download attachments for current file" |
| 오디오/비디오 | `raw/audio/`, `raw/video/` | 수동. transcribe 는 별도. |

하위 폴더는 자유롭게 추가 가능. 단 `raw/` 바로 아래는 위 분류만 권장 (LLM 의 ingest 가 깔끔해진다).

## 명명 규칙 (권장)

- `raw/articles/<slug>.md` — slug 는 kebab-case
- `raw/papers/<author-year-shorttitle>.pdf`
- `raw/youtube/<channel>-<video-id>.md`

엄격하지 않다. 단 ingest 후 만들어지는 `wiki/sources/<slug>.md` 의 slug 와 짝이 맞도록.

## 무엇을 *하지 않는가*

- 본문 편집 X (오타 수정마저도. 원본 보존이 본 layer 의 정체성).
- 별도 메타 파일 (`.meta.json` 등) 추가 X. 메타는 `wiki/sources/<slug>.md` 의 frontmatter 에.
- LLM 이 만든 요약/해석을 raw 안에 두지 않기. 그것은 wiki/.

## raw 와 wiki 의 짝

- 모든 `raw/<path>/<file>` 는 1:1 로 `wiki/sources/<slug>.md` 와 대응 (ingest 후).
- `wiki/sources/<slug>.md` 의 frontmatter `source_path` 가 raw 파일의 상대경로.

## 정정이 필요할 때

원본이 잘못되어 보이면:

1. 원본을 *수정하지 말고* 사용자가 직접 새 파일을 추가 (`raw/<path>/<file>-corrected.md`).
2. 두 source 모두 ingest. wiki 에서 두 source 를 같은 entity 의 `## Contradictions` 절에서 비교.
3. 어느 쪽이 옳은지의 판단은 사용자.
