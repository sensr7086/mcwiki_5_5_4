---
type: synthesis
title: "VFX/Audio Soft 참조 + Pool + Significance 통합 패턴 — Niagara/SoundCue/MetaSound/DataAsset 비동기 골격"
slug: vfx-audio-soft-pool-significance
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-assetclasses-vfx]]"
  - "[[sources/ue-assetclasses-audio]]"
  - "[[sources/ue-assetclasses-audio-metasound]]"
  - "[[sources/ue-components-particlecomponents]]"
  - "[[sources/ue-components-audiocomponent]]"
  - "[[sources/mc-asset-validation-policy]]"
entities:
  - "[[entities/UNiagaraSystem]]"
  - "[[entities/UNiagaraComponent]]"
  - "[[entities/USoundBase]]"
  - "[[entities/USignificanceManager]]"
concepts:
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, niagara, audio, soft, pool, significance]
---

# VFX/Audio Soft 참조 + Pool + Significance 통합 패턴

## 1. Thesis

VFX (Niagara) 와 Audio (SoundCue / MetaSound) 자산은 *대량 / 짧은 수명 / 동시 다발* 의 특성으로 [[synthesis/mc-soft-asset-component-pattern]] 의 Soft 골격에 더해 **(1) Pool (`ENCPoolMethod::AutoRelease` / Audio Voice Pool) + (2) Significance 거리 deactivate + (3) DataAsset 묶음 사전 로드** 의 3 축이 추가로 필요하다. 본 synthesis 는 Niagara / SoundCue / MetaSound / DataAsset 4 가지 자산을 같은 골격으로 처리하는 Helper Component 설계 + 결정 트리.

## 2. 4 자산 매트릭스

| 자산 | Soft 타입 | UE Setter / Spawn | Pool 옵션 | Significance 통합 |
| -- | -- | -- | -- | -- |
| `UNiagaraSystem` | `TSoftObjectPtr<UNiagaraSystem>` | `UNiagaraFunctionLibrary::SpawnSystemAttached` + `PoolingMethod=AutoRelease` | ✓ ([[sources/ue-niagara-skill]] §6) | EffectType + Significance Tag |
| `USoundCue` | `TSoftObjectPtr<USoundBase>` | `UGameplayStatics::SpawnSoundAttached` (자동 voice 관리) | Voice Concurrency (자동) | Attenuation + Concurrency + Significance |
| `USoundBase` (MetaSound) | `TSoftObjectPtr<USoundBase>` | 동일 + Source Effect Chain | 동일 | 동일 |
| `UDataAsset` (Bundle 묶음) | `TSoftObjectPtr<UMyEffectBundle>` | `UAssetManager::PreloadPrimaryAssets` + Bundle | 자체 Pool 없음 (메타데이터만) | Bundle 단위 Significance |

## 3. 통합 골격 (Helper Component)

```cpp
UCLASS(ClassGroup=(MC), meta=(BlueprintSpawnableComponent))
class UMCSoftEffectComponent : public USceneComponent
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TSoftObjectPtr<UNiagaraSystem> SoftVFX;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) TSoftObjectPtr<USoundBase>      SoftSound;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FName SignificanceTag = TEXT("Effect.Default");
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float MaxDistance = 5000.f;

    UFUNCTION(BlueprintCallable) void PlayAt(const FTransform& WorldXfm);

protected:
    virtual void BeginPlay() override;
    void RegisterSignificance();
    void OnSignificanceUpdate(float Score);
private:
    TSharedPtr<FStreamableHandle> LoadHandle;
    TWeakObjectPtr<UNiagaraComponent> ActiveVFX;
    TWeakObjectPtr<UAudioComponent>   ActiveSound;
};
```

`PlayAt` 호출 시:
1. Soft 미로드면 [[concepts/Asset-Loading-Policy]] §2 단계 5 비동기 → 콜백에서 spawn
2. Niagara = `SpawnSystemAtLocation(System, Loc, Rot, Scale, /*bAutoDestroy=*/true, /*PoolingMethod=*/ENCPoolMethod::AutoRelease)`
3. Audio = `UGameplayStatics::SpawnSoundAtLocation` (자동 voice 풀)
4. Significance manager 등록 — score < threshold 면 `Deactivate`

## 4. Significance + Pool 결정 트리

