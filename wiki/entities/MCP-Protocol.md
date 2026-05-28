---
title: "MCP (Model Context Protocol)"
kind: entity
status: stub
parent: integration-external
tags: [external, mcp, protocol, json-rpc, llm-tool, ue-574-bridge]
module: external (not UE)
external_ref: "https://modelcontextprotocol.io/"
created: 2026-05-22
last_updated: 2026-05-22
---

# MCP (Model Context Protocol)

Anthropic 의 **LLM ↔ 외부 도구 통합 표준 프로토콜** — JSON-RPC 2.0 기반. Server (도구 제공) ↔ Client (Claude Code CLI 등) 의 양방향 통신. stdio / HTTP / SSE 3개 transport 지원. Tool 정의 + tool call + initialize handshake + notification 4 message family.

> ⚠️ **외부 표준** — vault `ue-` scope 외, 통합 참조점 → stub entity.

## 핵심 message family

| 종류 | 방향 | 의미 |
|---|---|---|
| `initialize` | C → S | handshake — server capability 응답 |
| `tools/list` | C → S | server 의 tool 목록 |
| `tools/call` | C → S | tool 호출 (name + arguments) |
| `notifications/*` | both | 비응답 메시지 (progress, log 등) |
| `notifications/initialized` | C → S | handshake 완료 ack |

## Transport

| Transport | 사용 패턴 | 비고 |
|---|---|---|
| **stdio** | 자식 프로세스 stdin/stdout | MCMaterialAuto 채택 (Python proxy) |
| **HTTP** | REST POST | request-response 단발 |
| **SSE** | streaming | long-lived |

## 사용 패턴 (MCMaterialAuto)

```
[Claude CLI] ↔ stdio ↔ [Python proxy] ↔ HTTP ↔ [UE FHttpServerModule]
                                            (mcp__ue_material__*)
```

## 관련 함정

- [[concepts/Python-Stdio-MCP-Buffering-Hazard]] — stdio block-buffering
- [[concepts/UE-HttpServer-Body-NullTerm-Hazard]] — HTTP body null-term
- [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]] — Cowork deferred registry 우회
- Tool namespace: `mcp__<server>__<tool>` — server name 은 `[a-z_]+` 만 (dash → underscore, MMA-19)

## 관련 entity

- [[Claude-Code-CLI]] (client)
- [[FInteractiveProcess]] (UE 측 spawn)

## Citation Disclosure

| 주장 | Tier |
|---|---|
| JSON-RPC 2.0 기반 | 🟢 VAULT (공식 spec) |
| 4 message family | 🟢 VAULT |
| 3 transport 지원 | 🟢 VAULT |
| stdio block-buffering hazard | 🟢 VAULT (MMA-29 실측) |
| HTTP body null-term hazard | 🟢 VAULT (MMA-31 실측 — UE 측 limitation) |
| Server name `[a-z_]+` 제약 | 🟢 VAULT (MMA-19 실측) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-19/26/29/31 filing-back cross-link)
