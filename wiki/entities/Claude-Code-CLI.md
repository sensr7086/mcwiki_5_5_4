---
title: "Claude Code CLI"
kind: entity
status: stub
parent: integration-external
tags: [external, claude, cli, integration, mcp, ue-574-bridge]
module: external (not UE)
external_ref: "https://docs.claude.com/en/docs/claude-code"
created: 2026-05-22
last_updated: 2026-05-22
---

# Claude Code CLI

Anthropic 의 **command-line agentic coding tool** — `claude.exe` (Windows) / `claude` (Unix). MCP (Model Context Protocol) 서버 연결, 도구 사용, 멀티 턴 대화, non-interactive `-p` 모드 지원. MCMaterialAuto 는 이를 spawn 하여 UE Editor 와 LLM 을 통합.

> ⚠️ **외부 도구** — vault 의 `ue-` scope 밖이지만 UE+MCP 통합 작업의 핵심 참조점 → vault 정직성 §06 에 따라 stub entity 등록.

## 핵심 모드

| 모드 | 호출 | 용도 |
|---|---|---|
| Interactive REPL | `claude` | 사용자 대화 |
| Non-interactive `-p` | `claude -p "<prompt>"` | 자동화 단발 호출 |
| Streaming output | `--output-format stream-json --verbose` | NDJSON line-by-line |

## 주요 CLI 인자 (MCMaterialAuto 사용)

| 인자 | 역할 |
|---|---|
| `-p <prompt>` | non-interactive single prompt |
| `--mcp-config <json>` | MCP server config 파일 |
| `--allowed-tools <csv>` | 사전 활성화 도구 list (Cowork deferred 우회) |
| `--disallowed-tools <csv>` | 차단 도구 (ToolSearch 차단 의무) |
| `--permission-mode bypassPermissions` | 자동 허용 (non-interactive 의무) |
| `--max-turns <n>` | turn budget |
| `--model <name>` | 모델 선택 (opus / sonnet / haiku) |
| `--append-system-prompt <file>` | system prompt 추가 |

## 관련 함정

- [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]] — Cowork mode deferred registry 의무 우회
- Non-interactive 모드에서 permission prompt 불가 → `bypassPermissions` 필수 (MMA-23)
- OAuth 인증 vs API key 충돌 (MMA-22) — 환경변수 우선순위
- 일부 도구가 `--disallowed-tools` 에 들어가도 system prompt 의무 reinforcement 권고

## 관련 entity

- [[MCP-Protocol]] (사용 프로토콜)
- [[FInteractiveProcess]] (UE 측 spawn)

## Citation Disclosure

| 주장 | Tier |
|---|---|
| `-p` non-interactive 모드 동작 | 🟢 VAULT (실측 — MMA-23 fix) |
| `--allowed-tools` / `--disallowed-tools` 의무 | 🟢 VAULT (MMA-24/27 실측) |
| OAuth vs API key 충돌 mechanism | 🟡 PARTIAL (환경변수 우선순위 일부 미특정) |
| Cowork deferred registry 임계치 | 🔴 INFERRED (공식 문서 미확인) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-22/23/24/27 filing-back cross-link)