```
이 효과의 빈도 / 비용?
├── 자주 발생 + 작은 비용 (총알 임팩트, 풋스텝)
│   └── Pool 의무 (AutoRelease) + Significance 거리 컷 (예: 2000 cm)
├── 가끔 + 큰 비용 (폭발, 보스 스킬)
│   └── Pool optional + Significance 거리 컷 큼 (10000 cm)
├── 항상 (캐릭터 트레일 / 환경 ambient)
│   └── Pool 불필요 (life 길음) + Significance Bucket 분리 (Update 주기 길게)
└── 배경 / 대규모 (불꽃놀이)
    └── Pool 의무 + Niagara EffectType Quality Scaling ([[sources/ue-niagara-skill]] §Quality)
```

[[sources/ue-significance-skill]] §3 의 *score 함수는 단순 거리* 표준 + Tag 별 Bucket — VFX / Audio 별도 Bucket 구성.

## 5. DataAsset Bundle 묶음 사전 로드

게임 시작 시 자주 쓰는 효과 묶음 — `UMyEffectBundle : UPrimaryDataAsset` 안 `TArray<TSoftObjectPtr<UNiagaraSystem>>` + `TArray<TSoftObjectPtr<USoundBase>>` 정의. Match Start 에서:

```cpp
UAssetManager& AM = UAssetManager::Get();
TArray<FPrimaryAssetId> Bundles = { FPrimaryAssetId(TEXT("EffectBundle"), TEXT("PlayerCombat")) };
AM.LoadPrimaryAssets(Bundles, {TEXT("Game")}, FStreamableDelegate::CreateLambda([](){
    UE_LOG(LogMCAsset, Log, TEXT("Combat effect bundle loaded"));
}));
```

이러면 `UMCSoftEffectComponent::PlayAt` 호출 시 Soft `Get() != nullptr` 즉시 적용 — 첫 사용 히칭 0.

## 6. 함정 / 열린 질문

- [ ] **Pool 풀 부족 시 fallback** — `PoolingMethod=AutoRelease` + Pool 한도 초과 시 spawn 거절. `UNiagaraComponentPool::SetWorldParticleSystemPoolSettings` 로 한도 조정
- [ ] **Audio Concurrency 그룹** — Voice 한도 초과 시 가장 오래된 voice cull. Concurrency Asset 으로 그룹 정의 ([[sources/ue-assetclasses-audio]])
- [ ] **Significance score 매 프레임 계산 비용** — 50 효과 × 매프레임 score 호출. Bucket Update Rate 조정 (예: VFX bucket = 4 프레임마다)
- [ ] **MetaSound 의 PostLoad 비용** — MetaSound Graph 컴파일 비용. Bundle PreLoad 의무 ([[sources/ue-assetclasses-audio-metasound]])
- [ ] **Niagara GPU vs CPU** — GPU emitter 는 spawn 후 GPU 메모리 할당 — 첫 spawn 히칭 가능. PSO Precache + 사전 1회 spawn 으로 warm-up ([[synthesis/cooked-first-frame-stability]])
- [ ] **DataAsset Bundle 의 Hard 참조 cascade** — Bundle 안 `TSoftObjectPtr` 가 아닌 `TObjectPtr` 면 Bundle 로드 시 모든 자산 hard cascade. *항상 Soft* (열린)
- [ ] **DLC 효과 Bundle** — DLC 가 새 EffectBundle 추가 시 PrimaryAssetId 자동 등록? Cooker 설정 + AssetManager 재스캔 (열린, [[synthesis/cooked-first-frame-stability]])

## 7. 관련

### Sources

[[sources/ue-niagara-skill]] · [[sources/ue-significance-skill]] · [[sources/ue-assetclasses-vfx]] · [[sources/ue-assetclasses-audio]] · [[sources/ue-assetclasses-audio-metasound]] · [[sources/ue-components-particlecomponents]] · [[sources/ue-components-audiocomponent]] · [[sources/mc-asset-validation-policy]]

### Entities

[[entities/UNiagaraSystem]] · [[entities/UNiagaraComponent]] · [[entities/USoundBase]] · [[entities/USignificanceManager]]

### Concepts

[[concepts/Soft-Reference-vs-Hard]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Asset-Optimization-Policy]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/mc-soft-asset-component-pattern]] (Soft 골격 베이스) · [[synthesis/character-many-npc-5-fold-optimization]] (Significance 통합 — NPC + VFX 같은 매니저) · [[synthesis/cooked-first-frame-stability]] (Bundle PreLoad + PSO)
