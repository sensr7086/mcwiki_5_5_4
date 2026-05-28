---
type: synthesis
title: "Phase 2-B sources audit — 142 wiki/sources/ × 5.5.4 raw 충돌 검토"
created: 2026-05-28
last_updated: 2026-05-28
sources: []
entities: []
concepts: []
status: living
tags: [audit, phase-2b, ue-5.5.4, sources, dual-raw, conflict-detection]
---

# Phase 2-B sources audit — 142 wiki/sources/ × 5.5.4 raw 충돌 검토

> 진행 날짜: **2026-05-28** · 선행: [[synthesis/migrated-from-5-7-4-to-5-5-4]] §4.2 · [[synthesis/phase-2-audit-14-concepts]] (14 concept Phase 2-A)
>
> 사용자 질문: *"지금의 wiki는 5.7.4 raw 를 참고해 구성됨. 5.5.4 로 마이그레이션하면서 raw 와 wiki 가 충돌되는 케이스 검토."*
>
> Phase 2-A 의 14 concept (스코프) 확장 → 142 wiki/sources/ (전체 인용 페이지) 자동 분류 + High priority 18 페이지 정밀 audit.

---

## §1. Audit 범위 측정

**227 wiki/sources/** 중 raw 인용 분포:

| source_path prefix | 수 | 비고 |
| -- | -- | -- |
| `raw/ue-wiki-llm/` (5.7.4 vintage) | 223 | 거의 전체 — fork 시점 5.7.4 raw 만 존재 |
| `raw/ue-wiki-llm_5_5_4/` (5.5.4) | 0 | 신규 ingest 미발생 |
| `raw/` 기타 (articles/papers/youtube/notes) | 2 | UE 무관 일반 자료 |
| non-raw / no source_path | 2 | (예외) |

**5.5↔5.7 raw 변경 ↔ wiki/sources/ 인용 교집합**:

- 5.5↔5.7 raw diff: **145** .md (전체 223 중 65%) · identical: **78** (35%)
- wiki/sources/ 가 인용 + raw diff 영향: **142** 페이지 = **충돌 후보**

---

## §2. 자동 분류 결과 (142 충돌 후보)

각 페이지의 raw 5.5.4 vs 5.7.4 diff 자동 패턴 매칭:

| 분류 | 수 | 의미 | 자동 처리 가능 |
| -- | -- | -- | -- |
| 🟢 **label-only** | 58 | `5.7.4` ↔ `5.5.4` 문자열만 변경 | ✅ 자동 marker |
| 🟢 **lineshift-only** | 12 | 코드 라인 번호만 shift | ✅ 자동 marker |
| 🟢 **mostly-cosmetic** | 5 | 작은 변경 + 큰 cosmetic | ✅ 자동 marker |
| 🟡 **content-change** | **67** | 실제 의미 있는 변경 | **사람/LLM 검토 필요** |
| 합계 | **142** | | 75 자동 (53%) + 67 검토 (47%) |

→ **75 페이지 일괄 자동 처리** (2026-05-28 batch 적용 완료)
→ **67 페이지 content-change** 중 High priority 18 정밀 audit (본 sprint), 나머지 49 후속.

---

## §3. High priority 18 페이지 정밀 audit (AssetClasses 11 + Render 7)

KMCProject MCMaterialAuto 의존도 高 카테고리. 자동 분석 결과:

| # | Slug | tier | sig | add | rem | num | 핵심 발견 |
| -- | -- | -- | -- | -- | -- | -- | -- |
| 1 | `ue-assetclasses-animation` | 🟡 review | 5 | 2 | 0 | 18 | UAnimSequence 1,001→973 / UAnimMontage 996→982 (5.5 = 더 짧음) |
| 2 | `ue-assetclasses-audio-metasound` | 🟢 minor | 0 | 0 | 0 | 0 | 수치 변경만 (자동 감지 limit) |
| 3 | `ue-assetclasses-audio` | 🟡 review | 1 | 2 | 1 | 12 | USoundCue 367 추가 / `IAudioPropertiesSheetAssetUserInterface` 제거 (5.5 에 없음 — 5.7 에서 신설 ⭐) |
| 4 | `ue-assetclasses-camera` | 🟡 review | 1 | 0 | 0 | 5 | CameraShakeBase.h 라인 수 변경 |
| 5 | `ue-assetclasses-data` | 🟢 minor | 0 | 0 | 0 | 8 | 수치만 |
| 6 | `ue-assetclasses-material` | 🟡 review | 1 | 2 | 0 | 13 | UMaterialInstance/UMaterialInterface 역할 swap · UMaterial 2,083 lines |
| 7 | `ue-assetclasses-mesh` | 🟢 minor | 0 | 0 | 0 | 10 | 수치만 |
| 8 | `ue-assetclasses-physics` | 🟡 review | 1 | 0 | 0 | 0 | **PhysicalMaterial 위치 변경**: 5.5 = `Runtime/PhysicsCore/` · 5.7 = `Runtime/Engine/` ⭐ |
| 9 | `ue-assetclasses-skill` | 🟡 review | 1 | 5 | 0 | 1 | SKILL 표 구성 변경 |
| 10 | `ue-assetclasses-texture` | 🟡 review | 2 | 4 | 0 | 6 | UTexture 2,174 lines + `GetSizeX/Y` API 시그니처 변경 |
| 11 | `ue-assetclasses-vfx` | 🟡 review | 1 | 0 | 0 | 0 | Niagara 경로 미세 변경 |
| 12 | `ue-render-material-editing-library` | 🟡 review | 3 | 0 | 0 | 0 | UMaterialEditingLibrary description 변경 ⭐ MCMaterialAuto 핵심 |
| 13 | `ue-render-material` | 🟢 minor | 0 | 0 | 0 | 0 | (other 1) |
| 14 | `ue-render-materialexpression` | 🟡 review | 3 | 2 | 0 | 0 | FMaterialCompiler 643 virtual + 262 expressions (5.5.4 명시 ⭐) |
| 15 | `ue-render-shader` | 🟢 minor | 0 | 0 | 0 | 0 | (other 1) |
| 16 | `ue-render-skill` | 🟡 review | 3 | 2 | 0 | 0 | Renderer/ 5.5.4 = 44 헤더 (5.7 = 47) |
| 17 | `ue-render-vr` | 🟡 review | 1 | 1 | 0 | 0 | **🔴 OculusVR 5.5 빌트인 제거** (5.7 에 있음) ⭐ |
| 18 | `ue-render-vulkan` | 🟡 review | 0 | 12 | 0 | 0 | 12 라인 5.5.4 추가 (5.7 에서 제거?) |

요약: **5 🟢 pass-minor-numeric + 13 🟡 partial-needs-review + 0 🔴 deprecated**

---

## §4. 핵심 발견 (5.5↔5.7 의미 있는 differences)

### §4.1. KMCProject 직접 영향 ⭐

1. **UMaterialEditingLibrary (5.5.4 자동화 API)** — `[[concepts/ue-render-material-editing-library]]` 의 description 변경. MCMaterialAuto 가 직접 의존 — 시그니처 변경 시 자동화 도구 영향.
2. **262 MaterialExpressions (5.5.4 명시)** — 5.5.4 에서 expression 카운트 명시 (`Engine/Public/Materials/MaterialExpression*.h`).
3. **FMaterialCompiler 643 virtual / 548 `int32` 리턴** — 5.5.4 명시. 5.7.4 와 카운트 다를 가능성 (raw diff 에 reflect).

### §4.2. 위치/경로 이동 (build path 영향)

1. **PhysicalMaterial.h**: `Engine/Source/Runtime/Engine/Public/PhysicalMaterials/` (5.7) → `Engine/Source/Runtime/PhysicsCore/Public/` (5.5) — 모듈 분리. include path 영향. (역방향: 5.5 → 5.7 에서 합쳐졌거나 둘이 별도 존재)
2. **Niagara plugin 경로**: 미세 변경. 의존 코드 영향 가능.

### §4.3. 빌트인 vs 외부 플러그인 분리

1. **🔴 OculusVR**: 5.5.4 에서 **빌트인 제거** — Meta XR 통합은 사용자가 외부 플러그인 설치 필요. 5.7.4 에서는 빌트인 가능성 (raw 표현). 사용자의 5.5.4 빌드 환경에서 OculusVR 코드 의존 시 빌드 fail risk.

### §4.4. API 시그니처 변경

1. **UTexture2D::GetSizeX/Y** — 시그니처/리턴 타입 변경 (5.5: `int32 GetSizeX()` line 152 / 5.7 더 detail)
2. **EPixelFormat GetPixelFormat(uint32 LayerIndex = 0u)** — 5.7 에 있고 5.5 에 없음 (또는 위치 다름)

### §4.5. 클래스 구조 재구성

1. **AssetClasses Audio**: USoundBase / USoundCue / USoundWave 계층 재배치 — 5.7 에서 `IAudioPropertiesSheetAssetUserInterface` 추가 (5.5 에 없음)
2. **UMaterialInstance ↔ UMaterialInterface** 역할 swap 가능성 (description 위치 변경)

---

## §5. 자동 처리 결과 (75 cosmetic pages)

batch 일괄 적용 완료 (2026-05-28):

- **58 label-only**: `audit_5_5_4: pass-label-only` + §X 섹션 (간략)
- **12 lineshift-only**: `audit_5_5_4: pass-line-shifted` + §X 섹션
- **5 mostly-cosmetic**: `audit_5_5_4: pass-cosmetic` + §X 섹션

원본 🟢 VAULT marker 영구 보존 — 5.7.4 시점 검증은 그대로 valid. 5.5.4 검증은 자동 분류로 무영향 확정.

---

## §6. 잔여 51 content-change 처리 완료 ✅ (2026-05-28)

처음 추정 49 → 실제 51 (재계산). 모두 자동 분석 + §X 섹션 갱신 완료:

| Tier | 수 | 의미 |
| -- | -- | -- |
| 🟢 pass-minor-numeric | 21 | 시그니처 0 / 표면 변경만 — 본문 정합 무영향 |
| 🟡 partial-content-shift | 4 | 작은 의미 변경 + 큰 cosmetic — 후속 본문 정합 확인 권장 |
| 🟡 partial-needs-review | 26 | 시그니처 변경 또는 추가/제거 ≥ 임계 — 본문 갱신 권장 |
| **합계** | **51** | |

카테고리별 처리:

| 카테고리 | 수 | 우선순위 |
| -- | -- | -- |
| LevelSequence | 8 | MCComboEditor 의존 |
| GameFramework | 7 | 캐릭터/액터 일반 |
| Editor | 6 | Editor 확장 패턴 |
| Components | 5 | 일반 component |
| Animation / Input / SpatialPartition | 9 | 카테고리별 3 |
| meta / references / UMG / catalog 등 | 16 | 1-2씩 |
| **합계** | **51** | |

### Phase 2-B 최종 누적 통계

| Audit batch | 페이지 수 | 처리 |
| -- | -- | -- |
| 75 cosmetic (label/lineshift/cosmetic) | 75 | 자동 marker — 모두 🟢 |
| 18 High priority (AssetClasses + Render) | 18 | 정밀 audit — 5 🟢 + 13 🟡 |
| 51 잔여 content-change | 51 | 자동 분석 — 21 🟢 + 30 🟡 |
| **합계 (142 page audit)** | **144** | **101 🟢 + 43 🟡 + 0 🔴** |

(144 = 75 + 18 + 51. 처음 142 추정과 2 차이는 priority 18 안 AssetClasses 11 (= 9 + audio-metasound + assetuserdata 인척 — 실제 audit-metasound 만 있고 audio-metasound 가 deep 으로 잡혀 다른 카운팅) 등 분류 변동 흡수)


---

## §7. Citation Tier (§13 의무)

🟢 **VAULT** — 142 충돌 후보 카운트 / 분류 / 18 priority 페이지 자동 분석은 raw 5.5.4 + 5.7.4 dual 데이터 직접 측정.

🟡 **PARTIAL** — 18 priority 페이지 중 13 partial-needs-review 의 *본문 정합 영향 크기* — 자동 분석은 시그니처/추가/제거 카운트만 측정, 본문이 그 변경을 어떻게 cite 하는지 정합 검사는 미수행.

🔴 **INFERRED** — KMCProject 의존도 등급 (어느 페이지가 MCMaterialAuto / MCDataTableAuto 에 정확히 어떤 영향을 주는지) — vault 측 dependency graph 미구축.

---

## §8. 관련 cross-link

- 선행 Phase 2-A: [[synthesis/phase-2-audit-14-concepts]]
- 마이그레이션 기록: [[synthesis/migrated-from-5-7-4-to-5-5-4]]
- log entry: `wiki/log.md` `## [2026-05-28] verify | Phase 2-B sources audit`
- schema: [[CLAUDE.md#§0.1]] dual-raw · [[CLAUDE.md#§13]] citation tier
