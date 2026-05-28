---
type: source
title: "UE refs — 19 ExternalSourcesGuide (외부 source 신뢰성)"
slug: ue-ref-19-externalsourcesguide
source_path: raw/ue-wiki-llm/references/19_ExternalSourcesGuide.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, external-sources, confidence-tags]
---

# UE refs — 19 ExternalSourcesGuide

> Source: [[raw/ue-wiki-llm/references/19_ExternalSourcesGuide.md]] · 위키 sub-skill 부재 시 *검증 가능한 외부 source 추적* 표준

## 1. Summary

위키 sub-skill 에 없는 항목을 **inferred 로 답하지 말고 검증 가능한 외부 source 로 보강**. UE 공식 문서 → Engine grep → docs.unrealengine.com → Epic GitHub → Epic 포럼 → LLM 추론 6 단계 우선순위. 모든 wiki 액션 커맨드 (`/wiki-explain` / `/wiki-lookup` / `/wiki-example` / `/wiki-debug` / `/wiki-perf` / `/wiki-migrate`) 의 "위키에 없음" fallback. CLAUDE.md §0.1.3 정책. [[sources/ue-meta-confidence-tags]] / [[sources/ue-meta-corrections]] 페어.

## 2. 우선순위 6 단 (의무) 🟢

```
1순위 — 위키 sub-skill (`skills/<...>/SKILL.md`)        [verified]/[grep-listed]
2순위 — UE 5.7.4 트리 grep (`Engine/Source/...`)          [verified]
3순위 — 공식 docs.unrealengine.com                        [external-verified]
4순위 — Epic GitHub `EpicGames/UnrealEngine`              [external-verified, 액세스 권한]
5순위 — Epic 개발자 포럼 / Q&A (forums.unrealengine.com)   [community, 검증 약함]
6순위 — LLM 추론 (마지막 수단)                              [inferred] — 사용자 검증 의무
```

🚨 **3~5순위로 답한 항목은 모두 사용자에게 외부 출처 링크 + "외부 검증 의무" 명시**.

## 3. docs.unrealengine.com 검색 패턴 (3순위) 🟢

### 3.1. 표준 URL

```
https://docs.unrealengine.com/5.7/en-US/?application_version=5.7
```

한국어 — `/ko/` 경로. 자동 번역 품질 변동 → **영문 우선 권장**.

### 3.2. 검색 패턴 매트릭스

| 검색어 형태 | 예 | 의도 |
| -- | -- | -- |
| `<UClass>` | `UAnimInstance` | 클래스 레퍼런스 |
| `<UClass>::<함수>` | `UAnimInstance::NativeUpdateAnimation` | 메서드 |
| `<시스템> overview` | `Behavior Tree overview` | 개요 |
| `<시스템> setup` | `Enhanced Input setup` | 셋업 가이드 |
| `<용어> reference` | `MetaSound reference` | API 레퍼런스 |
| `release notes` | `5.7 release notes` | 버전 변경 |

### 3.3. 페이지 종류 신뢰도

| 종류 | 신뢰도 | 사용 |
| -- | -- | -- |
| C++ API Reference | 높음 | 시그니처 / 멤버 |
| Blueprint API Reference | 높음 | BP 노드 |
| Programming Guide | 중간 | 패턴 / 예제 (버전 차이 주의) |
| Setting Up Your Project | 중간 | 셋업 |
| Release Notes | 높음 | 5.x 변경점 |
| Sample Projects | 낮음 (오래됨) | 예제 |

🚨 **버전 셀렉터** — 좌측 상단 `5.7` 명시. 4.27 / 5.0 등 잘못된 버전 답변 위험.

### 3.4. 인용 형식

```
- 📚 docs.unrealengine.com/5.7 — `UAnimInstance` Reference [external-verified]
  https://docs.unrealengine.com/5.7/en-US/API/Runtime/Engine/Animation/UAnimInstance/
```

## 4. GitHub EpicGames/UnrealEngine 검색 (4순위) 🟢

