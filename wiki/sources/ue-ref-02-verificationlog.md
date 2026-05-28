---
type: source
title: "UE refs — 02 VerificationLog (1차 ingest 검증 매트릭스)"
slug: ue-ref-02-verificationlog
source_path: raw/ue-wiki-llm/references/02_VerificationLog.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, verification, ingest, governance]
---

# UE refs — 02 VerificationLog

> Source: [[raw/ue-wiki-llm/references/02_VerificationLog.md]] · vault 1차 개요 단계 검증 로그

## 1. Summary

LLM Wiki 1차 개요 단계에서 **실제 확인된 사실 / 사용 데이터 출처 / 알려진 한계** 정리. 다른 모델·세션이 이어서 작업할 때 본 문서만 읽고 컨텍스트 재구성 가능. [[sources/ue-meta-confidence-tags]] 의 진입점. [[concepts/MC-Asset-Validation-Policy]] 와 페어 (vault 검증 + 코드 검증).

## 2. 환경 검증 매트릭스 (확인됨) 🟢

| 항목 | 값 | 출처 |
| -- | -- | -- |
| 엔진 루트 경로 | `C:\Unreal\UnrealEngine` | 사용자 지정 + 마운트 확인 |
| 분석 대상 트리 | `Engine/Source/Runtime` | 디렉토리 존재 확인 |
| **엔진 버전** | **5.7.4** | `Engine/Build/Build.version` 직접 파싱 |
| BranchName | `UE5` | 동일 파일 |
| Changelist | `0` (IsLicenseeVersion=0, IsPromotedBuild=0) | 동일 파일 |
| Compatible Changelist | `47537391` | 동일 파일 |

```json
// Engine/Build/Build.version (원본)
{ "MajorVersion": 5, "MinorVersion": 7, "PatchVersion": 4, "Changelist": 0,
  "CompatibleChangelist": 47537391, "BranchName": "UE5",
  "IsLicenseeVersion": 0, "IsPromotedBuild": 0 }
```

## 3. 디렉토리 구조 검증 🟢

`Engine/Source/Runtime/` 직속 폴더 수: **189**

| 지표 | 수 | 비고 |
| -- | -- | -- |
| Runtime 폴더 총 수 | **189** | `ls Runtime/` |
| `.Build.cs` 보유 모듈 | **152** | 실제 빌드 단위 |
| 컨테이너 폴더 (Build.cs 없음) | **37** | 하위에 다시 모듈 보유 |

### 3.1. 컨테이너 폴더 전체 (37개)

```
AdpcmAudioDecoder · Advertising · Analytics · Android · Apple
AudioCaptureImplementations · AudioDeviceEnumeration · AudioLink
AudioPlatformSupport · AugmentedReality · BinkAudioDecoder · CUDA
CorePreciseFP · CoreVerseVM · Datasmith · Experimental · IOS
Interchange · Linux · MRMesh · Net · NetworkReplayStreaming
NullInstallBundleManager · Online · OpusAudioDecoder · PacketHandlers
PlatformThirdPartyHelpers · Portal · RadAudioCodec · Solaris
StudioTelemetry · TextureUtilitiesCommon · Toolbox · Unix
VirtualProduction · VorbisAudioDecoder · Windows
```

카탈로그 표 → 의존성 컬럼 `—` + 폴더 컬럼 `컨테이너` 표시.

## 4. 카테고리 분류 매트릭스 (작성자 매핑, 🟡)

| # | 카테고리 | 모듈 수 |
| -- | -- | -- |
| 1 | Foundation | 34 |
| 2 | Engine | 16 |
| 3 | Rendering | 17 |
| 4 | UI/App | 13 |
| 5 | Animation | 9 |
| 6 | Physics | 9 |
| 7 | AI | 5 |
| 8 | Audio | 19 |
| 9 | Networking | 13 |
| 10 | Cinematic | 12 |
| 11 | VR/XR | 4 |
| 12 | VP | 2 |
| 13 | Platform | 8 |
| 14 | DevTools | 10 |
| 15 | Messaging | 5 |
| 16 | Time | 3 |
| 17 | Misc | 10 |
| **합계** | | **189** ✓ |

분류 근거: 폴더명 + `.Build.cs` 의존 + UE5 도메인. 🟡 **자동 검증 X** — 다음 모델이 SKILL.md 작성 시 어색한 분류 재배치 (예: `Datasmith` 현재 Misc, VP 성격 강함).

## 5. 데이터 소스 (다른 모델 재사용 가능) 🟢

| 파일 | 용도 |
| -- | -- |
| `Engine/Build/Build.version` | 엔진 버전 정확도 |
| `LLM_Wiki/catalog/runtime_meta.json` | 189 모듈 메타 — `has_build` / `public_deps[]` / `private_deps[]` / `has_public_dir` / `has_private_dir` |
| `LLM_Wiki/catalog/RuntimeIndex.md` | 카탈로그 (한 줄 요약) |
| `LLM_Wiki/references/01_LayerMap.md` | L1-L7 의존 계층 |

`runtime_meta.json` = `Build.cs` 정규식 파싱 (`PublicDependencyModuleNames` / `PrivateDependencyModuleNames` 의 `new string[]{...}` + `AddRange(...)` 추출). 컨테이너 폴더 = `has_build: false`.

