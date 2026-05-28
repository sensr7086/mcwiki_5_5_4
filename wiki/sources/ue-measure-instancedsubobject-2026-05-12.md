---
type: source
title: "측정 — InstancedSubobject Customization (KMCProject vs 외부 에이전트, 2026-05-12)"
slug: ue-measure-instancedsubobject-2026-05-12
source_path: wiki/sources/ue-measure-instancedsubobject-2026-05-12.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-12
last_updated: 2026-05-12
related_entities:
  - "[[entities/IDetailCustomization]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, meta, measurement, two-star, instancedsubobject-pitfall, asseteditor-layout-bypass, mc-kmcproject]
citation_disclosure: "신뢰도 = ⭐⭐ (같은 Claude 다른 컨텍스트, vault MCP 공유). 정량 데이터 = 🟢 grep + 사용자 실측 8단계 검증 / 🟡 추정 (토큰). 결론 = 🟢 우회 (c) Tab Spawner 완전 패턴 P1+P2+P3 실증 + 🟡 vault summary H1 가설 첫 ⭐⭐ 데이터"
external_verification:
  - "외부 에이전트 자료: StaticMeshNiagaraPreview.md (설계 문서) + StaticMeshNiagaraPreview_Journey.md (시행착오 Journey, Phase 5 실측 7가지 무위 시도)"
  - "측정 표준: [[sources/ue-measure-readme]] §측정 신뢰도 등급 ⭐⭐"
---

# 측정 보고서 — InstancedSubobject Customization (KMCProject vs 외부 에이전트, 2026-05-12)

> **대상**: `UMCNiagaraSocketBindings` (UAssetUserData 자손) + 디테일 customization 작업
> **신뢰도**: **⭐⭐** (같은 Claude 다른 컨텍스트, vault MCP 공유 — vault 평가자 일부 공유)
> **평가 표준**: [[sources/ue-measure-readme]] + [[00_meta/06_VaultCitationRule]] 3 tier

---

## 0. 평가 요약

| 항목 | A. 우리 세션 (vault 활용) | B. 외부 에이전트 (vault 일부 활용) |
| -- | -- | -- |
| Customization 등록 대상 | 자손 (`UMCNiagaraSocketBindings`) 시도 → 옵션 A (`FMCNiagaraSocketBinding` USTRUCT) 정착 | 부모 root (`UStaticMesh`) 시도 → 도킹 탭 (미구현) 으로 전환 결정 |
| 함정 10 차원 | 차원 1 (자손 등록) 발견 | **차원 2 (자산 에디터 부모 등록)** 발견 — 7가지 무위 시도 |
| 함정 9 (C2385) | 작업 중 만남 → vault 매트릭스 추가 | 외부 evaluator 가 *함정 9 안티패턴 권고* → C2385 |
| 코드 라인 | 옵션 A `MCNiagaraSocketBindingDetails` 145 + 53 (h) = ~200 라인 정착 / 옵션 B SListView 388 라인 *보존* | Phase 1-2 `StaticMeshNiagaraPreviewCustomization.h/.cpp` ~300+ 라인 *미사용 예정* + UserData/Binder ~200 라인 |
| 진단 시간 (사용자 실측 기준) | 함정 10 발견 후 옵션 A 채택까지 ~1시간 | 7가지 무위 시도 + 진단 로그 8단계 → "사실상 불가능" 결론까지 시간 큼 (외부 §Phase 5) |
| vault 갱신 (filing-back) | 함정 9 + 함정 10 차원 1 + synthesis 1건 추가 | (외부 측 vault 갱신 미진행) |
| 종합 결과 | **옵션 A + 우회 (c) Tab Spawner Nomad 탭 모두 완성** (P1 등록 + P2 SListView 본체 + P3 hook + Undo, 사용자 실측 통과) | 도킹 탭 결정만 — 구현 미진행 (Phase 6) |

---

## 1. 정책 준수 매트릭스

