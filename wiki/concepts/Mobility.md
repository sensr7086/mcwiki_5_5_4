---
type: concept
title: "Mobility (Static / Stationary / Movable)"
aliases: [Mobility, EComponentMobility]
sources:
  - "[[sources/ue-components-skill]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, rendering]
last_updated: 2026-05-09
---

# Mobility — Static / Stationary / Movable

## 1. 정의 (한 줄)

[[entities/USceneComponent]] (그리고 자손 모두) 의 위치/회전 변경 가능성 + Light Baking 호환성을 결정하는 enum (`EComponentMobility`).

## 2. 자세히

| Mobility | 위치 변경 | Light Baking | 사용처 |
| -- | -- | -- | -- |
| **Static** | ❌ 런타임 변경 X | ✅ Fully baked | 변하지 않는 환경 (벽, 지형, 정적 props) |
| **Stationary** | ❌ 위치 고정 (Light intensity / color 는 변경 가능) | ✅ Direct lighting baked, indirect dynamic | 변동 가능한 light 가 부착된 정적 props |
| **Movable** | ✅ 모두 가능 | ❌ Baking X / Dynamic only | 캐릭터 / 동적 props / VFX |

## 3. 변형 / 사례 / 응용

- **생성자에서 결정**: `SetMobility(EComponentMobility::Movable)`. 런타임 SetMobility 금지 — Light Baking 일치 깨짐.
- **Light Mobility 와 별개**: ULightComponent 도 Mobility 보유. Static Light + Static Mesh = 완전 baked, Movable Light + Movable Mesh = 동적.
- **성능 영향**: Static / Stationary = 빠름 (baked). Movable = 동적 lighting + 매 프레임 transform update.
- **Movable 외 Tick 비활성 권장**: Static / Stationary 는 위치 변경 X 이므로 Tick 의 Transform 갱신 불필요.

## 4. 관련 entity

- [[entities/USceneComponent]]
- [[entities/UPrimitiveComponent]]
- [[entities/UStaticMeshComponent]]

## 5. 열린 질문

- [ ] Movable mesh + Stationary light 의 indirect lighting 정확도
- [ ] 5.x Lumen 환경에서 Mobility 의 의미 변화
