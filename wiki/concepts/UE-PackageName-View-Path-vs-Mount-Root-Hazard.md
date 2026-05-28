---
title: UE PackageName View Path vs Mount Root Hazard
slug: UE-PackageName-View-Path-vs-Mount-Root-Hazard
kind: concept
status: live
confidence: 🟢 VAULT
last_updated: 2026-05-27
audit_5_5_4: pass  # 2026-05-27 Phase 2 engine grep 완료
engine_version: 5.5.4
related_concepts:
  - UE-Phantom-Header-Hallucination-Hazard
  - UE-MetaSpecifier-LongPath-Requirement
  - LLM-Visual-Reference-Hallucination
related_synthesis:
  - mc-datatable-auto-blueprint
  - mc-datatable-auto-build-cycle-postmortem
  - ue-llm-assumption-hazard-family
tags: [packagename, content-browser, view-path, mount-root, fatal-log, llm-hallucination]
sources:
  - "C:/Unreal/UnrealEngine/Engine/Source/Runtime/CoreUObject/Public/Misc/PackageName.h"
  - "C:/Unreal/UnrealEngine/Engine/Source/Runtime/CoreUObject/Private/Misc/PackageName.cpp"
---

# UE PackageName View Path vs Mount Root Hazard

## 한 줄 요약

**콘텐츠 브라우저 view path (`/All/Game/...`) 는 실제 mount root (`/Game/...`) 가 아니다.** `FPackageName::LongPackageNameToFilename` 에 view path 전달 시 mount root 매핑 실패 → `UE_LOG(LogPackageName, Fatal, ...)` → assert break / 에디터 크래시.

## 권위 (🟢 VAULT)

UE 5.7.4 engine source:

```
Source/Runtime/CoreUObject/Public/Misc/PackageName.h:141
  static COREUOBJECT_API bool TryConvertLongPackageNameToFilename(
      const FString& InLongPackageName, FString& OutFilename,
      const FString& InExtension = TEXT(""));

Source/Runtime/CoreUObject/Private/Misc/PackageName.cpp:974
  FString FPackageName::LongPackageNameToFilename(...)
  {
      FString Result;
      if (!TryConvertLongPackageNameToFilename(InLongPackageName, Result, InExtension))
      {
          UE_LOG(LogPackageName, Fatal,
              TEXT("LongPackageNameToFilename failed to convert '%s'. "
                   "Path does not map to any roots."), *InLongPackageName);
      }
      return Result;
  }
```

`UE_LOG ... Fatal` 은 *assert break + process abort* 의무.

## 핵심 매트릭스

| 표현 | 위치 | 실제 의미 |
|---|---|---|
| `/All/` | 콘텐츠 브라우저 *view* prefix | view filter — 모든 mount root 통합 표시. **실제 path 아님**. |
| `/All/Game/Characters/...` | 콘텐츠 브라우저 트리 표시 | view path — 사용자가 보는 표면 |
| `/Game/Characters/...` | 내부 LongPackageName | 실제 mount root — `FPackageName` API 가 이해하는 형식 |
| `/Engine/Maps/...` | 내부 mount root | UE engine content |
| `/Script/<Module>` | 내부 mount root | C++ UObject 코드 |
| `/Plugins/<Plugin>/` | 내부 mount root | 플러그인 content |

→ **`/All/` 은 view filter** 이고 *내부 path 아님*. mount root 는 `/Game/`, `/Engine/`, `/Script/`, `/Plugins/...`.

## 함정 family

### 1. LLM hallucination — view path 그대로 전달

사용자가 콘텐츠 브라우저에서 `/All/Game/Characters/Nana/Meshes` 우클릭 → 경로 복사 / 또는 widget 입력 → LLM 도구 호출 args 에 그대로 사용.

LLM 은 *콘텐츠 브라우저 표시* 가 *실제 path* 라고 가정 — **spec 이해 오류**. [[concepts/LLM-Visual-Reference-Hallucination]] 의 path 변종.

### 2. Fatal log — assert / 크래시

`LongPackageNameToFilename` 가 mount root 매핑 실패 시 `UE_LOG Fatal` → debugger 안에서 break / shipping 빌드에서 fatal error dialog + 크래시.

Materialauto / DataTableAuto 같은 LLM-driven 도구에서 *입력 검증 안 하면* 매번 위험.

### 3. CreatePackage / FindObject — 별도 동작

`CreatePackage` 와 `FindObject` 도 invalid path 에 대해 *각자 다른 fail mode*. `/All/...` 에 대해 nullptr 반환 / 빈 package 생성 등 — *fatal 던지지 않더라도 silently 잘못된 결과* 가능.

→ **모든 path 입력은 진입점에서 정규화 의무**.

## 회피 패턴 (🟢 VAULT — MCDataTableAuto 검증)

### 1. 정규화 헬퍼

```cpp
FString NormalizedPkgPath = PkgPath;
NormalizedPkgPath.ReplaceInline(TEXT("\\"), TEXT("/"));
while (NormalizedPkgPath.EndsWith(TEXT("/")))
{
    NormalizedPkgPath.LeftChopInline(1, EAllowShrinking::No);
}

// `/All/Game/...` → `/Game/...` (콘텐츠 브라우저 view path 호환)
if (NormalizedPkgPath.StartsWith(TEXT("/All/")))
{
    NormalizedPkgPath.RemoveFromStart(TEXT("/All"));
}
else if (NormalizedPkgPath.Equals(TEXT("/All")))
{
    NormalizedPkgPath = TEXT("/Game");
}

// 시작 / 보장
if (!NormalizedPkgPath.StartsWith(TEXT("/")))
{
    NormalizedPkgPath = FString::Printf(TEXT("/%s"), *NormalizedPkgPath);
}
```

### 2. fatal 회피 API 사용

```cpp
// ❌ fatal 던짐
FString File = FPackageName::LongPackageNameToFilename(Pkg, Ext);

// ✅ return bool, no fatal
FString File;
const bool bOk = FPackageName::TryConvertLongPackageNameToFilename(Pkg, File, Ext);
if (!bOk || File.IsEmpty()) {
    // 명확한 에러 응답 + HINT (`/Game/...` 형식 사용)
}
```

### 3. LLM-friendly tool schema

도구 description 에 명시:
```
"pkg_path: '/Game/<sub>' 형식 (콘텐츠 브라우저 view 의 '/All/' prefix 자동 strip 됨)."
```

→ [[concepts/MCP-Tool-Schema-LLM-Friendly-Design]] 4 패턴 §1 (식별자 양식 양쪽 허용) 의 path 변종.

## MCDataTableAuto 적용 사례

- Phase 3c-3 후속 (2026-05-26) — VS 디버거 break 진단.
- McpServer create_datatable / fill_rows 두 도구 모두 적용.
- pkg_path = `/All/Game/Characters/Nana/Meshes` 실측 → 정규화 후 `/Game/Characters/Nana/Meshes` → SavePackage 정상.

## 변경 이력

- **2026-05-26** — 신규 작성. MCDataTableAuto Phase 3c-3 후속 cycle 에서 사용자 VS 디버거 break 직접 trigger → 정식화.
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `TryConvertLongPackageNameToFilename` 선언: 5.5.4 와 5.7.4 **모두 `PackageName.h:141`** (라인 shift 없음!)
- 양 버전 동일 시그니처 2개 오버로드 (FString / FStringView 버전)
- 파일 전체 라인: 5.5.4 = 981 / 5.7.4 = 1052 (다른 부분에서만 71 라인 추가)
- **결정**: 🟢 본 페이지의 `PackageName.h:141` 인용 5.5.4 에서도 정확. 동작 stable.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