## 6. 알려진 한계 6대 (🟡 / 🔴 — 다음 작업자 검증 의무)

| # | 한계 | 영향 |
| -- | -- | -- |
| 1 | **카테고리 정합성** 17개 = 휴리스틱 | Foundation/Engine 경계 + Audio 컨테이너 + VP/Misc 경계 재검토 |
| 2 | **모듈 한 줄 요약** UE5 일반 지식 | 5.7.4 트리에서 클래스/심볼 직접 확인 의무 |
| 3 | **의존성 파싱 누락 가능성** | 조건부 `if (Target.Type==...) Add` 단일 / `string[]` 외 컬렉션 — 의존성 수 *최저값* 으로 간주 |
| 4 | **버전별 차이** 5.7.4 신규 모듈 (`StateStream` / `MassEntity` / `CoreVerseVM`) | 5.4/5.5 비교 검증 안 함 |
| 5 | **컨테이너 폴더 내부** 37개 하위 모듈 | 컨테이너 단위 별도 스캔 필요 |
| 6 | **Editor/Developer/Programs/Plugins 제외** | 분석 범위 외 — Phase 4-6 에서 Editor 일부 ingest |

## 7. 작업 산출물 (현재까지)

```
C:\Unreal\UnrealEngine\LLM_Wiki\
├── 00_Overview\
│   ├── 00_README.md              위키 진입점, 폴더 구조, Tier
│   ├── 01_LayerMap.md            L1-L7 의존 계층 → vault [[sources/ue-ref-01-layermap]]
│   └── 02_VerificationLog.md     본 문서
├── 01_Catalog\
│   ├── RuntimeIndex.md           189 카탈로그 → vault [[sources/ue-catalog-runtimeindex]]
│   └── runtime_meta.json         의존성 원시 데이터
└── 02_Skills\                    (Phase 1-9 진행 중)
```

## 8. 다음 모델 작업 인계 메모

작업자는 다음 순서로 진행:

1. `references/00_README.md` 의 "Tier 분류" 절 확인
2. **Tier 1** 부터 모듈 선택 → `skills/<Module>/SKILL.md` 작성. 형식:
   - **개요** (역할 / 책임 한 단락)
   - **핵심 헤더 / 클래스** (`Public/` / `Classes/` 실제 헤더 인용)
   - **자주 쓰는 API** (시그니처 + 한 줄 설명)
   - **사용 예제** (5.7.4 트리 안 호출처 인용)
   - **관련 모듈** (`runtime_meta.json` 의존 기반)
3. 사실 인용 = `Engine/Source/Runtime/<Module>/` 직접 Read + 확인
4. 작성 모듈은 `references/00_README.md` "진행 단계" 표 체크

작성 규칙: `references/00_README.md` "작성 원칙" 섹션 (추측 금지, 사실 기반).

## 9. ⭐ 신뢰도 태그 시스템 (vault 측 통합)

| 태그 | 의미 | 출처 |
| -- | -- | -- |
| `[verified]` | UE 5.7.4 트리 grep + 라인 번호 | 로컬 직접 |
| `[grep-listed]` | sub-skill 인용 (직접 grep 안 함) | 위키 카탈로그 |
| `[external-verified]` | docs.unrealengine.com 또는 GitHub URL | 사용자 클릭 검증 가능 |
| `[community]` | 포럼 / Q&A | 약한 검증 |
| `[inferred]` | LLM 추론 | **외부 검증 의무** |

→ [[sources/ue-meta-confidence-tags]] 자세히. vault §13 `00_meta/06_VaultCitationRule` 의 🟢/🟡/🔴 3-tier 와 페어.

## 10. 후속 검증 후보 (Phase 1-9 후)

본 1차 검증 후 9 phase 진행되며 발견된 추가 검증 필요 항목:

- [ ] 5.7.4 vs 5.6 차이 — IsDataValid 시그니처 / FDataValidationContext 도입 시점 (Phase 4 검증 부족)
- [ ] 컨테이너 폴더 37개 하위 모듈 — 일부 vault 카탈로그 (Niagara, Audio 등) 보강 필요
- [ ] Plugin 카테고리 — GAS / Niagara / Significance / GeometryScript / Enhanced Input 등 — 일부만 카테고리화
- [ ] Editor/Developer 카탈로그 (Phase 6+) — [[sources/ue-catalog-editordevindex]] 추가 검증

## 11. Cross-link

- 자매 vault 메타: [[sources/ue-meta-confidence-tags]] · [[sources/ue-meta-corrections]] · [[sources/ue-meta-governance]] · [[sources/ue-meta-honest-limits]] · [[sources/ue-meta-improvement-roadmap]]
- 카탈로그: [[sources/ue-catalog-runtimeindex]] · [[sources/ue-catalog-editordevindex]]
- Layer 구조: [[sources/ue-ref-01-layermap]] (L1-L7) — 본 검증 위에 구축
- Wiki harness: [[sources/ue-ref-03-wikiharness]] (시나리오 라우팅)
- Audit: [[sources/ue-ref-18-modelevolutionaudit]] (분기별 staleness — 본 한계 6대 재검토 hook)
- Governance: [[00_meta/04_AuditPolicy]] · [[00_meta/06_VaultCitationRule]]
