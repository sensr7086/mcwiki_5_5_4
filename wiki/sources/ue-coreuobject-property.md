---
type: source
title: "UE CoreUObject — Property sub-skill"
slug: ue-coreuobject-property
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Property.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FProperty]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/UPROPERTY-Markup]]"
tags: [ue, runtime, foundation, coreuobject, reflection]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE CoreUObject — Property sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Property.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

[[entities/FProperty]] 5.x 시스템 디테일 — FObjectProperty / FArrayProperty / FMapProperty / FStructProperty + CastField + TFieldIterator + ImportText / ExportText + ContainerPtrToValuePtr.

## 2. Key claims

- FProperty 자손 카탈로그: FBoolProperty / FIntProperty / FFloatProperty / FStrProperty / FNameProperty / FObjectProperty / FStructProperty / FArrayProperty / FMapProperty / FSetProperty / FMulticastDelegateProperty 등.
- CastField<T>: FProperty → 자손 cast. UE 4.x 의 Cast<UObjectProperty> 의 5.x 대체.
- TFieldIterator<FProperty>(Class): UClass 의 모든 FProperty 순회.
- ImportText / ExportText: text ↔ Property value 변환 — Editor / 직렬화 / `.ini` 파일.
- ContainerPtrToValuePtr<T>(Object): Object 의 Property 메모리 주소 반환 — 동적 멤버 접근의 핵심.
- UProperty 는 deprecated — 신규 코드는 FProperty.

## 3. Quotations

> "5.x 의 reflection 표준 — UProperty (UE 4.x) 는 deprecated. CastField 가 Cast 를 대체."

## 4. Open questions

- [ ] FStructProperty 의 USTRUCT vs FInstancedStruct (StructUtils) 결정 트리
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| `Public/UObject/PropertyWrapper.h` | `UPropertyWrapper` (L22), `UMulticastDele → | `Public/UObject/UnrealType.h` / `Class.h` | `UPropertyWrapper`, `UMulticastDel`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/CoreUObject/references/Property.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/CoreUObject/references/Property.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
