---
title: "MCP Notification No-Response Spec — id 없는 알림에 응답 금지"
kind: concept
status: stable
severity: "★★"
tags: [mcp, stdio, json-rpc, notifications, spec, claude-cli, hazard, kmcproject]
related_concepts:
  - "[[concepts/Python-Stdio-MCP-Buffering-Hazard]]"
  - "[[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]]"
  - "[[concepts/UE-HttpServer-Body-NullTerm-Hazard]]"
related_synthesis:
  - "[[synthesis/mc-datatable-auto-build-cycle-postmortem]]"
created: 2026-05-26
last_updated: 2026-05-26
---

# MCP Notification No-Response Spec

> **유래**: MCDataTableAuto Phase 3c-3 3 차 fix (2026-05-26). proxy 의 `notifications/*` 처리 시 *error 응답* 반환 → MCP spec 위반 → claude 가 server malformed 처리 가능성 검증.

## 정의

MCP (Model Context Protocol) 의 *JSON-RPC 2.0* 기반 메시지 중 **`notifications/*` 또는 *id 없는 메시지*** 는 *알림 (notification)* 으로 분류. JSON-RPC 2.0 spec 상 **응답 금지**. Server 가 response 반환 시 client (host / claude) 가 *server malformed* 로 판단해 disconnect 가능.

## 자세히

### JSON-RPC 2.0 spec

```
A Notification is a Request object without an "id" member.
A Request object that is a Notification signifies the Client's lack of interest in the corresponding Response object.
The Server MUST NOT reply to a Notification.
```

→ id 없는 request 에 *어떤 응답도 반환 X*. error 응답도 금지.

### MCP 표준 notifications

흔히 사용:
- `notifications/initialized` — claude 가 initialize handshake 완료 후 자동 전송
- `notifications/cancelled` — 진행 중 작업 취소 알림
- `notifications/progress` — 작업 진행률 알림
- `notifications/message` — 일반 메시지

모두 *id 없음* + *응답 없음 기대*.

### 사례 — MCDataTableAuto Phase 3c-3 3차 (2026-05-26)

🟢 **VAULT** — KMCProject 실측.

**위반 코드** (Phase 3a 부터 적용):
```python
def handle_request(req):
    rid = req.get('id')
    method = req.get('method', '')
    ...
    # ❌ 모든 unknown method 에 error 응답
    return {'jsonrpc': '2.0', 'id': rid,
            'error': {'code': -32601,
                      'message': 'method not supported: ' + method}}
```

`notifications/initialized` 가 *handle_request* 에 도달 → *method 비-지원* 으로 분류 → *error 응답 stdout 출력*.

**전형적 handshake 시퀀스 (위반)**:
```
1. claude → proxy : initialize (id=1)        → 응답 OK
2. claude → proxy : notifications/initialized (id 없음)
   proxy → claude : {"error": {"code": -32601, "message": "method not supported"}}  ❌
3. claude : "server malformed" → disconnect
4. claude : ListMcpResources 에 server 누락
```

**Fix**:
```python
def handle_request(req):
    rid = req.get('id')
    method = req.get('method', '')
    # 🚨 MCP spec — notifications/* 는 id 없음 + 응답 금지
    if method.startswith('notifications/') or rid is None:
        log('  notification — no response (per MCP spec)')
        return None  # ✅ 응답 안 함
    ...
```

main loop:
```python
resp = handle_request(req)
if resp is not None:   # None 이면 stdout 출력 skip
    sys.stdout.write(json.dumps(resp) + '\n')
    sys.stdout.flush()
```

→ `return None` + `if not None` check = notifications 에 *어떤 byte 도 stdout 출력 X* → spec 준수.

### MCMaterialAuto 의 정확한 패턴 (답습 reference)

```python
method = req.get('method', '')
is_notification = method.startswith('notifications/') or req.get('id') is None
log('parsed method=' + method + ' is_notification=' + str(is_notification))

# Forward to UE-MCP HTTP regardless (HandleRpcRequest 가 notification 도 200 OK 처리).
resp = forward(req)

# Notifications: per JSON-RPC 2.0 we must NOT write a response.
if is_notification:
    log('notification — no response sent to claude')
    continue   # stdout write skip + loop 다음 iteration
```

