---
title: "Python Stdio MCP NonAscii Windows cp949 Hazard — json.dumps ensure_ascii=False + Windows stdout cp949 충돌"
kind: concept
status: stable
severity: "★★★"
tags: [python, mcp, stdio, encoding, cp949, windows, claude-cli, hazard, ue-574, kmcproject]
related_concepts:
  - "[[concepts/Python-Stdio-MCP-Buffering-Hazard]]"
  - "[[concepts/MCP-Notification-No-Response-Spec]]"
  - "[[concepts/UE-HttpServer-Body-NullTerm-Hazard]]"
  - "[[concepts/UE-Phantom-Header-Hallucination-Hazard]]"
related_synthesis:
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
  - "[[synthesis/mc-datatable-auto-build-cycle-postmortem]]"
created: 2026-05-26
last_updated: 2026-05-26
---

# Python Stdio MCP NonAscii Windows cp949 Hazard

> **유래**: MCDataTableAuto Phase 3c-3 9 cycle 끝에 발견 (2026-05-26). 한국어 Windows 환경에서 *9 cycle 진단* 끝에 `json.dumps(ensure_ascii=False)` + cp949 stdout 충돌 확정. **MMA-29 family 의 encoding 변종**.

## 정의

Python MCP stdio server (또는 proxy) 가 **`json.dumps(obj, ensure_ascii=False)`** 로 *non-ASCII (한글 등) 문자 그대로* stdout 출력. **Windows 한국어 환경의 stdout default encoding = cp949** — UTF-8 한글 character 를 cp949 로 encode 실패 또는 깨짐. claude / host 가 *malformed JSON* 수신 → *server 무효 처리* → ListMcpResources 에서 누락.

증상:
- proxy spawn 정상 + handshake (initialize / notifications / tools/list) 모든 로그 정상
- forward / parse 모두 정상
- **그런데 claude 응답: "MCP 서버는 mcwiki 만"** (우리 server 누락)
- 도구 호출 시도 `mcp__<our_server>__*` → *not found* / *deferred tools 0건 매칭*

진단 어려움 — *log 상으로는 모든 단계 OK*. 응답 *encoding 깨짐* 은 *log file 에는 정상 (UTF-8 file write)* 나타나지만 *stdout pipe* 에서만 깨짐.

## 자세히

### 사례 — MCDataTableAuto Phase 3c-3 (2026-05-26)

🟢 **VAULT** — KMCProject 9 cycle 실측 끝 발견.

**위반 코드** (Phase 3a 부터 적용 — *최적화 가정* — "한글 가독성 위해"):
```python
# parse_spreadsheet 응답
return {'result': {
    'content': [{'type': 'text',
                 'text': json.dumps(result, ensure_ascii=False)}]  # ❌
}}

# main loop stdout
out_line = json.dumps(resp, ensure_ascii=False)  # ❌
sys.stdout.write(out_line + '\n')
sys.stdout.flush()
```

**문제 chain**:
1. UE-MCP server 의 `BuildDataTableTools` description 에 *한글 포함* (예: "(Phase 3c-3) Generate C++ USTRUCT header... *시트명 (정책 P2 정규화 적용됨)* + fields")
2. UE 응답 JSON body 에 *한글 UTF-8 그대로* (3572 bytes)
3. proxy 가 `json.loads(raw)` 정상 (UTF-8 decode)
4. proxy 가 `json.dumps(resp, ensure_ascii=False)` → **한글 그대로** Python string
5. `sys.stdout.write(...)` — Windows 한국어 default `sys.stdout.encoding = 'cp949'`
6. → 한글 UTF-8 character (예: U+C2DC `시`) 를 cp949 로 encode 시도 → *encoding 깨짐 또는 UnicodeEncodeError*
7. claude (호스트) 가 *malformed JSON* 또는 *깨진 byte stream* 수신
8. → claude 가 *server 응답 invalid* 로 판단 → ListMcpResources 에서 *server 제외*

