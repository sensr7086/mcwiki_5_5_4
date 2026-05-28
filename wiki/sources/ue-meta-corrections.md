---
type: source
title: "UE meta — corrections (vault 거짓 누적 로그)"
slug: ue-meta-corrections
source_path: raw/ue-wiki-llm/meta/corrections.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-15
tags: [ue, meta, governance, corrections, self-eval-bias, filing-back]
citation_disclosure: "본 카드 = 🟢 vault 직시 (corrections 정정 매트릭스 5건이 vault 내 페이지 진화 + log.md append_log entry 로 모두 검증 가능). raw 원본 slim → vault-side 정밀화 (Cycle 5d 2차)."
---

# UE meta — corrections (vault 거짓 누적 로그)

> Source: [[raw/ue-wiki-llm/meta/corrections.md]]
>
> 보강 2026-05-15 (Cycle 5d 2차) — slim card → 정밀 enrich. raw 의 "사용자 발견 거짓 누적" 의무를 vault Phase 8~10 + Cycle 1~5d 진화 안에서 발견한 정정 5건 매트릭스 + 분기 audit 의 입력 매핑.

## 1. Summary

📋 **사용자 발견 거짓 누적 로그** — vault 의 `[inferred]` / 🔴 INFERRED 항목 중 외부 검증 결과 잘못된 것 수집. 분기별 audit ([[sources/ue-ref-18-modelevolutionaudit]]) 의 입력. Cycle 1~5d 진화 안에서 발견한 정정 5건 + 정정 절차 표준 + Self-eval bias 권위 사례 2건.

## 2. 정정 누적 매트릭스 (2026-05-15 기준)

### 2.1 Cycle 5b 정정 — `ue-editor-toolmenus` §2.4 정정 (2026-05-14) 🟢

**Before** (Phase 4 / Cycle 1):
- 주장 — "AssetEditor 의 Window 메뉴는 ToolMenus 가 관리. `ExtendMenu("AssetEditor.X.MainMenu.Window")` 로 확장 가능"
- tier — 🔴 INFERRED (vault 미확정 — 일반 UE 지식 외삽)

**검증 (KMCProject 2026-05-14)**:
- KMCProject 5 후보 ToolMenus 시도 (`AssetEditor.PersonaEditor.MainMenu.Window` / `AssetEditor.MainMenu.Window` / `LevelEditor.MainMenu.Window` 등) 모두 `IsMenuRegistered=FALSE` 영구
- `FAssetEditorToolkit::InitAssetEditor` L222 `SetAllowWindowMenuBar(true)` 직접 grep — Window 메뉴는 *TabManager 의 자체 시스템*
- ToolMenus 외부 시스템 — `ExtendMenu` 가 영원히 stub

**정정**:
- `ue-editor-toolmenus` §2.4 (관리 매트릭스) — "AssetEditor Window 메뉴 = TabManager 자체 (ToolMenus 외)" 명시
- `ue-editor-toolmenus` §2.9 신규 — TabManager 자체 시스템 + 호스트별 `OnRegisterTabs` delegate 표준
- `ue-editor-personatoolkit` §2.7 신규 — `FPersonaModule::OnRegisterTabs()` delegate 표준
- `ue-editor-asseteditorapi` §11 신규 + 함정 12번 등록

