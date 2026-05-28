---
type: concept
title: "Unity Build Include Cascade — UE .cpp 묶음 재배치로 인한 latent header 누락 노출"
aliases: [Unity Build, UBT Unity, Include Cascade, Latent Header Bug, Transitive Include Fragility]
sources:
  - "[[sources/ue-build-skill]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, build, unity-build, ubt, include-policy, header, latent-bug, iwyu, kmcproject]
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# Unity Build Include Cascade

> 본 페이지는 KMCProject 의 MCMaterialAuto v0.13 빌드 회기 (2026-05-21) 의 실측 사례에서 *vault filing-back* 된 일반 UE 5.7.4 지식. 🟢 vault scope: `ue-` 일반 ([[00_meta/08_VaultScopePolicy]]) — KMCProject 외 모든 UE 프로젝트 재사용 가능.

## 1. 정의 (한 줄)

UE 가 빌드 가속을 위해 같은 모듈 안 여러 .cpp 를 `Module.<Mod>.<N>.cpp` 로 묶어 한 번에 컴파일하는 *Unity Build* 패턴 — 묶음 안 *.cpp 순서 변경* 시 *transitive include 사슬이 깨져* 이전에 우연히 통과하던 *latent header 누락 bug* 가 노출되는 현상.

## 2. 자세히

### 2.1. UBT Unity Build 동작

- 같은 모듈의 N 개 .cpp 를 합쳐 `Module.<Mod>.X.cpp` 형식의 *합성 .cpp* 1 개로 컴파일
- 묶음 크기 한도 (default ~64 KB) 안에서 .cpp concatenate
- 묶음 안 *.cpp 순서* 는 파일 시스템 enumeration / alphabetical / 모듈 그래프 등에 따라 결정 — **결정적이지 않음**

| 단계 | 동작 |
|---|---|
| 1 | UBT 가 모듈 안 .cpp 목록 enumerate |
| 2 | 묶음 한도까지 .cpp 합성 → `Module.<Mod>.0.cpp`, `Module.<Mod>.1.cpp`, ... |
| 3 | 각 합성 .cpp 단일 단위로 컴파일 |
| 4 | 묶음 안 *앞 .cpp 의 include* 가 *뒷 .cpp 의 transitive include* 가 됨 |

→ 어떤 .cpp 가 *직접 사용하는 type 의 header* 를 명시 include 하지 않으면 *묶음 안 앞 .cpp 의 include* 에 우연히 의존. 묶음 순서 변경 시 그 의존 깨짐.

### 2.2. 함정 매트릭스

| 증상 | 원인 |
|---|---|
| `C2027 정의되지 않은 형식 'X'` | header 의 *forward declaration* 만 있고 full 정의 누락 — `.method()` 또는 `sizeof(X)` 호출 불가 |
| 신규 .cpp 추가 후 *기존 .cpp* 의 빌드 에러 | Unity Build 묶음 재배치 → transitive cascade 깨짐 |
| 같은 코드가 *clean build* 시 다르게 동작 | 묶음 순서 의존성 — 비결정적 |
| 일부 빌드머신만 fail | 파일 시스템 enumeration 순서 차이 |

### 2.3. 노출 *시점* 의 비결정성

- 정상 빌드: 묶음 안 *앞 .cpp* 가 우연히 `DetailWidgetRow.h` 같은 header include → 뒷 .cpp 가 사용 가능 → 통과
- 신규 .cpp 추가: 그 .cpp 가 앞에 위치 + 다른 header set → 뒷 .cpp 의 transitive 의존 다른 곳에서 와야 함 → 없으면 fail
- 즉 *bug 자체는 항상 존재*, 단지 *Unity Build 의 운* 으로 통과해왔음

## 3. 회피 패턴

### 3.1. 표준 의무 (IWYU — Include What You Use)

> 🚨 **모든 .cpp 는 *직접 사용하는 type 의 header* 를 *명시* include 한다. transitive 의존 *최소화*.**

각 .cpp 의 include 검증 체크리스트:
- 직접 사용 (호출 / instantiate / member 접근 / sizeof) 하는 모든 type → 해당 header 명시 include
- *forward declaration 만 있는 header* 에 의존하지 말고 *full 정의 header* 명시
- 사용 안 하는 header 는 *제거* (over-include 도 빌드 시간 부담)

### 3.2. UE 의 IWYU 옵션

| Build.cs 설정 | 의미 |
|---|---|
| `PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs` | KMCProject 기본 — explicit PCH 또는 공유 PCH 사용. IWYU 친화. |
| `bEnforceIWYU = true` (모듈별) | IWYU 위반 시 *컴파일 에러* 즉시. 단 Unity Build 묶음 우연 통과 가능 |
| `bUseUnity = false` (모듈별) | Unity Build 비활성 — 모든 transitive 즉시 노출. *디버그 빌드* 권장. |

### 3.3. 빌드 검증 방법

신규 module 추가 또는 대규모 refactor 후 의무:
- `Saved/UnusedHeaders.txt` 검사 (UBT 가 IWYU 위반 누적)
- 또는 *해당 모듈만* Unity Build 비활성 후 clean build — 모든 transitive 즉시 노출
- CI 가 있다면 `bUseUnity=false` 빌드를 *주 1 회* 라도 실행

### 3.4. 시점별 의무 매트릭스

| 시점 | 행동 |
|---|---|
| .cpp 작성 시 | 사용하는 모든 type 의 header 명시 include |
| 신규 module / 폴더 추가 시 | 기존 module 의 *clean build* 검증 의무 |
| Unity Build 묶음 재배치 시 (자동) | 첫 빌드에서 latent bug 노출 — 즉시 fix |
| Code review | IWYU 검토 항목 (직접 사용 vs transitive 의존 검증) |

