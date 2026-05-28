---
type: source
title: "UE Components — USceneComponent sub-skill"
slug: ue-components-scenecomponent
source_path: raw/ue-wiki-llm/skills/Components/references/SceneComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/USceneComponent]]"
related_concepts:
  - "[[concepts/Mobility]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Components — USceneComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/SceneComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/USceneComponent]] 트랜스폼 보유 베이스 — SetWorldLocation / SetRelativeLocation / AttachToComponent / GetForwardVector / [[concepts/Mobility]] (Static/Stationary/Movable). Sockets 지원.

## 2. Key claims

- Transform 3 종 axis: Location / Rotation / Scale. Relative (부모 기준) / World (절대).
- AttachToComponent(Parent, SocketName, Rules) — Component Hierarchy. Rules: KeepRelative / KeepWorld / SnapToTarget.
- GetForwardVector / GetRightVector / GetUpVector — World rotation 의 axis.
- [[concepts/Mobility]] 결정 (Constructor 안만, 런타임 SetMobility 금지): Static (변경 X / Light Baked) / Stationary (위치 고정 / Light 일부 동적) / Movable (모두 가능 / Light Baked X).
- Sockets: Skeleton 의 본 또는 Mesh 의 named transform. AttachToComponent 의 SocketName 인자.
- WorldTransform 캐싱 — Attach Hierarchy 갱신 시 자동 dirty.

## 3. Open questions

- [ ] AttachToComponent 의 Sockets 명명 규칙 (Skeleton vs StaticMesh)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `### 4.2 Setter API (Widget.h L427+) → ### 4.2 Setter API (SceneComponent.h L383+)`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Components/references/SceneComponent.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Components/references/SceneComponent.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