> 🔒 **액세스 권한 필요** — Epic 계정 + GitHub 연결 + EULA 동의.

### 4.1. 표준 검색

| 패턴 | 예 | 의도 |
| -- | -- | -- |
| `org:EpicGames repo:UnrealEngine "<symbol>"` | `class UAnimInstance` | 정의 위치 |
| 파일 검색 — `<filename>` | `AnimInstance.h` | 헤더 직접 |
| 라인 인용 — Permalink | `blob/<commit>/Engine/Source/...#L123` | 라인 고정 |

### 4.2. 5.7.4 태그 / 브랜치

```
브랜치 — release / 5.7
태그 — 5.7.4-release (해당 시)
```

🚨 main 브랜치 = 5.8+ 가능성 → 5.7.4 와 다를 수 있음. 항상 `release` 또는 `5.7` 브랜치 명시.

### 4.3. 인용 형식

```
- 🔍 GitHub UE 5.7 — `Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h:NNN` [external-verified]
  https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h#LNNN
```

## 5. 로컬 UE 5.7.4 트리 grep (2순위) 🟢

### 5.1. 표준 경로

```
C:\Unreal\UnrealEngine\Engine\Source\Runtime\<Module>\
C:\Unreal\UnrealEngine\Engine\Source\Editor\<Module>\
C:\Unreal\UnrealEngine\Engine\Source\Developer\<Module>\
C:\Unreal\UnrealEngine\Engine\Plugins\<Plugin>\Source\
```

❌ `Engine/Source/Programs/` 는 **분석 제외** (UnrealHeaderTool / UnrealBuildTool 빌드 도구).

### 5.2. grep 명령 패턴

```bash
# 클래스 정의
grep -rn "class UAnimInstance" Runtime/Engine/Public/Animation/

# UFUNCTION 노출
grep -rn "UFUNCTION(BlueprintCallable, Category=\"Animation\"" Runtime/Engine/

# 매크로 정의
grep -rn "#define DOREPLIFETIME_CONDITION" Runtime/Engine/
```

### 5.3. 인용 형식 (`[verified]` 의무)

```
- 🔍 Local UE 5.7.4 — `Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h:NNN` [verified]
```

## 6. Epic 개발자 포럼 / Q&A (5순위) 🟡

### 6.1. 도메인

| 사이트 | 용도 |
| -- | -- |
| `forums.unrealengine.com` | 일반 토론 + Q&A 통합 (구 AnswerHub) |
| `dev.epicgames.com/community` | Q&A 새 도메인 |

### 6.2. 신뢰도 — 낮음 ~ 중간

- 답변 작성자 Epic 직원 여부 확인 (Epic Verified 배지)
- 5.x 태그 매칭 의무 (5.0 / 5.1 / ... / 5.7)
- **5년 이상 오래된 답변 = 신뢰도 매우 낮음** (deprecated 가능)

### 6.3. 인용 형식

```
- 💬 Epic Forum — "Behavior Tree Decorator FlowAbort" [community]
  https://forums.unrealengine.com/t/...
  ⚠ 검증 약함 — 외부 검증 의무
```

## 7. ⭐ 외부 보강 워크플로우 (모든 wiki-* 표준) 🟢

```
[사용자 질의 도착]
       ↓
[Step 1] 위키 sub-skill 매칭 — 03_WikiHarness.md 라우팅
       ├─ Hit → [verified]/[grep-listed] 답변
       └─ Miss → ↓
[Step 2] UE 5.7.4 로컬 트리 grep
       ├─ Hit → [verified] 답변 + 라인 번호
       └─ Miss → ↓
[Step 3] docs.unrealengine.com 5.7 검색
       ├─ Hit → [external-verified] + URL + 사용자 검증 권고
       └─ Miss → ↓
[Step 4] GitHub UE 5.7 release 브랜치 (액세스 시)
       ├─ Hit → [external-verified] + Permalink
       └─ Miss → ↓
[Step 5] Epic 포럼 / Q&A (5.x 태그)
       ├─ Hit → [community] + URL + ⚠ 약한 검증 경고
       └─ Miss → ↓
[Step 6] LLM 추론 — [inferred] + "외부 검증 의무" 명시 + corrections.md 누적 안내
```

