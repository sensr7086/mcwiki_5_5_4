---
type: concept
title: "UE HttpServer Body NullTerm Hazard — TArray<uint8> Body 가 null-terminated 보장 안 됨"
aliases: [FHttpServerRequest Body, UTF8_TO_TCHAR Null-Term, HTTP JSON Parse Fail]
sources:
  - "[[sources/ue-build-skill]]"
related_concepts: []
tags: [ue, http, httpserver, fstring, utf8, hazard, kmcproject]
last_updated: 2026-05-27
audit_5_5_4: pass  # 2026-05-27 Phase 2 engine grep 완료
---

# UE HttpServer Body NullTerm Hazard

> KMCProject MCMaterialAuto v0.14.8 회기 (2026-05-22) 의 *vault filing-back*. 🟢 vault scope: `ue-` 일반 — 모든 UE HttpServer 사용자에 적용.

## 1. 정의 (한 줄)

UE `FHttpServerRequest::Body` 가 `TArray<uint8>` 라 *null-terminated 보장 X*. `FString(UTF8_TO_TCHAR(Req.Body.GetData()))` 가 *null terminator 까지* 읽어 byte 길이 부정확 — 일부 request 는 우연히 null 없어 통과, 다른 request 는 buffer cutoff 로 JSON parse fail.

## 2. 자세히

### 2.1. 메커니즘

```cpp
// ⚠ 위험 패턴 — null-terminated 가정
const FString Body = FString(UTF8_TO_TCHAR(reinterpret_cast<const ANSICHAR*>(Req.Body.GetData())));
```

| 단계 | 동작 |
|---|---|
| 1 | `Req.Body` = `TArray<uint8>` — UE Core 표준, **null-terminated 보장 X** |
| 2 | `GetData()` = raw `uint8*` pointer |
| 3 | `UTF8_TO_TCHAR(ptr)` 매크로 = *null terminator 만날 때까지* 변환 |
| 4 | `FString(TCHAR*)` constructor = 변환된 TCHAR 길이만큼 복사 |
| 5 | **Body buffer 끝에 우연한 0 바이트** 또는 **buffer 끝 garbage** → JSON 일부 cutoff |

### 2.2. 비결정성 (KMCProject 실측)

mcp_proxy_rpc.log v0.14.7:
```
[21:50:13] add_expression: forward done — resp_size=189   ✅ 정상 응답 (우연 통과)
[21:50:15] connect_to_material_property: resp_size=21    🚨 21 bytes!
```

→ 21 bytes = `{"error":"bad json"}` (HandleRpcRequest 의 parse fail fallback). 같은 server, 같은 transport, 다른 payload 가 *우연한 null 위치* 에 따라 결과 다름.

## 3. 회피 패턴

### 3.1. 명시 null terminator 추가 (의무)

```cpp
const TArray<uint8>& BodyBytes = Req.Body;
TArray<ANSICHAR> NullTerminated;
NullTerminated.Reserve(BodyBytes.Num() + 1);
NullTerminated.Append(reinterpret_cast<const ANSICHAR*>(BodyBytes.GetData()), BodyBytes.Num());
NullTerminated.Add('\0');   // ⭐ 명시 null terminator
const FString Body = FString(UTF8_TO_TCHAR(NullTerminated.GetData()));
```

### 3.2. 진단 로그 추가

parse 실패 시 *body 첫 500 bytes + 전체 byte 수* 로깅 — null terminator 누락 vs JSON 문법 오류 구분 가능.

```cpp
if (!FJsonSerializer::Deserialize(Reader, Json) || !Json.IsValid())
{
    UE_LOG(LogYourMod, Warning, TEXT("bad json (%d bytes): %s"), BodyBytes.Num(), *Body.Left(500));
    // ... error response
}
```

## 4. 변형 / 사례 / 응용

### 4.1. KMCProject MCMaterialAuto v0.14.8 (`mc-`)

UE-MCP HTTP server 의 HandleRpcRequest. proxy.py 가 정상 forward 했음에도 *connect_to_material_property* request 에서 *bad json* 21 bytes 응답. v0.14.8 fix 후 모든 payload 정상.

자세히 — KMCProject Docs/MCMaterialAuto_Design.md §변경 이력 v0.14.8.

### 4.2. 일반 적용

같은 패턴이 발현 가능한 다른 사례:
- UE 의 WebSocket / WebHook server 모듈
- `IHttpResponse::GetContent()` 처리
- 외부 process spawn 의 stdout pipe 받기

→ **임의 byte buffer 를 FString 으로 변환할 때 *항상 명시 null terminator + 길이*** 의무.

## 5. 관련 entity

- (없음 — Core 레벨 함정)

## 6. 열린 질문

- [ ] UE 5.7.4 의 `FString::ConstructFromPtrSize` 또는 비슷한 *length-aware* API 존재 여부
- [ ] `FUTF8ToTCHAR` converter 의 *명시 length* constructor 시그니처

## 7. Cross-link

- [[concepts/Editor-Only-4-Tier-Separation]] — UE 일반 build 정책
- [[sources/ue-build-skill]] — UBT 메인
- [[00_meta/06_VaultCitationRule]] — 3-tier citation 의무

## 8. Citation Disclosure ([[00_meta/06_VaultCitationRule]])

- 🟢 VAULT: `TArray<uint8>` 가 null-terminated 보장 안 함 — UE Core 표준
- 🟢 VAULT: `UTF8_TO_TCHAR` 가 null-terminated 가정 — UE 표준 매크로
- 🟢 VAULT: KMCProject v0.14.8 사례 — mcp_proxy_rpc.log 의 resp_size=21 직접 증거
- 🟡 PARTIAL: `FString::ConstructFromPtrSize` UE 5.7.4 정확한 시그니처 — 후속 검증

## 9. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-22 | 초안 작성 — KMCProject MCMaterialAuto v0.14.8 filing-back |
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `FString::ConstructFromPtrSize` 존재 양 버전:
  - 5.5.4: `UnrealString.h.inl:124` — `static CORE_API UE_STRING_CLASS ConstructFromPtrSize(const ANSICHAR* Str, int32 Size);`
  - 5.7.4: `UnrealString.h.inl:131` — `[[nodiscard]] static CORE_API UE_STRING_CLASS ConstructFromPtrSize(const ANSICHAR* Str, int32 Size);`
- 5.4 부터 도입 (deprecated 메시지에 명시: `UE_STRING_DEPRECATED(5.4, "use ConstructFromPtrSize")`)
- 시그니처 동일 (5.7.4 만 `[[nodiscard]]` attribute 추가 — semantic 영향 없음)
- **결정**: 🟢 length-aware API 5.5.4 에서 존재 + 동일 동작. 본 페이지의 hazard 결론 유효.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
