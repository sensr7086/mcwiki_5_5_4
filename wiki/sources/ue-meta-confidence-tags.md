---
type: source
title: "UE meta — confidence-tags (3 tier 신뢰도 체계)"
slug: ue-meta-confidence-tags
source_path: raw/ue-wiki-llm/meta/confidence-tags.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
tags: [ue, meta, governance, citation, confidence, three-tier, self-eval-bias]
citation_disclosure: "본 카드 = 🟢 vault 직시 (3 tier 체계가 00_meta/06_VaultCitationRule + ue-meta-honest-limits §2 self-eval bias 사례 2건 + Cycle 5d 1차 evaluator 평균 89.5 / 2차 §2.11.1 격상 실측 모두 vault 내). raw 원본 slim → vault-side 정밀화."
---

# UE meta — confidence-tags (3 tier 신뢰도 체계)

> Source: [[raw/ue-wiki-llm/meta/confidence-tags.md]]
>
> 보강 2026-05-15 (Cycle 5d 2차) — slim card → 정밀 enrich. raw 의 `[verified] / [grep-listed] / [inferred]` 3단계 의무 + [[00_meta/06_VaultCitationRule]] 의 🟢/🟡/🔴 정밀판 통합 + Cycle 5a~5d 실측 사례 + 격상 / 강등 절차.

## 1. Summary

🚨 **위키 항목의 3 tier 신뢰도 체계** — 매 사실 주장에 의무 적용. 사용자가 한 줄로 vault 자산성과 LLM 인퍼런스를 식별 가능해야 한다. raw 원본 (`[verified] / [grep-listed] / [inferred]`) 과 [[00_meta/06_VaultCitationRule]] (🟢 VAULT / 🟡 PARTIAL / 🔴 INFERRED) 의 매핑 정밀판 + Cycle 5a~5d 격상 / 강등 실측.

## 2. 3 tier 매트릭스 (정밀판)

| Tier | raw 원본 마커 | 정밀 마커 (06_VaultCitationRule) | 의미 | 검증 방법 | 사용 시 의무 |
| -- | -- | -- | -- | -- | -- |
| ⭐⭐⭐ | `[verified]` | 🟢 **VAULT** | 실제 grep + 컴파일 + Cooked 검증 완료 (또는 vault 본문 직접 인용) | `Read` / `Grep` / `Build.bat` + Cooked Build + `[[wikilink]]` | (없음 — 직접 사용 가능) |
| ⭐⭐ | `[grep-listed]` | 🟡 **PARTIAL** | 헤더 / 라인 grep 만 (실제 동작 미확인) 또는 vault 근거 일부 + 외삽 | grep 라인 인용 + "(외삽 부분 명시)" | "vault 근거: ... · 외삽" 짧은 주석 |
| ⭐ | `[inferred]` | 🔴 **INFERRED** | 추측 — 외부 검증 의무 (vault 미확정) | 일반 UE 지식 / 외부 docs / 코드 추론 | "**추론** (vault 미확정)" prefix 의무 + 사용 전 외부 검증 |

## 3. 의무 운영 흐름 (3 tier 분류 알고리즘)

```text
주장 작성 → vault 검증 의무
  ↓
[Step 1] mcwiki:search → 매치 페이지 확인
  ├─ 매치 있음 → mcwiki:read_page → 본문에서 직접 답 가능?
  │   ├─ Yes → 🟢 VAULT — [[wikilink]] + 라인 번호 인용
  │   ├─ Partially → 🟡 PARTIAL — vault 근거 + 외삽 부분 분리 표기
  │   └─ No  → 🔴 INFERRED — vault 미확정 명시
  └─ 매치 없음 → 🔴 INFERRED 의무 (no fallback)
  ↓
[Step 2] (선택) Grep / Read 로 UE Engine source 직접 검증
  ├─ Yes → 🟢 으로 격상 가능 (라인 번호 인용)
  └─ No  → tier 유지
  ↓
[Step 3] (선택) 컴파일 / Cooked Build 검증
  └─ 성공 → ⭐⭐⭐ [verified] (vault 페이지 갱신 의무 → log.md append_log)
  ↓
[Step 4] 사용자 외부 검증 결과 도착 시
  ├─ 검증 PASS → 🟡/🔴 → 🟢 격상 (filing-back)
  └─ 검증 FAIL → [[sources/ue-meta-corrections]] 누적 + 페이지 강등 / 정정
```

## 4. 격상 / 강등 절차

### 4.1 격상 (🟡 PARTIAL → 🟢 VAULT) — 외부 검증 사이트 확보 시

**조건**:
1. 동일 패턴이 UE Engine source / KMCProject 외 사이트에서 재현 가능
2. grep / Read 로 라인 번호 직접 확인
3. 컴파일 또는 동작 검증

**절차**:
1. 페이지 §추가 (예: `§2.11 → §2.11.1`) — "다른 customization 재현 검증" 형태
2. 검증 매트릭스 추가 — 사이트 + 라인 번호 + 회피 패턴
3. tier 표시 갱신 — 🟡 → 🟢
4. `last_updated` 갱신
5. `log.md` append_log — `op: note` + 격상 기록

**Cycle 5d 2차 실측 예시** ([[sources/ue-coreuobject-uobject]] §2.11.1):
- Before (2026-05-14 Cycle 5c): KMCProject `UMCHitBoneCurveUserData` 1 사이트만 — 🟡 single-case 의심
- After (2026-05-15 Cycle 5d 2차): UE Engine `SRowEditor` + `PerlinNoiseChannel` 2 사이트 grep 검증 — 🟢 일반 패턴
- 회피 패턴 매트릭스 1 → 3종 확장 (A Reserve / B FStructOnScope 자손 override / C FInstancedStructProvider)