## 8. 신뢰도 태그 매핑 🟢

| 태그 | 출처 | 검증 방법 |
| -- | -- | -- |
| `[verified]` | UE 5.7.4 트리 grep + 라인 번호 | 로컬 직접 |
| `[grep-listed]` | sub-skill 인용 (직접 grep 안 함) | 위키 카탈로그 |
| `[external-verified]` | docs / GitHub URL | 사용자 클릭 검증 가능 |
| `[community]` | 포럼 / Q&A | 약한 검증 |
| `[inferred]` | LLM 추론 | **외부 검증 의무** |

→ [[sources/ue-meta-confidence-tags]] 자세히. vault §13 `00_meta/06_VaultCitationRule` 의 🟢/🟡/🔴 3-tier 와 페어.

## 9. ⭐ 거짓 발견 시 의무 🟢

1. **[[sources/ue-meta-corrections]]** 에 누적 — 누가 / 언제 / 어디서 / 무엇이 거짓
2. 해당 sub-skill 에 `<!-- corrected YYYY-MM-DD -->` 주석 + 수정
3. 신뢰도 태그 강등 — `[verified]` → `[inferred]` 임시 + 재검증
4. [[sources/ue-ref-18-modelevolutionaudit]] 분기 감사 시 일괄 검토

## 10. 사용 예 (위키 액션 커맨드)

### `/wiki-lookup UStateTreeComponent` 응답 예시

```
# UStateTreeComponent

⚠ 위키 sub-skill 에 없음. StateTree (5.x 신규 — Plugin) 는 위키에 다루어지지 않습니다.

## 외부 검증 출처
- 📚 docs.unrealengine.com/5.7 — StateTree Overview [external-verified]
  https://docs.unrealengine.com/5.7/en-US/state-tree-in-unreal-engine/

- 🔍 GitHub UE 5.7 — `Engine/Plugins/Runtime/StateTree/` [external-verified]
  https://github.com/EpicGames/UnrealEngine/tree/release/Engine/Plugins/Runtime/StateTree

- 💬 Epic Forum — "StateTree vs Behavior Tree" 5.x [community] ⚠ 검증 약함

## 사용자 다음 단계
1. 위 URL 1개 이상 직접 확인
2. 사용 시도 후 거짓 발견 시 corrections.md 누적
3. 위키에 추가 가치 → ue-wiki-maintainer 에이전트로 신규 sub-skill 작성 가능
```

## 11. 안티패턴 (5대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | `[inferred]` 태그 없이 추론 답변 | 6단 우선순위 의무 — 마지막 LLM 추론 시 `[inferred]` 명시 |
| 2 | 4.27 / 5.0 docs URL 답변 (구버전) | `5.7` 버전 셀렉터 의무 |
| 3 | GitHub main 브랜치 인용 | `release` / `5.7` 브랜치 명시 |
| 4 | 5년 이상 오래된 포럼 답변 인용 | 5.x 태그 + 작성 시점 검증 |
| 5 | 거짓 발견 후 corrections.md 누적 X | §9 의무 — 누적 + 재검증 |

## 12. Cross-link

- 자매 vault meta: [[sources/ue-meta-confidence-tags]] (태그 정의) · [[sources/ue-meta-corrections]] (거짓 정정 누적) · [[sources/ue-meta-honest-limits]] (LLM 한계)
- 검증 베이스: [[sources/ue-ref-02-verificationlog]] (1차 검증 + 신뢰도 태그)
- Audit hook: [[sources/ue-ref-18-modelevolutionaudit]] (분기별 외부 source 신선도 검토)
- Wiki harness: [[sources/ue-ref-03-wikiharness]] (시나리오 라우팅 — 본 페이지가 "위키에 없음" fallback)
- vault Governance: [[00_meta/06_VaultCitationRule]] (§13 3-tier 마커)
