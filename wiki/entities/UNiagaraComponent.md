---
type: entity
title: "UNiagaraComponent"
aliases: [UNiagaraComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, runtime, components, vfx, plugin]
last_updated: 2026-05-09
---

# UNiagaraComponent

## 요약

UFXSystemComponent 자손 (Niagara Plugin). **5.x VFX 표준** 의 호스트 — [[entities/UNiagaraSystem]] 자산 참조 + 런타임 인스턴싱 + GPU/CPU SimTarget. ENCPoolMethod (AutoRelease 표준) 으로 일회성 VFX 자동 풀링. USignificanceManager 통합으로 거리 기반 자동 비활성화.

## 관계

- 부모: UFXSystemComponent → [[entities/UPrimitiveComponent]] → [[entities/USceneComponent]]
- 페어 자산: [[entities/UNiagaraSystem]] (필수)
- 협력: USignificanceManager (Significance/Cull)

## 핵심 주장

- ENCPoolMethod (AutoRelease 표준): 일회성 VFX (총알 hit / 폭발) 의 Component 자동 회수. 직접 NewObject 금지. 다수 spawn 환경 표준.
- SpawnSystemAtLocation / SpawnSystemAttached: UNiagaraFunctionLibrary 의 표준 spawn API.
- Variable 동적 변경: `SetNiagaraVariableFloat` / `SetNiagaraVariableVec3` 등 — 시스템 외부에서 파라미터 주입.
- Significance 통합: NiagaraEffectType 의 Cull 설정으로 거리별 자동 비활성. [[concepts/Asset-Optimization-Policy]] 의 5번 영역.
- Cascade (UParticleSystemComponent) 와 비교: 신규 VFX = 무조건 Niagara, Cascade 는 호환만.

## 열린 질문

- [ ] ENCPoolMethod 의 풀 size 자동 조정
- [ ] Niagara DataInterface 9종 의 Component 측 셋업 패턴