**filing-back**:
- KMCProject `FMCHitBoneCurveEditorMenu` 마이그레이션 완료 (Task #81) — `FWorkflowTabFactory` 자손 + delegate 등록 패턴
- 함정 카탈로그 (uobject §4) — 함정 12 신규 등록 검토 (현재 미등록)

→ **vault 내 페이지 3건 동시 정정** (toolmenus + personatoolkit + asseteditorapi). 가장 큰 단일 정정 사례.

### 2.2 Cycle 5a 정정 — `IsBoneValidInSkeleton` C2440 (2026-05-14) 🟢

**Before** (Phase 4G — UAssetUserData 1차):
- 주장 — "UAssetUserData 자손은 const 메서드에서 `GetOuter` Cast 결과를 비-const 변수에 대입 가능"
- tier — 🟡 PARTIAL (vault 외삽 — const-correctness 규칙 미적용)

**검증 (KMCProject 2026-05-14)**:
- `UMCHitBoneCurveUserData::IsDataValid` line 266 — `USkeleton* Skeleton = OwnerMesh->GetSkeleton();` → MSVC C2440
- 진짜 원인 — `USkeletalMesh::GetSkeleton() const` 의 const 오버로드가 `const USkeleton*` 반환 → const propagation

**정정**:
- `ue-coreuobject-uobject` §2.10 신규 — const propagation 함정 catalog
- `mc-asset-validation-policy` §11 신규 — const-correctness 체크리스트 추가
- `ue-assetclasses-mesh` §3 신규 — `GetSkeleton` const 오버로드 매트릭스
- 함정 카탈로그 (uobject §4) — 함정 7번 신규 등록

### 2.3 Cycle 5c 정정 — `IStructureDetailsView::SetStructureData` 의도 (2026-05-14) 🟢

**Before** (Phase 4G — PropertyEditor 1차):
- 주장 — "`IStructureDetailsView::SetStructureData(NewData)` 만 호출하면 내부 SCurveEditor 가 자동 재생성"
- tier — 🟡 PARTIAL (외삽 — Slate widget lifecycle 외삽)

**검증 (KMCProject 2026-05-14)**:
- KMCProject `SMCHitBoneCurveEditor` — SCurveEditor 자식이 `FRichCurve*` 를 캐시
- `SetStructureData(NewData)` 만 호출 → SCurveEditor 가 *예전 FRichCurve\* 캐시 보유* → TArray reallocation 후 0xFFFFFFFFFFFFFFFF crash

**정정**:
- `ue-editor-propertyeditor` §2.8 신규 — IStructureDetailsView 매번 재생성 + SBox 패턴 명시
- `ue-coreuobject-uobject` §2.11 신규 — FStructOnScope + TArray reallocation 함정
- `synthesis/mc-character-hit-reaction-pipeline` §6 신규 — Hit Curve Pipeline 통합
- 함정 카탈로그 (uobject §4) — 함정 8번 신규 등록

### 2.4 Cycle 5c 정정 — Phase 5 C2059 진짜 원인 (2026-05-14, 사용자 직접 진단) 🟢

**Before** (Cycle 5b 진단):
- vault 1차 진단 — "ToolMenus include path 문제" (잘못)
- vault 2차 진단 — "UCLASS(MinimalAPI) 외부 모듈 막힘" (잘못)
- tier — 🔴 INFERRED (vault 자체 진단 실패)

**검증 (KMCProject 사용자 직접 진단 2026-05-14)**:
- `SMCHitBoneCurveEditor.cpp:847` — `auto* PI = Mesh->PreviewInstance.Get();` → C2059 "구문 오류: 상수"
- 진짜 원인 — `UnrealMathUtility.h` L65 `#define PI (3.1415926535897932f)` 전처리기 치환
- vault 가 2회 잘못된 진단 + 사용자가 root cause 발견

**정정**:
- `ue-coreuobject-uobject` §2.12 신규 — UE 글로벌 매크로 reserved 식별자 매트릭스 (11종)
- §2.12.7 자체 평가 정정 — vault 진단 실패 사례 + 교훈 명시
- 함정 카탈로그 (uobject §4) — 함정 9번 신규 등록 ⭐⭐⭐

→ **vault 자체 진단 실패 = 격리된 self-eval bias 사례**. raw [[sources/ue-meta-honest-limits]] §2 페어.

### 2.5 Cycle 4 → Cycle 5b 사이 — `FPropertyEditorModule::OnRegisterTabs` (2026-05-14) 🟡

**Before** (Phase 4G — PropertyEditor 1차):
- 주장 — "PropertyEditor 모듈도 `OnRegisterTabs` delegate 보유 (Persona 와 유사)"
- tier — 🔴 INFERRED ("일반 패턴 외삽")

**검증 (KMCProject 2026-05-14 Cycle 5b)**:
- `FPropertyEditorModule.h` grep — `OnRegisterTabs` 멤버 부재
- TabManager 자체 시스템은 *각 자산 에디터 host 모듈* (`FPersonaModule` / `FLevelEditorModule` / `FBlueprintEditorModule` / 등) 안에 위치
- PropertyEditor 는 detail view 모듈이라 자체 TabManager 보유 X

**정정**:
- `ue-editor-asseteditorapi` §11.4 — 호스트별 OnRegisterTabs 매트릭스 (현재 검증 완료 Persona / LevelEditor 2건만 🟢, 다른 host 🟡/🔴)
- ⚠ `FBlueprintEditorModule::OnRegisterTabs` — Cycle 5e 후보 (검증 미실시 → 🔴 INFERRED 유지)

→ vault 가 *유추 일반 패턴* 으로 PropertyEditor 도 OnRegisterTabs 있다고 외삽한 것이 잘못. **모든 모듈이 자체 TabManager 보유 X** — 자산 에디터 host 만 보유. Cycle 5e 에서 BlueprintEditor 검증 의무.

### 2.6 Cycle 5d 1차 정정 — `WorkflowOrientedApp` 모듈 가설 (2026-05-15) 🟢

**Before** (Phase 4G — Cycle 5b 시점):
- KMCProject 가설 — "`WorkflowOrientedApp` 은 UnrealEd 외 독립 모듈 — Build.cs 에 추가 필요"
- tier — 🔴 INFERRED (KMCProject 자체 외삽)

**검증 (KMCProject 2026-05-15 MCComboEditor 빌드)**:
- `Build.cs` 에 `"WorkflowOrientedApp"` 추가 → **UBT RulesError** ("Could not find module 'WorkflowOrientedApp'")
- 진짜 위치 — `Engine/Source/Editor/UnrealEd/Public/WorkflowOrientedApp/` (UnrealEd 모듈 안 폴더)
- 정답 — `UnrealEd` 의존성만 추가

**정정**:
- `ue-editor-unrealed-asseteditortoolkit` §2.15 신규 — WorkflowOrientedApp 폴더 vs 모듈 함정 + UnrealEd Public 폴더 매트릭스 6종 + 유사함정 5종

→ **vault 가 KMCProject 의 잘못된 외삽을 catalog 화한 케이스**. 외삽이 vault 페이지로 정착하기 전 grep 검증 의무.

## 3. 정정 절차 표준 (5단)

```text
[Step 1] 사용자 / KMCProject / 외부 발견 거짓 의심
  ↓
[Step 2] Grep / Read 로 UE Engine source 직접 검증
  ├─ 거짓 확인 → Step 3
  └─ 검증 통과 → 정정 불요 (cherry-pick 의심 가능)
  ↓
[Step 3] 영향 페이지 매트릭스 작성
  - 직접 영향 (해당 § 정정)
  - 간접 영향 (cross-link 페어 페이지 § 정정 의무)
  - 함정 카탈로그 영향 (uobject §4 등록 / 강등)
  ↓
[Step 4] 페이지 갱신
  - tier 표시 강등 (🟢 → 🟡/🔴) 또는 정정 명시
  - 정정 부분 신규 § + "Before / After / 검증 / filing-back" 표준 형식
  - `last_updated` 갱신
  ↓
[Step 5] 본 페이지 (corrections.md) + log.md append_log
  - corrections.md §2 신규 entry (정정 # / Before / 검증 / 정정 / filing-back)
  - log.md `op: correction` entry
  - 분기 audit 의 입력 (다음 Q audit 시 검증 의무)
```

## 4. 정정 통계 (2026-05-15 기준)

| 카테고리 | 정정 수 | 대표 |
| -- | -- | -- |
| 🔴 INFERRED → 🟢 VAULT (격상 정정) | 4 | §2.1 ToolMenus / §2.3 IStructureDetailsView / §2.4 PI 매크로 / §2.6 WorkflowOrientedApp |
| 🟡 PARTIAL → 🟢 VAULT (격상 정정) | 2 | §2.2 C2440 / [[sources/ue-coreuobject-uobject]] §2.11.1 (Cycle 5d 2차 SRowEditor 검증) |
| 🔴 INFERRED 유지 (미해결) | 2 | §2.5 BlueprintEditor OnRegisterTabs / `ue-editor-assettools` §2.6.1 FText 2nd call |
| **누적 정정 누적** | **6 (4 격상 + 2 PARTIAL→VAULT)** | **vault 진화 절차의 핵심 검증 trail** |

→ Cycle 5a~5d 까지 vault 가 **6 건의 정정을 누적**. 매 정정은 cross-link 페어 페이지 영향 (예: §2.1 = 3 페이지 동시 정정). 분기 audit 시 정정 패턴 분석 의무.

## 5. ⚠ vault 자체 진단 실패 사례 (Self-eval bias 권위)

상세 = [[sources/ue-meta-honest-limits]] §2.

본 페이지 § 2.4 (PI 매크로) 가 가장 강한 self-eval bias 사례:
- vault 가 2회 잘못된 진단 (ToolMenus include / UCLASS MinimalAPI)
- 둘 다 *그럴듯해 보였지만 잘못*
- 사용자가 root cause (PI 매크로) 발견

**교훈**:
- C2059 "상수" 신호 → **매크로 pollution 가설 *제일 먼저***
- *MinimalAPI* 등 attribute 가설보다 *전처리기 단계 함정* 우선 의심
- 우회로 (symptom fix) vs 진짜 진단 (root cause) 구분 의무

→ vault 평가자도 동일 함정 회피 의무 — [[sources/ue-meta-confidence-tags]] §6 self-eval bias 회피.

## 6. Cross-link

### 페어 (의무 Read)

- [[sources/ue-meta-honest-limits]] §2 — Self-eval bias 사례 2건 권위 (본 §5 의 출처)
- [[sources/ue-meta-confidence-tags]] §4 / §5 — 격상 / 강등 절차 + Cycle 5a~5d 매트릭스
- [[sources/ue-meta-governance]] — 거버넌스 마스터
- [[sources/ue-ref-18-modelevolutionaudit]] — 분기 audit (본 페이지의 출력)

### 정정 권위 페이지

- [[sources/ue-coreuobject-uobject]] §2.10 / §2.11 / §2.12 / §2.11.1 (Cycle 5a/5c/5d 정정)
- [[sources/ue-editor-toolmenus]] §2.4 / §2.9 (Cycle 5b 정정)
- [[sources/ue-editor-propertyeditor]] §2.8 (Cycle 5c 정정)
- [[sources/ue-editor-unrealed-asseteditortoolkit]] §2.15 (Cycle 5d 1차 정정)
- [[sources/ue-editor-asseteditorapi]] §11.4 (Cycle 5b — PropertyEditor OnRegisterTabs 외삽 정정)

### 운영 메타

- [[00_meta/06_VaultCitationRule]] · [[00_meta/04_AuditPolicy]]


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-ref-19-externalsourcesguide]] (inbound=3, suggest_missing_cross_link high confidence)
## 7. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest, slim) |
| **2026-05-15 (Cycle 5d 2차)** | **정밀 enrich** — §2 정정 누적 매트릭스 6건 (Cycle 5a~5d 진화 안 발견 정정) + §3 정정 절차 표준 (5단) + §4 정정 통계 (4 격상 + 2 PARTIAL→VAULT) + §5 vault 자체 진단 실패 권위 (PI 매크로 사례) + §6 Cross-link 5 권위 페이지. raw slim → vault-side 정밀화. 🟢 vault 직시 (모든 정정이 vault 안 페이지 진화 + log.md entry 로 검증 가능). |
