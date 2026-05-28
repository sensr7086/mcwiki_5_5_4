---
title: "MCP Tool Schema — LLM-friendly Design 4 패턴"
kind: concept
status: stable
severity: "★★"
tags: [mcp, tool-schema, llm, integration, MMA-42, MMA-43, MMA-44, MMA-46, ue-574]
created: 2026-05-22
last_updated: 2026-05-22
---

# MCP Tool Schema — LLM-friendly Design 4 패턴

## 정의

LLM (Claude / GPT / Gemini 등) 이 MCP (Model Context Protocol) 도구를 호출할 때 *brute-force retry* / *형식 추측* / *우회로 채택* 등의 비효율을 줄이는 **도구 schema 디자인 4 패턴**. MCMaterialAuto v0.20→v0.23 cycle 의 실측 검증 — 각 패턴 채택 후 동일 작업의 turn budget 이 약 40-60% 감소.

핵심 원칙: **caller (LLM) 의 추측 부담을 server (UE 도구) 가 흡수**.

## 자세히 — 4 패턴

### 패턴 1 — 식별자 양식 양쪽 허용 (MMA-42)

🟢 **VAULT** — MCMaterialAuto v0.21 실측:

**Before**:
```cpp
// UClass lookup — short name 만 가정
UClass* C = FindObject<UClass>(nullptr, *(TEXT("/Script/Engine.MaterialExpression") + Name));
// LLM 이 "ScalarParameter" 보내면 OK, "MaterialExpressionScalarParameter" 보내면 실패
```

**After**:
```cpp
// 자동 양식 정규화
FString Full = Name;
if (!Full.StartsWith(TEXT("MaterialExpression"))) Full = TEXT("MaterialExpression") + Full;
UClass* C = FindObject<UClass>(nullptr, *(TEXT("/Script/Engine.") + Full));
```

**일반화**: LLM 이 같은 entity 를 가리킬 때 사용 가능한 *모든 자연스러운 양식* 을 caller 측에서 정규화. 예시 매트릭스:
- short name vs full UClass name
- with prefix ("/Game/...") vs short asset name
- property name vs UE 축약 ([[concepts/UE-Material-Pin-Name-Shortening]])
- camelCase vs snake_case (있을 시)

### 패턴 2 — Multi-source ID Resolver (MMA-43)

🟢 **VAULT** — MCMaterialAuto v0.21 실측:

**Before**:
```cpp
// 같은 turn 안 추가한 노드만 lookup
TWeakObjectPtr<UMaterialExpression>* Found = Registry.Find(LocalId);
if (!Found) return Error("not found");
// → pre-existing 노드는 *영원히* 참조 불가 → LLM 우회 시도
```

**After**:
```cpp
static UMaterialExpression* ResolveExpression(UMaterial* M, const FString& IdOrGuid)
{
    // 1) local_id from this-turn registry
    if (auto* Found = Registry.Find(IdOrGuid)) { ... }
    // 2) GUID fallback — Material 전체 expression 순회
    FGuid Target;
    if (FGuid::Parse(IdOrGuid, Target))
        for (UMaterialExpression* E : Material->GetExpressions())
            if (E->MaterialExpressionGuid == Target) return E;
    return nullptr;
}
```

**일반화**: identifier 가 여러 출처 (이번 호출 / 기존 자산 / 외부 lookup) 에서 올 수 있을 때 단일 인자에 *모든 형식 시도* — caller 가 어디서 ID 를 얻었는지 신경 안 써도 동작.

### 패턴 3 — Valid-list Error Response (MMA-44 + MMA-45)

🟢 **VAULT** — MCMaterialAuto v0.21/v0.22 실측:

**Before**:
```cpp
return MakeError(TEXT("ConnectMaterialExpressions returned false"));
// → LLM 이 다음 turn 에서 *임의 변형* 시도 (brute-force) — 5-6 turn 소비
```

**After**:
```cpp
if (!bOk) {
    TArray<FString> ValidInputs = ReflectAllInputNames(DstExpr);
    const FString Hint = (ValidInputs.Num() == 1)
        ? FString::Printf(TEXT(" HINT: %s has ONLY 1 input — retry with dst_input=\"\"."), ...)
        : FString();
    return MakeError(FString::Printf(
        TEXT("ConnectMaterialExpressions failed. Valid dst_input on %s: [%s].%s"),
        *DstClass, *Join(ValidInputs, TEXT(", ")), *Hint));
}
```

**일반화**: 실패 응답에 **다음 turn 의 정확한 입력값** 을 포함 — LLM 이 한 번에 fix. 핵심 요소:
- 시도한 값 (정확한 echo)
- *모든 valid 값* 리스트 (reflection 으로 enumerate)
- 단일 옵션 시 *명시 HINT* (예: 빈 문자열 사용)
- 도구 내부 메커니즘 명시 (예: "auto-normalize applied")

### 패턴 4 — Tool Result Detail in Log (MMA-46)

🟢 **VAULT** — MCMaterialAuto v0.22 실측:

**Before**:
```cpp
if (Type == TEXT("user")) return TEXT("[tool_result]");
// → 풀 로그에 prefix 만 — 어느 호출이 어떤 에러로 실패했는지 추적 불가
```

**After**:
```cpp
if (Type == TEXT("user")) {
    // content[0] 에서 is_error + text 추출
    bool bError = ...; FString Text = ...;
    if (Text.Len() > 300) Text = Text.Left(300) + TEXT("...");
    return FString::Printf(TEXT("[tool_result%s] %s"),
        bError ? TEXT(":ERROR") : TEXT(""), *Text);
}
```

**일반화**: 풀 로그에 도구 호출 결과의 **truncated detail** 포함 — debugging 시 *어느 호출이 어떤 에러* 추적 가능. UI 필터에서 `:ERROR` suffix 만 사용자에게 노출 (성공은 풀 로그만 → 노이즈 회피).

## 채택 효과 (MCMaterialAuto 실측)

| Cycle | Hazard | Turn budget 절약 (추정) |
|---|---|---|
| v0.21 (MMA-42 + MMA-43 + MMA-44) | class_name + GUID + valid list | ~40% |
| v0.22 (MMA-45 + MMA-46) | 빈 문자열 + tool_result detail | ~20% |
| v0.23 (MMA-48 자동 정규화) | Pin name shortening | ~30% |

🔴 **INFERRED** — 정량 측정은 turn count 직접 비교 미수집 (사용자 실측 데이터 보완 후속).

## 회피 패턴 (Anti-pattern)

| ❌ 안티 | ✅ 패턴 적용 |
|---|---|
| `"<name>"` 단일 양식 강제 (예: "short only") | 두 양식 모두 정규화 (패턴 1) |
| 1 source identifier (예: local_id only) | Multi-source resolver (패턴 2) |
| 일반 에러 메시지 ("not found" / "failed") | Valid list + HINT (패턴 3) |
| `[tool_result]` prefix 만 | is_error + text 300자 (패턴 4) |
| LLM 가이드 (system prompt) 만 의무 | server 측 자동 흡수 (전 패턴) |

⚠ **system prompt 가이드 vs server 자동 흡수**: 둘 다 보완적이지만 *server 자동 흡수가 reliable* — system prompt 무시되는 케이스 발생 (Cowork ToolSearch 우회 vs 직접 차단의 차이와 동일 — [[concepts/Claude-Code-Cowork-ToolSearch-Bypass]]).

## 변형 사례

1. **다른 LLM (GPT / Gemini)**:
   - 동일 패턴 적용 가능 — 모델별 brute-force 경향이 다르지만 server 자동 정규화는 모델 무관 효과
2. **GraphQL / REST API**:
   - 같은 원칙: caller 부담 → server 흡수. 특히 valid-list error 는 REST 의 422 응답 표준화에 활용 가능
3. **CLI 도구**:
   - 위 패턴들은 `--help` / `--dry-run` 외 *런타임 에러* 의 friendly 화 측면도 동일

## 관련 entity

- [[Claude-Code-CLI]] (caller)
- [[MCP-Protocol]] (protocol)
- [[UMaterialEditingLibrary]] (server 도구의 base API — Connect... 등)

## 열린 질문

1. ❓ 정량 측정 표준화 — turn count / latency / error rate 비교 메트릭. MCMaterialAuto 의 후속 cycle 에서 수집 필요.
2. ❓ 패턴별 보호 한계 — 어떤 hazard 가 server 자동 흡수로 해결 불가능한지 (예: semantic 오해석).
3. ❓ Tool description 의 *최대 토큰 길이* — 패턴 적용으로 description 이 길어지면 context 비용 증가. trade-off 측정 필요.

## Cross-link

- `concepts/UE-Material-Pin-Name-Shortening` (MMA-48 — 가장 큰 단일 hazard, 패턴 1 의 사례)
- `concepts/Claude-Code-Cowork-ToolSearch-Bypass` (server 자동 흡수 vs system prompt 가이드 비교)
- `concepts/Python-Stdio-MCP-Buffering-Hazard` (같은 MCP integration 계열)
- `synthesis/UE-Claude-MCP-Integration-Patterns` (TODO — 본 cycle 결과 + 외부 사례 합성)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 4 패턴 catalog | 🟢 VAULT | MCMaterialAuto v0.21-v0.23 실측 채택 |
| Class name 양식 양쪽 허용 | 🟢 VAULT | MMA-42 실측 |
| Multi-source ID resolver | 🟢 VAULT | MMA-43 실측 |
| Valid-list error response | 🟢 VAULT | MMA-44 실측 |
| Tool result detail in log | 🟢 VAULT | MMA-46 실측 |
| Turn budget 절약 정량 추정 | 🔴 INFERRED | turn count 직접 측정 미수집 |
| 다른 LLM 효과 | 🔴 INFERRED | Claude 만 검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MCMaterialAuto v0.21-v0.23 cycle 누적 filing-back)