**Fix** — MCMaterialAuto 답습 (default `ensure_ascii=True`):
```python
# 정정
return {'result': {
    'content': [{'type': 'text',
                 'text': json.dumps(result)}]  # ✅ default ASCII escape
}}

out_line = json.dumps(resp)  # ✅
```

→ 한글 `시` → `시` ASCII escape → **모든 stdout output ASCII only** → Windows cp949 안전.

### 9 cycle 진단 history (왜 9차에 도달했나)

| Cycle | 가설 | 결과 |
|---|---|---|
| 1차 | Widget 모델 + create_datatable | 무관 |
| 2차 | fill_rows + auto-trigger | 무관 |
| 3차 | proxy notifications/* spec ([[concepts/MCP-Notification-No-Response-Spec]]) | 일부 fix (별도 함정) |
| 4차 | generate_row_struct 자동 생성 | 무관 |
| 5차 | proxy local stub → UE forward | 일부 fix |
| 6차 | 진단 log 강화 | 진단 도움 |
| 7차 | capabilities resources/prompts | 의도 효과 없음 (틀린 가설) |
| 8차 | New Session 버튼 | 일부 fix |
| **9차** | **ensure_ascii=False fix** | ⭐⭐⭐ **결정적 fix** |

**핵심 교훈**: *MCMaterialAuto 답습 시 정확 grep 안 한 경우*. 우리 cycle 의 *최적화 가정* (한글 가독성) 이 *함정 trigger*.

## 회피 — 3 패턴

### Pattern 1 (⭐ 추천) — default `ensure_ascii=True`

```python
out = json.dumps(obj)  # default — 모든 non-ASCII \uXXXX escape
```

JSON spec 100% 준수 + 모든 환경 안전 + 가장 단순.

**단점**: log 가독성 — `시` 가 *file 안에서도 ASCII escape* 형태. log 파일은 사람이 읽기 어려움.

→ Fix: *log 함수만 따로* `ensure_ascii=False` 사용 (file 만, stdout 아님):
```python
def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')   # file: UTF-8 명시
    print('[mcp_proxy] ' + line, file=sys.stderr, flush=True)
    # stdout 의 JSON 응답만 ensure_ascii=True
```

### Pattern 2 — `sys.stdout.reconfigure(encoding='utf-8')` 명시

```python
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
# 또는 (Python 3.7+):
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
```

stdout 자체를 UTF-8 강제. `ensure_ascii=False` 도 안전.

**단점**: Windows console *cp949 가정 코드* 와 충돌 가능. 모든 환경 검증 필요.

### Pattern 3 — `PYTHONIOENCODING=utf-8` 환경변수

```cpp
// claude spawn 시 env 추가 (UE-MCP config writer 에서)
Env->SetStringField(TEXT("PYTHONIOENCODING"), TEXT("utf-8"));
```

Python 인터프리터 시작 시 stdin/stdout/stderr 모두 UTF-8.

**단점**: env 설정 누락 시 다시 함정. *Pattern 1* 가 더 robust.

## 검증 방법

### Standalone 검증

Python proxy 직접 실행 + 한글 응답 simulate:
```cmd
python -c "import sys, json; print(json.dumps({'text': '시트명 정규화'}, ensure_ascii=False))"
```

Windows 한국어 환경에서:
- `cmd` chcp 949 (default) → 깨짐 또는 UnicodeEncodeError
- `cmd` chcp 65001 (UTF-8) → 정상

`ensure_ascii=True` (또는 default):
```cmd
python -c "import sys, json; print(json.dumps({'text': '시트명 정규화'}))"
```
→ 어디서나 `{"text": "시트..."}` 정상.

### MCP server stdio 검증

claude CLI spawn 후 `mcp_proxy_*.log` 의 *stdout sent (N bytes)* 라인 확인. MCMaterialAuto 패턴.

### 직접 raw byte 확인

```cmd
python mcp_proxy.py < test_input.json > out.bin
```

→ `out.bin` 의 hex dump 검증. UTF-8 한글 (3 byte sequence `EC 8B 9C` for 시) 또는 ASCII escape (`\u`) 확인.

## 관련 사례

같은 메커니즘의 다른 변종:

| 변종 | 함정 |
|---|---|
| **JSON dumps + cp949** (본 concept) | 한글 응답 stdout 출력 |
| CSV write + cp949 | 한글 데이터 csv.writer 출력 |
| Subprocess stdout capture | `subprocess.run(..., capture_output=True)` 의 stdout decode |
| Print + cp949 | 한글 단순 print() 가 cp949 console 에 출력 시 깨짐 |
| File open + 기본 encoding | `open(path, 'w')` 가 cp949 default → 한글 write 실패 |

모두 같은 회피 — *UTF-8 명시* 또는 *ASCII escape*.

## 다른 OS 비교

| OS | stdout default encoding | 우리 함정 영향 |
|---|---|---|
| Windows 한국어 | **cp949** | ❌ 영향 큼 |
| Windows 영어 | cp1252 | ⚠ 한글 영향 (영문은 OK) |
| macOS | UTF-8 | ✅ 안전 |
| Linux | UTF-8 (locale 의존) | ✅ 안전 (대부분) |
| Windows + chcp 65001 | UTF-8 | ✅ 안전 |

→ **한국어 Windows 사용자에게 특히 위험**. 본 vault scope 의 KMCProject case study 가 그 환경.

## 관련

- [[concepts/Python-Stdio-MCP-Buffering-Hazard]] (MMA-29 — stdin buffering family)
- [[concepts/MCP-Notification-No-Response-Spec]] (같은 Phase 3c-3 cycle 발견 — JSON-RPC spec 변종)
- [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] (MMA-31 — UE HTTP body family)
- [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (Phase 1a — vault 인용 hallucination family)
- [[synthesis/ue-llm-assumption-hazard-family]] (LLM 추측 hazard family)
- [[synthesis/mc-datatable-auto-build-cycle-postmortem]] (Phase 3c-3 9 cycle 회고)

## 열린 질문

1. ❓ Windows console *chcp 65001* (UTF-8) 강제 시 우리 proxy 가 `ensure_ascii=False` 도 안전한가 — 검증 미수행.
2. ❓ Python 3.7+ 의 *UTF-8 mode* (`-X utf8` flag) 가 강제 시 — 같은 효과? `-u` flag 와 함께 권장 가능.
3. ❓ Anthropic Claude CLI 의 *stdin/stdout 처리* — claude 자체가 *UTF-8 강제* 안 하는 이유. spec 명시 가능성.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| MCMaterialAuto vs 우리 proxy 의 `ensure_ascii` 차이 | 🟢 VAULT | KMCProject 양쪽 mcp_proxy.py 직접 read + diff |
| Windows 한국어 stdout default = cp949 | 🟢 VAULT | Python 표준 — `sys.stdout.encoding` 검증 가능 |
| 9 cycle 끝에 발견 | 🟢 VAULT | KMCProject Phase 3c-3 1~9차 실측 log |
| claude 가 *malformed JSON* 으로 인식 → server 무효 처리 | 🟡 PARTIAL | 가장 그럴듯한 가설 — proxy + UE log 종합 추론. 직접 claude internals 검증 미수행 |
| Pattern 2 (stdout.reconfigure) 가 `ensure_ascii=False` 와 함께 안전 | 🔴 INFERRED | 미검증 |
| 다른 OS (mac/linux) 영향 | 🟡 PARTIAL | locale 의존 — 일반 지식 |

## 변경 이력

- 2026-05-26: 초안 작성. MCDataTableAuto Phase 3c-3 9 cycle 끝 발견 — `ensure_ascii=False` + Windows cp949 stdout 충돌. MCMaterialAuto 답습 정확화 (default `ensure_ascii=True`). 3 회피 패턴 + 검증 방법 정리. [[synthesis/ue-llm-assumption-hazard-family]] 의 *encoding 변종* family 확장.
- 2026-05-26: `related_concepts` 에 MCP-Notification-No-Response-Spec 추가 (reciprocal cross-link) + `## 관련` 절에도 추가.