## 4. 변형 / 사례 / 응용

### 4.1. KMCProject MCMaterialAuto v0.13 실측 (2026-05-21) — `mc-` 사례

> *vault scope*: 이 §4.1 은 [[00_meta/08_VaultScopePolicy]] 의 *KMCProject 실측 사례 (case study)*. 일반 패턴 (§2, §3) 의 *검증* 으로 사용.

**증상**: `MCSplineNodeDetails.cpp` 가 C2027 'FDetailWidgetRow' 정의되지 않은 형식 (3 위치: L20, L138, L192). 이전 빌드 (v0.12 이하) 까지는 통과했음.

**진단 흐름**:
1. `IPropertyTypeCustomization.h` (L10) 가 `class FDetailWidgetRow;` *forward declaration* 만 제공
2. `MCSplineNodeDetails.cpp` 의 `_slot_category.AddCustomRow(...)` 호출은 `FDetailWidgetRow` 의 *full 정의* (`DetailWidgetRow.h`) 필요
3. 이전 빌드: Unity Build 묶음 안 *다른 .cpp* (예: `MCMaterialNodeDetails.cpp` — 명시 include 보유) 가 앞에 위치 → transitive 로 `DetailWidgetRow.h` 통과
4. v0.13 신규 파일 (`MCMaterialAutoActiveAsset.h/.cpp`) 추가 → 묶음 재배치 → `MCSplineNodeDetails.cpp` 가 다른 묶음으로 이동 또는 앞 .cpp 의 include set 변경 → transitive 깨짐 → 노출

**Fix**: `MCSplineNodeDetails.cpp` 상단에 명시 include 3 종:
```cpp
#include "DetailWidgetRow.h"        // FDetailWidgetRow full 정의
#include "DetailLayoutBuilder.h"    // IDetailLayoutBuilder
#include "DetailCategoryBuilder.h"  // IDetailCategoryBuilder
```

**검증**: KMCProject `MCEditorModule/DetailView/` 의 다른 6 details 파일은 *이미* 명시 include 보유 — single point of failure 였음.

KMCProject 의 본 사례 상세 (변경 이력 / 빌드 에러 raw / 진단 절차) 는 *vault 외부* 의 `KMCProject/Docs/MCMaterialAuto_Design.md` §변경 이력 v0.13 빌드 fix 에 기록.

### 4.2. 일반화 — 모든 UE 모듈에 적용

같은 패턴이 발현 가능한 후보 함수:
- `FDetailWidgetRow::WholeRowContent()`, `.NameContent()`, `.ValueContent()`
- `IDetailLayoutBuilder::EditCategory()`, `.HideProperty()`
- `IDetailCategoryBuilder::AddCustomRow()`, `.AddProperty()`
- `FOnClicked::CreateSP/Static/Raw`
- 기타 *forward declaration 만 흔한 PropertyEditor / Slate 헤더*

### 4.3. 회피 자동화 후보

- 신규 .cpp 추가 시 *해당 모듈 clean build* CI hook
- pre-commit hook 으로 IWYU 위반 검출

## 5. 관련 entity

- [[entities/UnrealBuildTool]] — UBT 의 Unity Build 결정

## 6. 열린 질문

- [ ] UBT 의 정확한 묶음 algorithm — alphabetical / file mtime / 의존 그래프 우선순위 중 무엇? (🔴 INFERRED — UE 5.7.4 docs 미수록)
- [ ] `Build.cs` 의 `MinFilesUsingPrecompiledHeader` / `bFasterWithoutUnity` / `bEnforceIWYU` 옵션의 Unity Build cascade 영향 정량화
- [ ] PCH (precompiled header) 와 Unity Build 의 상호작용 — 공유 PCH 사용 시 비슷한 cascade 발현 가능성

## 7. Cross-link

- [[concepts/Editor-Only-4-Tier-Separation]] — UE 모듈 분리의 일반 정책 (Build.cs 의무)
- [[sources/ue-build-skill]] — UBT 메인 (Unity Build 의무 정책)
- [[00_meta/08_VaultScopePolicy]] — `ue-` (일반) vs `mc-` (KMCProject 실측 case study) 분류

## 8. Citation Disclosure ([[00_meta/06_VaultCitationRule]])

- 🟢 VAULT: UBT Unity Build 표준 동작 매커니즘 — UE 공식 docs 및 일반 지식 (직접 검증)
- 🟢 VAULT: KMCProject v0.13 사례 — 사용자 빌드 에러 메시지 직접 증거 (C2027 + 파일 위치 + 라인 번호)
- 🟡 PARTIAL: UBT 묶음 algorithm 정확한 우선순위 — 일반 패턴은 vault 근거, 정확한 결정 함수는 §6 열린 질문
- 🔴 INFERRED: `bUseUnity` / `bEnforceIWYU` flag 명의 UE 5.7.4 정확성 — UE 5.x 일반 지식, vault 본 페이지 작성 시점 미직접 검증

## 9. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-21 | 초안 작성 — KMCProject MCMaterialAuto v0.13 빌드 회기 filing-back. §4.1 실측 사례 + §3 회피 패턴 + §6 열린 질문 |
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

UBT 의 unity-cpp 묶음 cascade 는 일반 build system 패턴 — 5.5↔5.7 사이 algorithm 본질 변화 없음. 원래도 일부 🔴 INFERRED (`bUseUnity`/`bEnforceIWYU` flag 정확성) — 그 부분은 5.5.4 에서도 동일하게 미검증 상태로 유지.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
