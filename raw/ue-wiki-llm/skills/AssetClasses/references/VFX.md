---
name: assetclasses-vfx
description: UNiagaraSystem (5.x Plugin 표준) + UParticleSystem (Cascade legacy) + UVectorField + UNiagaraEffectType (Significance/Cull).
---

# AssetClasses/VFX — UNiagaraSystem + UParticleSystem (legacy) + UVectorField

> **위치**: Plugin (Niagara) `Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraSystem.h` + Engine `Engine/Classes/Particles/ParticleSystem.h` + `VectorField/VectorField.h`
> **베이스**: `UFXSystemAsset : public UObject` → `UNiagaraSystem` (5.x 표준) / `UParticleSystem` (Cascade — legacy)
> **요지**: **모든 VFX 의 자산 트리** — 컴포넌트 (NiagaraComponent / ParticleSystemComponent) 페어. **5.x = Niagara 표준** (Cascade 는 호환만).

---

## 🚨 공통 정책

| 정책 | VFX 자산 적용 |
|------|--------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | **NiagaraSystem 자산 = 매우 큼** (Stack 모듈 + Data Interface + GPU 시뮬). **TSoftObjectPtr<UNiagaraSystem>` + Match Start PreLoad + Pool 표준** (`ENCPoolMethod::AutoRelease`). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | OnSystemFinished / Notify 콜백 첫 줄 스코프. |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | **§5 Niagara Quality Scaling 의무** — UNiagaraEffectType + FNiagaraSystemScalabilitySettings + 품질 레벨 5종 매트릭스 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2) + ENiagaraSignificanceHandling 4종 + Pool (`ENCPoolMethod::AutoRelease`) + Scalability::SetQualityLevels. **모든 NiagaraSystem = EffectType 의무**. |

---

## 1. UNiagaraSystem (5.x 표준)

> **자세한 = [`Niagara/SKILL.md`](../../Niagara/SKILL.md)** (Plugin sub-skill — Component 사용 패턴 포함). 본 §은 자산 측면만.

### 1.1 자산 핵심 구조

```cpp
class UNiagaraSystem : public UFXSystemAsset
{
    // 시스템 Stack — System / Emitter Spawn / Update
    TArray<FNiagaraEmitterHandle> EmitterHandles;

    // System Spawn / Update Script
    UPROPERTY()
    TObjectPtr<UNiagaraScript> SystemSpawnScript;

    UPROPERTY()
    TObjectPtr<UNiagaraScript> SystemUpdateScript;

    // 사전 컴파일 Effect Type
    UPROPERTY()
    TObjectPtr<UNiagaraEffectType> EffectType;
};
```

### 1.2 Effect Type (자산)

```cpp
class UNiagaraEffectType : public UObject
{
    // Significance 통합 — 거리 기반 자동 비활성
    UPROPERTY(EditAnywhere)
    ENiagaraSignificanceHandling SignificanceHandling;

    // Performance Baseline — Cull 기준
    UPROPERTY(EditAnywhere)
    int32 CullCount;

    UPROPERTY(EditAnywhere)
    float CullDistance;
};
```

### 1.3 사용 패턴 (런타임)

```cpp
// 정적 Spawn
UNiagaraComponent* NC = UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, NiagaraSys, Location);
NC->SetVariableFloat(TEXT("SpawnRate"), 100.f);
NC->SetVariableLinearColor(TEXT("Color"), FLinearColor::Red);

// Pool 사용 — 매 프레임 Spawn (발사 / 발자국)
UNiagaraComponent* PooledNC = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    this, NiagaraSys, Location, FRotator::ZeroRotator, FVector::OneVector,
    /*bAutoDestroy=*/ true,
    /*bAutoActivate=*/ true,
    ENCPoolMethod::AutoRelease   // ⭐ 자동 풀
);
```

---

## 2. UParticleSystem (Cascade — Legacy)

```cpp
// Particles/ParticleSystem.h
class UParticleSystem : public UFXSystemAsset
{
    UPROPERTY()
    TArray<TObjectPtr<UParticleEmitter>> Emitters;

    // LOD
    UPROPERTY()
    TArray<float> LODDistances;
};
```

> **⚠️ 5.x 에서 Cascade 는 deprecated 추세** — 신규 VFX 무조건 Niagara. 기존 자산만 호환.

---

## 3. UVectorField (3D 벡터 필드)

```cpp
// VectorField/VectorField.h
class UVectorField : public UObject
{
    // 3D 그리드 데이터 (X/Y/Z Vector)
    int32 SizeX, SizeY, SizeZ;
    FBox Bounds;
};

// 자식 — UVectorFieldStatic (정적) / UVectorFieldAnimated (애니메이션)
```

> **사용** — Niagara Data Interface 또는 Cascade 의 VectorField Module 에서 참조. 바람 / 자기장 / 블랙홀 시뮬.

---

## 4. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 신규 VFX = ParticleSystem (Cascade) | 5.x = Niagara 의무 |
| 2 | NiagaraSystem 매 프레임 Spawn (Pool 안 사용) | `ENCPoolMethod::AutoRelease` 의무 |
| 3 | NiagaraSystem PreLoad 안 함 (큰 자산) | Match Start `PreloadPrimaryAssets` |
| 4 | EffectType 미지정 | Significance / Cull 안 됨 — 모든 NiagaraSystem 의 EffectType 의무 |
| 5 | GPU 시뮬 + Mobile 빌드 안 검증 | Mobile Forward 호환 검사 |
| 6 | NiagaraSystem 의 Data Interface (SkeletalMesh) Hard 참조 | Soft 검토 |
| 7 | OnSystemFinished 콜백 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 8 | 🚨 `TObjectIterator<UNiagaraSystem>` | UAssetManager + AssetRegistry |

---

## 5. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`Niagara/SKILL.md`](../../Niagara/SKILL.md) — Plugin 사용 패턴 (Component + Pool + Stack 모듈)
- [`Components/ParticleComponents`](../../Components/references/ParticleComponents.md) — 호스트 컴포넌트
- 교차: 🎯 [`