### 4.2 강등 (🟢 VAULT → 🔴 INFERRED) — 외부 정정 또는 audit 실패 시

**조건**:
1. 사용자 발견 거짓 (`[[sources/ue-meta-corrections]]` 등록)
2. UE 마이너 업그레이드 후 라인 번호 / 시그니처 불일치
3. 분기 audit 에서 stale 발견 (>90 days)

**절차**:
1. 페이지 §정정 — 잘못된 부분 명시 + 정정 출처
2. tier 표시 강등 — 🟢 → 🔴 (또는 페이지 deprecate)
3. `corrections.md` 또는 `[[sources/ue-meta-corrections]]` 누적
4. `last_updated` 갱신 + `log.md` append_log — `op: correction`
5. 분기 audit 시 재검증 의무

## 5. Cycle 5a~5d 격상 / 강등 실측 매트릭스 (KMCProject vault 진화)

| 페이지 / § | Before (tier) | After (tier) | Cycle | 격상 사유 |
| -- | -- | -- | -- | -- |
| `ue-coreuobject-uobject` §2.10 (C2440) | 🟡 single-case (KMCProject) | 🟢 vault 의무 정책 catalog | 5a (2026-05-14) | const 오버로드 vault 페어 + mc-asset-validation-policy §11 |
| `ue-editor-toolmenus` §2.9 (TabManager Window 메뉴) | 🔴 INFERRED ("ToolMenus 가 메뉴 관리") | 🟢 VAULT (TabManager 자체 시스템 발견) | 5b (2026-05-14) | KMCProject 5 후보 ToolMenus stub 검증 |
| `ue-editor-propertyeditor` §2.8 (IStructureDetailsView) | 🟡 외삽 | 🟢 VAULT (KMCProject crash 0xFFFF 재현) | 5c (2026-05-14) | dangling pointer 실측 |
| `ue-coreuobject-uobject` §2.11 (FStructOnScope TArray) | 🟡 single-case (KMCProject 1) | 🟢 일반 패턴 (UE Engine 2 사이트 재현) | 5d 2차 (2026-05-15) | SRowEditor + PerlinNoise grep 검증 |
| `ue-editor-assettools` §2.6.1 (RegisterAdvancedAssetCategory FText 2번째 호출 무시) | 🟡 외삽 | 🟡 외삽 (유지) | 5d 1차 | UE Engine source grep 미실시 — Cycle 5e 후보 |

→ **5건 중 4건 격상**, 1건 미진행 — Cycle 5e 후보로 이동.

## 6. ⚠ 함정 — vault 평가자의 self-eval bias

상세 = [[sources/ue-meta-honest-limits]] §2.

**핵심** — vault 평가자 (ue-agent-evaluator) 가 vault 안 함정을 권고한 사례 2건 ([[sources/ue-meta-honest-limits]] §2.1 + §2.2). 평가자 카드 (ue-agent-evaluator) 의 권고가 *vault 다른 페이지의 함정 안티패턴* 과 모순. **권고 전 baseline grep 의무**.

→ 본 confidence-tags 의무 = **평가자도 의무 적용**. 평가자가 "🟢 권고" 표시 시 vault 내 페어 페이지 검증 의무 (예: `IDetailCustomization` 자손에 `TSharedFromThis` 권고 시 → `[[sources/ue-editor-propertyeditor]] §2.6.9 함정 9` 검증 의무).

## 7. Cross-link

### 페어 (의무 Read)

- [[sources/ue-meta-honest-limits]] — 6대 한계 + Self-eval bias 사례 (본 § 6 의 권위)
- [[sources/ue-meta-corrections]] — 사용자 발견 거짓 누적 (강등 절차의 입력)
- [[sources/ue-meta-governance]] — 거버넌스 마스터
- [[00_meta/06_VaultCitationRule]] — 본 § 의 정밀판

### 격상 / 강등 사례 권위

- [[sources/ue-coreuobject-uobject]] §2.10 / §2.11 / §2.11.1 (Cycle 5a/5c/5d 실측)
- [[sources/ue-editor-toolmenus]] §2.9 (Cycle 5b 강등 → 격상)
- [[sources/ue-editor-propertyeditor]] §2.8 (Cycle 5c 격상)

### 운영 메타

- [[00_meta/03_EvaluatorRecipe]] — 8단계 평가
- [[00_meta/04_AuditPolicy]] — 분기 audit
- [[00_meta/06_VaultCitationRule]] — 3 tier 인용


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-ref-02-verificationlog]] (inbound=3, suggest_missing_cross_link high confidence)
- [[sources/ue-ref-19-externalsourcesguide]] (inbound=3, suggest_missing_cross_link high confidence)
## 8. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest, slim) |
| **2026-05-15 (Cycle 5d 2차)** | **정밀 enrich** — §2 3 tier 매트릭스 (raw `[verified]/[grep-listed]/[inferred]` ↔ 06_VaultCitationRule `🟢/🟡/🔴` 매핑) + §3 의무 운영 흐름 알고리즘 + §4 격상 / 강등 절차 (Cycle 5d 2차 §2.11.1 실측 사례) + §5 Cycle 5a~5d 격상 / 강등 매트릭스 (5건 중 4건 격상) + §6 self-eval bias 페어 + §7 Cross-link 4종 권위. raw slim → vault-side 정밀화. 🟢 vault 직시 (모든 격상 사례가 vault 안 페어 페이지로 검증 가능). |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
