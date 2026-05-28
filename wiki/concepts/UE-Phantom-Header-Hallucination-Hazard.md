---
title: "UE Phantom Header Hallucination Hazard — 존재한 적 없는 헤더를 include 하는 함정"
kind: concept
status: stable
severity: "★★"
tags: [ue, build, headers, hallucination, llm, ai-paste, legacy-code, kmcproject, ue-574]
related_concepts:
  - "[[concepts/LLM-Visual-Reference-Hallucination]]"
  - "[[concepts/UE-NameHiding-Override-Hazard]]"
related_entities:
  - "[[entities/UObject]]"
related_synthesis:
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
created: 2026-05-25
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# UE Phantom Header Hallucination Hazard — 존재한 적 없는 헤더를 include 하는 함정

> **유래**: KMCProject Phase 1a 빌드 중 발견 (2026-05-25). `MCDataBase.h:31` + `MCTableManager.h:25` 의 `#include "Templates/IsDerivedFrom.h"` — UE 5.7.4 Engine 본가에 *그 이름의 파일 0건*. 사용자 (sensr7086@naver.com) 가 직접 정정 요구 → 출처 추적으로 phantom 확정.

## 정의

UE 코드의 `#include` 가 **Engine 권위 source 에 존재한 적 없는 헤더 경로** 를 가리키는 함정. 보통 외부 source (AI assistant / 옛 forum post / 다른 프로젝트 paste / IDE 자동완성) 의 잘못된 추정이 그대로 사용자 코드에 들어옴.

특징:
- 헤더 *이름* 자체가 plausible — 표기 규칙 ([Templates/...], [UObject/...]) 따름
- 안의 *심볼* 은 다른 헤더에 실존 → 사용자 코드가 그 심볼을 정상 사용 → 외관상 정상 코드
- 빌드 통과 가능성 — PCH 가 *실제 헤더* (예: UnrealTypeTraits.h) 를 transitively include 하면 phantom include 가 *noop* 으로 동작
- 새 source directory 추가 / non-unity 빌드 / incremental cache miss 시 *드러남* → fatal error C1083 ("No such file or directory")

## 자세히

### 사례 — `Templates/IsDerivedFrom.h` (KMCProject Phase 1a, 2026-05-25)

🟢 **VAULT** — Engine 5.7.4 grep 으로 확정.

**증상**:
```
MCPlayModule/MCGame/MCDataBase.h(31): fatal error C1083:
'Templates/IsDerivedFrom.h': No such file or directory

MCPlayModule/MCGame/MCTableManager.h(25): fatal error C1083:
'Templates/IsDerivedFrom.h': No such file or directory
```

발견 흐름:
1. KMCProject 에 새 sub-folder `MCDataTableAuto/` 추가 → UBT makefile 무효화 → 전체 재컴파일
2. non-unity / PCH 우회 path 에서 phantom include 노출 → C1083

**Engine 5.7.4 권위 검증**:
```
Glob C:/Unreal/UnrealEngine/Engine/Source/**/IsDerivedFrom.h
  → No files found

Grep "Templates/IsDerivedFrom\.h" C:\Unreal\UnrealEngine\Engine\Source
  → No files found (어떤 Engine 파일도 그 include 사용 안 함)

Read C:\Unreal\UnrealEngine\Engine\Source\Runtime\Core\Public\Templates\UnrealTypeTraits.h
  → L37-60 에 TIsDerivedFrom 자체 정의 (외부 헤더 없음)
```

→ `Templates/IsDerivedFrom.h` 는 **UE 5.7.4 권위 source 에 존재한 적 없는 phantom 헤더**.

**진짜 권위 위치**:
- `Templates/UnrealTypeTraits.h:37-60` 안 `TIsDerivedFrom` 자체 정의
- 멤버 alias: `::Value` (L57) / `::IsDerived` (L59) 둘 다 valid
- Engine 본가 사용 통계: `::Value` 18건 / `::IsDerived` 9건

**Fix**:
```cpp
// before — phantom
#include "Templates/IsDerivedFrom.h"

// after — Engine 권위
#include "Templates/UnrealTypeTraits.h"
```

코드 사용처 (`TIsDerivedFrom<T, B>::Value`) 그대로. include path 만 교체.

### 빌드가 어떻게 통과했었나 (가설)

🔴 INFERRED — KMCProject 가 이전 빌드 어느 시점에 통과했다면:

1. **PCH transitive include** — Unity build 의 PCH 가 `UnrealTypeTraits.h` 를 끌어와서, *.cpp 안 phantom include 가 검사되기 전에* 심볼이 이미 사용 가능. phantom include 의 파일 검사가 *우회*.
2. **Unity build chunk merging** — 같은 chunk 안 다른 .cpp 가 *실제* 헤더 include → 컴파일러가 chunk 단위로 처리 시 phantom 못 봄.
3. **Incremental build cache** — 옛 빌드 산출물이 캐시돼 재컴파일 안 됨. *새 source directory 추가* 가 cache miss 트리거.

본 cycle 발견 — Phase 1a 의 `MCDataTableAuto/` sub-folder 추가가 위 3 경로 모두 깨뜨림.

## phantom 헤더의 가능 출처 (모두 🔴 INFERRED)

