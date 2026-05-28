---
type: concept
title: "Python Stdio MCP Buffering Hazard — pipe mode 4KB block-buffer 로 인한 tool_use hang"
aliases: [Python Stdio Buffering, MCP Proxy Block-Buffer, Stdio Hang]
sources:
  - "[[sources/ue-build-skill]]"
related_concepts: []
tags: [ue, mcp, claude-cli, python, stdio, buffering, hazard, kmcproject]
last_updated: 2026-05-22
---

# Python Stdio MCP Buffering Hazard

> KMCProject MCMaterialAuto v0.14.4 회기 (2026-05-22) 의 *vault filing-back*. 🟢 vault scope: `ue-` 일반 ([[00_meta/08_VaultScopePolicy]]) — 모든 Claude CLI + Python stdio MCP proxy 환경에 적용.

## 1. 정의 (한 줄)

Python interpreter 의 *stdin pipe-mode default block-buffering (4 KB)* 가 Claude CLI 의 stdio MCP transport 와 결합 시 — *handshake (initialize/tools/list)* 는 우연히 통과하지만 *후속 tools/call* 단일 메시지가 4KB buffer 못 채워 *영원히 대기*. claude tool_use 후 무한 hang.

## 2. 자세히

### 2.1. 메커니즘

| 단계 | 동작 |
|---|---|
| 1 | Claude CLI 가 Python proxy.py 를 stdio MCP server 로 spawn |
| 2 | Python 의 stdin = pipe (terminal 아님) → **default block-buffered (4KB)** |
| 3 | `for line in sys.stdin:` iterator 가 *내부 buffer 채워질 때까지* 대기 |
| 4 | handshake 메시지들 (initialize ~ tools/list) 가 *합쳐서 4KB* 채워서 우연 통과 |
| 5 | tools/call 단일 메시지 (~300-500 bytes) 가 buffer 못 채움 → **영원히 대기** |

### 2.2. 비결정성

- terminal stdin: **line-buffered** ✅ → 즉시 처리
- pipe stdin: **block-buffered (4KB)** ⚠ → 조건부 hang
- 같은 코드가 *수동 PowerShell 호출* 시 정상 / *Claude CLI 호출* 시 hang

### 2.3. KMCProject 실측 증거

mcp_proxy_rpc.log (2026-05-22):
```
[21:49:26] stdin recv (305 bytes): initialize
[21:49:26] stdin recv (54 bytes): notifications/initialized
[21:49:26] stdin recv (46 bytes): tools/list      ← 합쳐서 ~405 bytes
[21:49:36] stdin EOF — exit                       ← 10초 후 claude timeout
```

→ handshake 만 통과, tools/call 도착 *0건*. claude code 측에서는 tool_use *전송 시도*했지만 proxy 의 stdin buffer 가 채워지지 않음.

## 3. 회피 패턴

### 3.1. 이중 안전 fix (의무)

```python
# 1단계: Python interpreter 자체 unbuffered
# CLI spawn 시: python -u proxy.py  (또는 `py -u`)

# 2단계: proxy.py 안 stdin 명시 재구성 (Python 3.7+)
import sys
sys.stdin.reconfigure(line_buffering=True)
sys.stdout.reconfigure(line_buffering=True)

# 3단계: for-line iterator 대신 readline() 사용
while True:
    line = sys.stdin.readline()
    if not line: break  # EOF
    # process ...
```

### 3.2. mcp-config JSON 예시

```json
{
  "mcpServers": {
    "ue_material": {
      "type": "stdio",
      "command": "py",
      "args": ["-u", "C:/path/to/proxy.py"],   // ⭐ -u flag 의무
      "env": { "UE_MCP_URL": "...", "UE_MCP_TOKEN": "..." }
    }
  }
}
```

### 3.3. 진단

증상별 진단:
- `[system:init] mcp=[...]` 표시되지만 tool_use 후 hang → **MMA-29**
- handshake 통과 + 첫 tool_use 안 응답 → block-buffering 의심
- proxy 의 stderr 안 *handshake 다음 stdin recv 라인 없음* → 결정적

## 4. 변형 / 사례 / 응용

### 4.1. KMCProject MCMaterialAuto v0.14.4 사례 (`mc-`)

> *vault scope*: [[00_meta/08_VaultScopePolicy]] §case study.

UE-MCP HTTP server + Python stdio proxy 패턴 — Claude CLI 가 stdio 표준 transport 로 proxy 와 통신 → proxy 가 HTTP RPC 로 UE 에 forward. v0.14.4 fix 후 handshake/tool_use 모두 정상.

자세히 — KMCProject Docs/MCMaterialAuto_Design.md §변경 이력 v0.14.4.

### 4.2. 일반 적용

같은 패턴이 모든 *Python stdio MCP server* 에 발현:
- Anthropic 의 example mcp-server-python
- FastMCP / `mcp` SDK
- 자체 구현 stdio MCP server

## 5. 관련 entity

- (없음 — Python interpreter 레벨 함정, UClass 무관)

## 6. 열린 질문

- [ ] Python `-u` flag 의 정확한 영향 범위 — stdin/stdout/stderr 모두 unbuffered?
- [ ] Windows `py launcher` 가 `-u` flag 를 Python 에 정확히 forward 하는가? (사용자 실측 확인됨, 일반 동작 미검증)
- [ ] Claude CLI 의 정확한 *tool_use → stdin* 동기화 매커니즘 — flush 시점

## 7. Cross-link

- [[concepts/Editor-Only-4-Tier-Separation]] — 일반 build 정책 (이번 함정과 직교)
- [[sources/ue-build-skill]] — UBT 메인
- [[00_meta/06_VaultCitationRule]] — 3-tier citation 의무

## 8. Citation Disclosure ([[00_meta/06_VaultCitationRule]])

- 🟢 VAULT: Python stdin pipe-mode block-buffering — Python 공식 docs 표준 동작
- 🟢 VAULT: `python -u` unbuffered 강제 — CPython 표준 flag
- 🟢 VAULT: KMCProject v0.14.4 사례 — mcp_proxy_rpc.log 직접 증거
- 🟡 PARTIAL: Anthropic Claude CLI 의 stdio MCP transport 정확한 사양 — Anthropic docs 기반
- 🔴 INFERRED: Windows `py launcher` 의 `-u` forwarding 동작 — 실측 검증

## 9. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-22 | 초안 작성 — KMCProject MCMaterialAuto v0.14.4 filing-back |
