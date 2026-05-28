---
title: MCP Tool Schema Strip Hazard
slug: MCP-Tool-Schema-Strip-Hazard
kind: concept
status: live
confidence: 🟢 VAULT
last_updated: 2026-05-26
engine_version: 5.7.4
related_concepts:
  - MCP-Tool-Schema-LLM-Friendly-Design
  - MCP-Notification-No-Response-Spec
  - Python-Stdio-MCP-NonAscii-Windows-cp949-Hazard
related_synthesis:
  - mc-datatable-auto-blueprint
  - mc-datatable-auto-build-cycle-postmortem
related_entities:
  - MCP-Protocol
tags: [mcp, tool-schema, jsonschema, claude-cli, parameter-stripping]
sources:
  - "MCDataTableAuto Phase 3c-3 후속 cycle (2026-05-26) — 사용자 진단 확정"
---

# MCP Tool Schema Strip Hazard

## 한 줄 요약

**MCP 프레임워크 (Claude SDK side) 는 `tools/list` 의 JSONSchema `properties` 에 *선언되지 않은* 도구 호출 인자를 strip 해서 서버까지 전달 안 함.** schema 가 *완전 매니페스트* 의무 — 누락 시 `-32602` 또는 *조용한 인자 손실*.

## 권위 (🟢 VAULT — 사용자 진단 확정)

MCDataTableAuto Phase 3c-3 후속 사용자 스크린샷 (2026-05-26) — Claude 의 정확한 진단:

> "ToolSearch 로 재확인한 schema 는 `properties: {asset_path}` 만 선언 — `rows` 파라미터 누락.
>  MCP 프레임워크가 schema 미선언 파라미터를 strip 하기 때문에 `rows` 배열이 서버까지 전달되지 않음."

실측:
- UE-host MCP server `fill_rows` 핸들러 — args: `{asset_path, rows[]}`
- `tools/list` schema 등록 시 `rows` 누락 → 호출 시 `-32602 fill_rows requires: ... rows (array)`
- schema 에 `rows` 정확 등록 → 정상 동작

## 함정 family

### 1. schema 부분 매니페스트 = 인자 손실

LLM (Claude) 이 도구 호출 시 generate 한 args JSON 은 *전부* 보내지 않음. MCP 프레임워크가:
- schema 의 `properties` key 와 *일치하지 않는* args 키를 제거
- `additionalProperties: false` (default) — 미선언 키 strip
- type validation 실패 시 reject 또는 coerce

→ 도구 핸들러는 *부분 args* 만 수신 → 필수 인자 누락 에러.

### 2. 발현 양상

| 증상 | 원인 |
|---|---|
| `-32602 invalid params` | 필수 인자 schema 누락 → strip 됨 |
| LLM 응답에 "tried with X" 인데 서버 args 안 X | 부분 매니페스트 |
| 일부 args 만 정상 동작 | properties 일부만 선언됨 |

### 3. JSONSchema 완전 매니페스트 패턴 (UE 측)

```cpp
MakeSchema([](TSharedPtr<FJsonObject> P){
    // 1. 기본 string
    P->SetObjectField(TEXT("asset_path"), StringProp());

    // 2. array — items schema 의무
    TSharedPtr<FJsonObject> RowsArr = MakeShared<FJsonObject>();
    RowsArr->SetStringField(TEXT("type"), TEXT("array"));
    {
        TSharedPtr<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("type"), TEXT("object"));
        TSharedPtr<FJsonObject> ItemProps = MakeShared<FJsonObject>();
        ItemProps->SetObjectField(TEXT("row_name"), StringProp());
        TSharedPtr<FJsonObject> Fields = MakeShared<FJsonObject>();
        Fields->SetStringField(TEXT("type"), TEXT("object"));
        ItemProps->SetObjectField(TEXT("fields"), Fields);
        Item->SetObjectField(TEXT("properties"), ItemProps);
        Item->SetArrayField(TEXT("required"), { "row_name", "fields" });
        RowsArr->SetObjectField(TEXT("items"), Item);
    }
    P->SetObjectField(TEXT("rows"), RowsArr);

    // 3. optional fields — properties 에 추가, required 에 미포함
    P->SetObjectField(TEXT("merge_policy"), StringProp());
}, /*required*/ { TEXT("asset_path"), TEXT("rows") })
```

### 4. nested object — type=object 만 선언해도 *통과 가능*

`fields` 가 freeform object 인 경우 `{ type: "object" }` 만 선언 → 안의 모든 key 통과. 만약 `additionalProperties: false` 가 강제되면 안의 key 도 strip 됨 — UE 측에서 받는 시점에 *원하는 모든 field* 도달 보장 필요 시 명시.

### 5. description 의 매개변수 안내 ≠ schema

도구 description 안에 `Args: asset_path, rows[]` 라고 *적어도* schema 에 없으면 strip. **description 은 LLM 가이드**, **schema 는 hard contract**.

## 회피 패턴 (의무)

1. **schema 와 핸들러 args 1:1 매칭** — 모든 핸들러 사용 인자는 schema 에 등록.
2. **required vs optional 명확화** — `required` 배열에 의무 인자 명시.
3. **array / object 타입** — `items` / `properties` nested schema 작성.
4. **변경 시 schema + 핸들러 동시 갱신** — 한쪽만 변경 시 즉시 strip 발생.

## 진단 절차 (-32602 받았을 때)

1. **서버 핸들러 코드 보기** — args parse 시점 (TryGetStringField / TryGetArrayField) 확인
2. **schema 보기** — properties key 와 핸들러 args 매칭 여부
3. **LLM 호출 args 보기** — Claude 의 `tool_use` JSON 의 input 부분 (proxy log)
4. **strip 확인** — LLM 이 보낸 args 와 서버 수신 args 비교 → 누락 키 = schema 미선언

## MCDataTableAuto 적용 사례

- Phase 3c-3 후속 (2026-05-26) — fill_rows `rows` 누락 사례 정식 trigger.
- 사용자 진단 → schema 갱신 → 정상 동작.

## 변경 이력

- **2026-05-26** — 신규 작성. MCDataTableAuto Phase 3c-3 후속 cycle 에서 fill_rows `rows` 인자 strip 확정 → 정식화. Claude 자체 진단으로부터 추출.