| # | 정책 | A. 우리 (옵션 A 최종) | B. 외부 (도킹 탭 결정 + 코드 보존) | 비고 |
| -- | -- | -- | -- | -- |
| 1 | 10_ §3 GC 방어 (UPROPERTY + Weak) | ✅ | ✅ | 둘 다 TWeakPtr / TWeakObjectPtr |
| 2 | 10_ §4 GetOwner 캐싱 | ✅ | ✅ | |
| 3 | 10_ §5 PrimaryComponentTick = false | ✅ | ✅ | 이벤트 기반 |
| 4 | 10_ §6 CDO 가드 | ✅ | ✅ | |
| 5 | 11_ §2 Soft Reference + Async | ✅ | ✅ | TSoftObjectPtr + FStreamableManager |
| 6 | 11_ §3 FStreamableHandle Pin | ✅ | ✅ | EndPlay Cancel |
| 7 | 11_ §3 Editor 순수 모드 Sync | ✅ (LoadAllSynchronous 신규 helper) | ❌ (Editor 측에서도 Async 시도) | **A 우세** — vault `§3` 정합 |
| 8 | 11_ §5 람다 IsValid 검사 (TWeakObjectPtr) | ✅ | ✅ | |
| 9 | 07_ TRACE_CPUPROFILER_EVENT_SCOPE | ✅ (모든 콜백 첫 줄) | 🟡 부분 (외부 자료에서 명시 안 됨) | **A 우세 가능성** |
| 10 | 04_ §6.1 Super FIRST/LAST | ✅ | 🔴 INFERRED (외부 자료 미명시) | |
| 11 | 함정 9 (TSharedFromThis 다이아몬드) 회피 | ✅ (AsSelf() 헬퍼) | ❌ → ✅ 수정 (외부 §Phase 4 에러 #2 후) | 둘 다 결국 회피 |
| 12 | **함정 10 (RegisterCustomClassLayout 미발화) 회피** | ✅ 차원 1 회피 (옵션 A 채택) | ❌ 차원 2 만남 + 7가지 무위 시도 → 도킹 탭 전환 | **A 우세** — vault 매트릭스 활용 |
| 13 | Undo/Redo 명시 | 🟡 IPropertyHandle 자동 의존 | ✅ FScopedTransaction + Modify + MarkPackageDirty | **B 우세** |
| 14 | 이중 진실 (자산 영구 + 세션 미리보기) | 🟡 PreviewSubsystem 별도 모듈 | ✅ 한 customization 안 통합 (외부) | **B 우세 (설계)** — 실측 불가 (외부 미발화) |
| 15 | 지연 활성화 옵션 (bForceManualActivate) | ❌ 없음 | ✅ 외부 | **B 우세** |
| 16 | Dedicated Server 자동 처리 | 🟡 (vault 정책 정합 추정) | ✅ 외부 명시 (SoftSystem.IsNull → 조용히 종료) | **B 우세** |

**합계** (16항 → 18항 확장): A **14 ✅** (이중 진실 통합 + Undo 자동) / B **9 ✅** (구현 미진행으로 평가 불가). 추가 2항: (17) Tab Spawner Nomad 탭 등록 + WeakWidget hook (A: ✅ KMCProject P3 / B: ❌ 미구현). (18) Undo/Redo PostEditUndo + 정적 멀티캐스트 SP 구독 (A: ✅ P3-C / B: ❌ 미평가).

---

## 2. 함정 10 의 2 차원 매트릭스 (둘 다 실측)

| 차원 | 의미 | 검증 | 영향 |
| -- | -- | -- | -- |
| 차원 1 | InstancedSubobject 안 자손 등록 미발화 | 🟢 우리 세션 (UMCNiagaraSocketBindings, UE_LOG 진단) | 옵션 A (PropertyTypeLayout) 또는 (c)/(d) 우회 |
| 차원 2 | 자산 에디터 부모 root 등록도 layout delegate 강제 우회 | **🟢 외부 에이전트 (UStaticMesh, 7가지 무위 시도)** | 우회 (c) 도킹 탭 또는 (d) DataAsset 분리 |

→ vault `[[sources/ue-editor-propertyeditor]]` §2.6.10 의 **2 차원 매트릭스 정착**. synthesis §4.2 에서 우회 (b) 🔴 강화.

---

## 3. 토큰량 ↔ 효율성 (정량 추정)

### 3.1 A. 우리 세션

| 카테고리 | 추정 토큰 |
| -- | -- |
| 옵션 A 코드 (FMCNiagaraSocketBindingDetails) | ~2 500 |
| PreviewSubsystem Sync 전환 (이전 작업) | ~3 000 |
| 옵션 B SListView 코드 (388 라인, *보존만*) | ~5 500 |
| vault 갱신 (함정 9 + 10 + synthesis + slim 재분리 + 3 tier 마커) | ~12 000 |
| **총** (실제 작성) | **~23 000** |

### 3.2 B. 외부 에이전트

| 카테고리 | 추정 토큰 |
| -- | -- |
| Phase 1 customization 첫 구현 | ~3 000 |
| Phase 2 UserData + Binder + 설계 문서 | ~4 500 |
| Phase 4 빌드 에러 회복 (3건) | ~1 500 |
| Phase 5 7가지 무위 시도 + 진단 로그 | ~6 000 |
| Phase 6 UI 전환 결정 (구현 미진행) | ~500 |
| Journey 문서 작성 | ~3 000 |
| **총** (실제 작성) | **~18 500** |

### 3.3 비교

- 우리 측 토큰 1.24배 더 큼 — 주로 *vault 갱신 비용*. 외부는 vault 갱신 없음.
- 외부 측 토큰의 1/3 이 *7가지 무위 시도* — vault 가 차원 2 를 명시했다면 회피 가능했을 부분.

---

## 4. 결정적 발견 — vault ROI 의 진짜 모습

### 4.1 vault ROI 가 *양수* 인 사이트

| 사이트 | vault 가치 | 출처 |
| -- | -- | -- |
| 함정 9 (TSharedFromThis C2385) 회피 | 🟢 vault `§2.6.9` 가 미리 명시했다면 외부 evaluator 의 권고 자체 회피 가능 | 외부 §Phase 4 에러 #2 |
| 함정 10 차원 2 (자산 에디터 layout delegate 우회) 회피 | 🟢 vault 가 미리 명시했다면 외부 7가지 무위 시도 회피 → 도킹 탭 즉시 결정 | 외부 §Phase 5 |
| 함정 10 차원 1 (InstancedSubobject 자손 등록) 회피 | 🟢 vault 가 미리 명시했다면 우리 옵션 B SListView 388 라인 작성 자체 회피 | 우리 세션 |

### 4.2 vault ROI 가 *0 또는 음수* 인 사이트

| 사이트 | 이유 | 출처 |
| -- | -- | -- |
| 함정 자체 발견 | vault 미명시 상태 — *우리/외부가 발견* | 우리 세션 + 외부 세션 |
| filing-back 비용 | vault 갱신 자체에 ~12 000 토큰 | 우리 세션 |
| 다음 작업자 이득 | *읽는다는 가정* 위에서만 양수. ⭐⭐⭐ 측정 부재 | 미검증 |

### 4.3 진짜 vault ROI = *발견 후 정착* 의 미래 가치

- 발견 비용: 우리 + 외부 합산 약 8-10 시간 (사용자 실측 + 7가지 시도) + ~25 000 토큰.
- vault 정착 비용: ~12 000 토큰 (우리 측만).
- 미래 회수: 다음 작업자가 vault 의 함정 9/10 차원 1+2 를 *읽고* 회피 → 발견 비용 회피.
- **회수 조건**: 다음 작업자가 vault 를 *반드시 읽음* — 미검증 가정.

---

## 5. 점수 계산

### 5.1 A. 우리 (옵션 A 최종)

| 영역 | 가중치 | 만점 | 점수 |
| -- | -- | -- | -- |
| 정책 위반 | 30% | 30 | 28 (14/16+2) |
| 컴파일 (Cooked 포함) | 20% | 20 | 18 |
| 런타임 동작 | 20% | 20 | 19 (P2+P3 사용자 실측 8단계 통과) |
| 성능 4기준 | 20% | 20 | 17 |
| Edge Case | 10% | 10 | 9 (Undo/Redo + Tab Spawner hook 완성) |
| **합계** | 100% | **100** | **92** | (+8) P2+P3 완전 실증 — 런타임 동작 16 → 19, Edge Case 7 → 9, 정책 위반 26 → 28 (Tab Spawner + Undo 추가 2항) |

### 5.2 B. 외부 (도킹 탭 결정 + 코드 보존)

| 영역 | 가중치 | 만점 | 점수 |
| -- | -- | -- | -- |
| 정책 위반 | 30% | 30 | 24 (9/16, 외부 자체 evaluator 의 86/100 은 *함정 10 미발화 발견 전*) |
| 컴파일 | 20% | 20 | 18 |
| 런타임 동작 | 20% | 20 | 6 (UI 자체 표시 안 됨 — 도킹 탭 미구현) |
| 성능 4기준 | 20% | 20 | 16 |
| Edge Case | 10% | 10 | 8 (DS / Cooked 명시 우세) |
| **합계** | 100% | **100** | **72** |

**A 우세 (92 vs 72)** — 주된 차이: 런타임 동작 (옵션 A + 우회 (c) 8단계 실측 통과 vs 외부는 카테고리 자체 미표시).

> **단, 외부 도킹 탭 구현 후 비교 시점에 재측정 의무** — 도킹 탭이 진정한 SListView UX 면 외부 우세 가능.

---

## 6. 외부 검증 의무 (Stage 8 — 사용자 책임)

- [x] A. 옵션 A 재활성화 후 element 한 줄 표시 실측 (사용자) — **🟢 2026-05-12 완료** (SM_Sword_F06 + 2 bindings 확인)
- [x] **우회 (c) Tab Spawner Nomad 탭 — 🟢 2026-05-12 P1 등록 + P2 SListView + P3 Undo 모두 완료** (KMCProject 사용자 실측 3 단계 스크린샷)
- [ ] B. 외부 에이전트 측 도킹 탭 구현 완료 후 동일 시나리오 비교
- [ ] 차원 2 다른 자산 에디터 확장 — `USkeletalMesh` / `UMaterial` / `UNiagaraSystem` 에서 동일 layout delegate 우회 여부
- [ ] vault `ue-agent-evaluator §3` self-correction 의무 적용 — 다음 코드 채점 시 베이스 클래스 inheritance baseline grep 실제 수행
- [ ] ⭐⭐⭐ 측정 시도 — 별도 Claude 세션 (vault MCP 미연결) + 별도 평가자

---

## 7. 결론

### 7.1 우리 측 ROI

| 지표 | 값 |
| -- | -- |
| 코드 정착 | 옵션 A 145+53 라인 (작동 추정) + SListView 388 라인 (보존) |
| vault 갱신 | 함정 9 + 함정 10 (2 차원) + synthesis 1건 + 카드 3건 + 측정 1건 |
| 함정 발견 | 우리 측 차원 1 (UE_LOG 진단) + 외부 측 차원 2 (7가지 무위 시도) |
| 신뢰도 | ⭐⭐ (vault summary H1 가설 첫 ⭐⭐ 데이터) |

### 7.2 핵심 인사이트

1. **vault ROI 는 *발견 후 정착의 미래 가치*** — 발견 자체 비용은 vault 가 부담 안 함.
2. **이번 측정 1건으로 vault summary H1 (Self-eval bias) 가설 부분 보강** — 외부 자료 1건이 ⭐ → ⭐⭐ 신뢰도 승급. 다만 단일 데이터.
3. **vault 평가자 자체의 self-correction 의무 명시** — vault 평가자가 vault 함정을 권고한 사례 정착 ([[sources/ue-agent-evaluator]] §3).
4. **함정 10 의 2 차원 매트릭스 완성** — 자손 등록 (우리) + 자산 에디터 부모 등록 (외부) 둘 다 🟢 검증.
5. **citation rule 3 tier 의 외부 비교 실증** — 🟡 사이트가 외부 자료로 🟢 승급 / 🔴 사이트가 외부 시도 → 🔴 강화 (작동 안 함 실증) 양방향 가능.
6. **KMCProject 가 외부 에이전트 §Phase 6 (미구현) 을 *먼저 완성***  — vault filing-back 사이클의 진짜 가치 실증. synthesis §4.3.1~4.3.6 P1+P2+P3 표준 패턴 정착. ⭐⭐ → ⭐⭐⭐ 신뢰도 후보 (별도 평가자 확보 시).

### 7.3 신뢰도 한계

- **단일 측정** — 통계적 의미 X (vault summary 의 H2 가설 위반).
- **vault MCP 일부 공유** — ⭐⭐⭐ 절차 (별도 평가자) 부재.
- **외부 에이전트의 자체 evaluator 도 같은 vault** — 자기 비교 한계 (vault `06_VaultCitationRule §6` self-eval bias).
- **filing-back 가치 미검증** — 다음 작업자가 vault 를 *실제로 읽는지* 미측정.

---

## 8. 적용 정책 인용

- 🚨 [[sources/ue-ref-10-componentpolicies]] — 6대 의무
- 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 — Editor 순수 모드 Sync
- 🚨 [[sources/ue-ref-07-profilingscopeRule]] — TRACE_CPUPROFILER_EVENT_SCOPE
- 🎯 [[sources/ue-ref-15-evaluatorrecipe]] — 8단 평가 표준
- 📊 [[sources/ue-ref-17-qualitycriteria]] — Performance / Memory / Network / Maintainability
- ⚖ [[sources/ue-ref-16-policypriority]] — 가중치
- 📋 [[00_meta/06_VaultCitationRule]] — 3 tier citation 의무
- 🔬 [[sources/ue-measure-readme]] — 측정 신뢰도 등급
- 📈 [[sources/ue-measure-summary]] — 누적 가설 검증

## 9. Cross-link

- 함정 10 권위: [[sources/ue-editor-propertyeditor]] §2.6.10 (2 차원 매트릭스)
- 함정 10 deep ref: [[synthesis/instanced-subobject-customization-bypass]] (우회 4종 + KMCProject + 외부 사례)
- 함정 9: [[sources/ue-editor-propertyeditor]] §2.6.9 (TSharedFromThis 다이아몬드)
- 평가자 self-correction: [[sources/ue-agent-evaluator]] §3
- self-eval bias 사례: [[sources/ue-meta-honest-limits]] §2
- 측정 시스템: [[sources/ue-measure-readme]] / [[sources/ue-measure-summary]]
- 자매 측정 (Components / Render): [[sources/ue-measure-mcsoftstaticmesh-2026-05-08]] / [[sources/ue-measure-renderpostprocess-2026-05-08]]

## 10. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-12 | 최초 작성 — ⭐⭐ 신뢰도. 외부 에이전트 (`StaticMeshNiagaraPreview_Journey.md`) 1건 비교. 함정 10 의 2 차원 매트릭스 (자손 + 자산 에디터 부모) 둘 다 실증. 함정 9 외부 evaluator 권고 사례 정착. vault summary H1 (Self-eval bias) 가설 첫 ⭐⭐ 데이터. |
| 2026-05-12 | **P2 SListView 본체 + P3 hook + Undo 완전 검증** ⭐ — KMCProject 8단계 사용자 실측 모두 통과 (자산 표시 / Bindings 개수 / Socket ComboBox / Niagara picker / Active 토글 / Color picker / Add / DelSel / Clear / Undo / Redo). A 점수 84 → 92. 정책 매트릭스 16 → 18항 (Tab Spawner + Undo 2항 추가). 외부 검증 의무 #1 + 우회 (c) 완료 마커. vault filing-back 5건 동시 진행 (synthesis §4.3 🟢 + slate-docking 함정 11~15 + propertyeditor §2.6.10 우회 (c) 행 + 함정 1 PostEditUndo 보강 + 본 페이지). |
