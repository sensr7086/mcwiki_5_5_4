---
type: entity
title: "UNiagaraSystem"
aliases: [UNiagaraSystem, NiagaraSystem]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, vfx, plugin]
last_updated: 2026-05-09
---

# UNiagaraSystem

## 요약

Niagara Plugin (5.x VFX 표준) 의 자산 클래스. **Stack 모듈** (System / Emitter / Particle Spawn / Update) + Data Interface 9 종 (SkeletalMesh / StaticMesh / PhysicsAsset / Curve / VolumeTexture / RenderTarget2D / CollisionQuery / Audio / ParticleRead). GPU vs CPU SimTarget. ENCPoolMethod (AutoRelease 표준). USignificanceManager 통합. UNiagaraComponent 가 호스트.

## 관계

- 부모: [[entities/UObject]]
- 페어 호스트: UNiagaraComponent (UFXSystemComponent 자손)
- 협력 자산: UNiagaraEmitter (System 안의 Emitter), Data Interface 9종 (SkeletalMesh 의 Bone 위치 sample 등)
- 5.x 표준: 신규 VFX = Niagara 의무. Cascade (UParticleSystem) 는 호환만.

## 핵심 주장

- Stack 구조: System (Emitter 컨테이너) → Emitter (Particle 생성/업데이트 그룹) → Module (스크립트화된 동작).
- SimTarget 2 종: CPUSim (게임 스레드) / GPUSim (Compute Shader, 다수 입자 표준).
- Data Interface 9 종: 외부 데이터를 Niagara 에 노출. SkeletalMesh DI 로 Bone 위치 sampling, Curve DI 로 시간별 값, RenderTarget2D 로 GPU 텍스처 — Niagara 의 강력함의 핵심.
- ENCPoolMethod (AutoRelease 표준): UNiagaraComponent 풀링 — 일회성 VFX 의 Component 객체 자동 회수. 다수 spawn 환경 (총알 hit, 폭발) 표준.
- USignificanceManager 통합: NiagaraEffectType 의 Significance / Cull — 거리별 자동 비활성화. [[concepts/Asset-Optimization-Policy]]
- 5.x 의 신규 VFX 는 무조건 Niagara. Cascade 는 마이그레이션 / 호환 목적만.

## 열린 질문

- [ ] GPU Sim 의 Compute Shader 디버깅 (RenderDoc 통합)
- [ ] Cascade → Niagara 마이그레이션 표준 절차