→ MCMaterialAuto 는 *forward 는 하되 stdout 출력 안 함*. UE 측이 *200 OK 처리* (그러나 응답 body 는 빈) — proxy 가 그냥 무시.

## 회피 패턴 — 4 Layer

### Layer 1: handle_request 진입 시점 *id check*

```python
if method.startswith('notifications/') or rid is None:
    return None  # 또는 main loop 에서 continue
```

### Layer 2: main loop 의 `if resp is not None` check

```python
resp = handle_request(req)
if resp is not None:
    sys.stdout.write(...)
```

### Layer 3: forward + notification dispatch 분기

```python
# MCMaterialAuto 패턴 — forward 는 하되 stdout skip
resp = forward(req)
if is_notification:
    continue  # stdout 출력 안 함
```

### Layer 4: UE-host server 의 *empty body* 응답

UE-MCP server 가 *notifications/* method 받으면 *empty body 200 OK* 응답. proxy 가 forward 결과 그대로 stdout 출력 시도 시 *parsing 실패* — fallback 으로 `resp = None` 처리.

## 관련 함정

같은 메커니즘 — *MCP spec 위반* 의 다른 변종:

| 변종 | 함정 |
|---|---|
| **Notifications response** (본 concept) | id 없는 알림에 응답 반환 |
| Bidirectional notification | server → client notification 시 *id 자동 부여* 실수 |
| Empty result vs error | resp `null` 일 때 *empty result object* vs *error 응답* 선택 |
| `protocolVersion` mismatch | spec 의 standard version 외 값 → claude 무시 |
| `capabilities` 누락 | initialize 응답에 *required capabilities* 누락 |

## 검증 방법

### Manual proxy spawn

```cmd
echo {"jsonrpc":"2.0","method":"notifications/initialized"} | python mcp_proxy.py
```

→ stdout output 이 *비어있어야* 정상. 어떤 응답이라도 나오면 spec 위반.

### MCP proxy log 패턴

```
handle_request method=notifications/initialized id=None
  notification — no response (per MCP spec)
```

→ *log 만* (file/stderr) 적고 *stdout 출력 0*.

## MCP spec 외 ID 가 없는 경우

JSON-RPC 2.0 에서 *id 있어도 valid notification* 가능 (드뭄). 그러나 MCP 의 표준은:
- *id 있음 + method 있음* = Request → 응답 의무
- *id 없음 + method 있음* = Notification → 응답 금지
- *id 있음 + method 없음 + result/error* = Response → 처리

→ 안전한 dispatch: `method.startswith('notifications/') or rid is None` 양쪽 OR.

## 관련

- [[concepts/Python-Stdio-MCP-Buffering-Hazard]] (MMA-29) — same family (stdio MCP 함정)
- [[concepts/Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard]] — 같은 cycle 발견 (encoding 변종)
- [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] (MMA-31) — UE HTTP side family
- [[synthesis/mc-datatable-auto-build-cycle-postmortem]] (Phase 3c-3 9 cycle 회고)

## 열린 질문

1. ❓ Anthropic claude CLI 의 *server malformed* 판정 정확 기준 — *몇 byte invalid* 또는 *N consecutive error*. 미확정.
2. ❓ UE-MCP server (FHttpServerModule) 가 notification 받으면 *empty body 200 OK* 표준 동작 — 확인 미수행.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| JSON-RPC 2.0 spec notifications no-response | 🟢 VAULT | JSON-RPC 2.0 표준 문서 + MCP spec |
| MCMaterialAuto 의 정확한 패턴 (forward + continue) | 🟢 VAULT | KMCProject 실측 코드 read |
| 우리 cycle 의 위반 + fix | 🟢 VAULT | Phase 3c-3 3차 실측 |
| spec 위반 시 claude 의 정확한 행동 | 🟡 PARTIAL | "server malformed → disconnect" 추론 — 정확 internals 미검증 |

## 변경 이력

- 2026-05-26: 초안 작성. MCDataTableAuto Phase 3c-3 3차 발견 — notifications/* error 응답 spec 위반. MCMaterialAuto 패턴 답습 정확화 (`return None` + `if resp is not None` check). 4-Layer 회피 패턴 정리.