1. **AI assistant hallucination** — LLM 이 "TIsDerivedFrom 의 include path 가 뭐냐" 질문에 plausible 추측. [[concepts/LLM-Visual-Reference-Hallucination]] 의 *text 변종* — UE 컨벤션 `Templates/<TypeName>.h` 학습 prior 가 추측 압도.
2. **Forum / Stack Overflow paste** — 옛 답변이 잘못된 헤더 추정. 사용자 paste.
3. **UE 4.x 잔재** — UE 4.x 어느 시점에 *잠시 존재했을 가능성* (미검증). 5.x migration 시 변경 누락.
4. **IDE 자동완성 잘못 추천** — Visual Studio / Rider 의 fuzzy match.

KMCProject 의 정확한 출처 — 사용자 본인도 미확정 (2026-05-25 대화).

## 회피 패턴 (Layer 4 Defense — vault [[synthesis/ue-llm-assumption-hazard-family]] 변종)

### Layer 1 — include 작성 시 Engine grep 의무

새 include 추가 / 옛 코드 paste 시 **반드시** Engine source grep:

```
Glob C:/Unreal/UnrealEngine/Engine/Source/**/<HeaderName>.h
Grep "#include.*<HeaderPath>" C:\Unreal\UnrealEngine\Engine\Source --files-with-matches
```

둘 다 0건이면 phantom 가능성. Engine 본가의 *어떤 .cpp 도 그 include 안 쓴다면* 그 헤더는 실존 안 함.

### Layer 2 — non-unity 빌드 의무 검증

CI / 정기 점검에서 `bUseUnityBuild = false` (또는 `-noubt`) 로 빌드 — phantom include 즉시 노출.

### Layer 3 — UHT/UBT 전체 재실행 정기 트리거

PCH cache + Unity chunk 의존이 phantom 을 *숨김*. 정기적으로:
- `clean rebuild`
- 새 dummy source 추가 → makefile invalidation
- `-disableunity` 빌드

→ latent phantom 드러남.

### Layer 4 — AI 작성 코드 review 시 include 전수 검증

Cursor / Copilot / Claude 가 작성한 코드의 *모든 include* 가 *Engine 본가 grep 으로 실존 확인된 것* 인지 검증. 가능성 prior 의 *외관 plausibility* 만 보면 안 됨.

## 함정 패밀리 (확장 후보)

phantom symbol 의 다른 변종:

| 변종 | 예 |
|---|---|
| Phantom header | `Templates/IsDerivedFrom.h` (본 사례) |
| Phantom class | `UAssetEditorSubsystemBase` 같은 존재 안 하는 base |
| Phantom function | `GetDataTableRowAsStruct` 같은 plausible 이름 |
| Phantom macro | `UE_DEPRECATED_FUNCTION` 같은 변형 |
| Phantom delegate | `OnAssetEditorClosing` 같은 (실제는 `OnAssetEditorRequestClose`) |

모두 같은 메커니즘 — LLM/도구 prior 의 plausible 추측 → 외관 정상 → 빌드 PCH cover → 새 cycle 노출.

## 관련

- [[concepts/LLM-Visual-Reference-Hallucination]] (image 추측 — 본 concept 의 image 변종)
- [[synthesis/ue-llm-assumption-hazard-family]] (LLM 추측 hazard 통합)
- [[00_meta/06_VaultCitationRule]] (🟢/🟡/🔴 분리 — phantom 을 사실처럼 단정 금지)

## 열린 질문

1. ❓ UE 4.x 어느 버전에 `Templates/IsDerivedFrom.h` 가 실존했는지 — 미확정 (그 시기 source 미접근).
2. ❓ KMCProject 의 phantom include 작성 정확 시점 / 출처 (AI / paste / 자동완성) — 사용자 본인도 미기억.
3. ❓ KMCProject 의 다른 phantom include 가능성 — Source/ 전체 systematic grep 미수행.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `Templates/IsDerivedFrom.h` 가 UE 5.7.4 권위 source 에 존재 안 함 | 🟢 VAULT | Engine source grep (Glob 0 + Grep 0) |
| TIsDerivedFrom 권위 위치 `UnrealTypeTraits.h:37-60` | 🟢 VAULT | 직접 Read 검증 |
| 멤버 ::Value / ::IsDerived 사용 통계 | 🟢 VAULT | Engine 본가 grep (18 / 9) |
| KMCProject 외 다른 사용처 | 🟢 VAULT | KMCProject Source grep 0건 / vault wiki+raw grep 0건 |
| 빌드 통과 메커니즘 (PCH transitive / Unity / cache) | 🟡 PARTIAL | UE Unity build 일반 동작 + KMCProject 실측 종합 |
| UE 4.x 시기 실존 가능성 | 🔴 INFERRED | 미검증 |
| phantom 출처 (AI / paste / IDE) | 🔴 INFERRED | 진짜 미확정 |

## 변경 이력

- 2026-05-25: 초안 작성. KMCProject Phase 1a 빌드 cycle 의 직접 발견 + 사용자 정정 요구 + 3축 grep 으로 phantom 확정. [[concepts/LLM-Visual-Reference-Hallucination]] family 확장.
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

⭐ 가장 강력한 검증: `TIsDerivedFrom` 키워드가 두 raw 모두에서 0 hit — 5.7.4 와 5.5.4 사이 `Templates/IsDerivedFrom.h` 가 *지속적으로 부재* 확정. Phantom 결론은 minor version 통과 안정.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
