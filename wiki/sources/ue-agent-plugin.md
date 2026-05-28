---
type: source
title: "UE Plugin Specialist — GAS + Niagara + Significance 통합"
slug: ue-agent-plugin
source_path: raw/ue-wiki-llm/agents/ue-plugin-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UAttributeSet]]"
  - "[[entities/UNiagaraComponent]]"
  - "[[entities/USignificanceManager]]"
tags: [ue, agent, specialist, gas, niagara, significance, plugin, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Plugin Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-plugin-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[GAS]` / `[Niagara]` / `[Significance]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 GAS / Niagara / Significance 통합 전문가. MOBA / RPG / 다수 NPC / VFX 작업. **GAS 5종 핵심 클래스** + **Niagara 5.x VFX 표준** + **Significance Manager 거리 LOD**.

## 2. 자동 로드 (작업별)

- **GAS**: `skills/GAS/SKILL.md` + [[sources/ue-ref-07-profilingscopeRule]]
- **Niagara**: `skills/Niagara/SKILL.md` + [[sources/ue-ref-12-assetoptimizationpolicy]] §5
- **Significance**: `skills/Significance/SKILL.md` + [[sources/ue-components-meshcomponents]] §7

## 3. GAS — MOBA / RPG / 멀티플레이 표준

### 5종 핵심 클래스

- `UAbilitySystemComponent` — Actor 컴포넌트 (Pawn 또는 PlayerState)
- `UAttributeSet` — Health / Mana / Damage 어트리뷰트
- `UGameplayAbility` — 어빌리티 (스킬)
- `FGameplayEffect` — 어트리뷰트 변경 (데미지 / 버프)
- `FGameplayTag` — 분류 / 상태

### 결정 매트릭스

| 항목 | 옵션 | 결정 기준 |
|------|------|---------|
| **호스트** | Pawn vs PlayerState | Map 전환 살아남음? = PlayerState / 단일 Map = Pawn |
| **ReplicationMode** | Full / Mixed / Minimal | Full=싱글 / Mixed=ARPG / Minimal=MOBA |
| **InstancingPolicy** | NonInstanced / PerActor / PerExecution | 단순 = NonInstanced / 상태 = PerActor |
| **NetExecutionPolicy** | LocalPredicted (표준) / ServerInitiated / ServerOnly / LocalOnly | Predict 가능? = LocalPredicted |

### 표준 패턴

```cpp
// MOBA 모델 (PlayerState 호스트)
class AMyPS : public APlayerState, public IAbilitySystemInterface
{
    UPROPERTY() TObjectPtr<UAbilitySystemComponent> AbilitySystem;
    UPROPERTY() TObjectPtr<UMyAttributeSet> Attributes;
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override { return AbilitySystem; }
};

// Pawn — InitAbilityActorInfo (Owner=PlayerState, Avatar=Pawn)
void AMyChar::PossessedBy(AController* C) {
    Super::PossessedBy(C);
    if (auto* PS = GetPlayerState<AMyPS>())
        PS->GetAbilitySystemComponent()->InitAbilityActorInfo(PS, this);
}
```

## 4. Niagara — 5.x VFX 표준 (Cascade Legacy)

### 핵심 5종

- `UNiagaraComponent` (UFXSystemComponent 자손)
- `UNiagaraSystem` (자산)
- Stack 모듈 (System / Emitter / Particle / Spawn / Update)
- Data Interface 9종
- `UNiagaraEffectType` (Significance / Cull)

### 표준 사용 — Pool + AutoRelease

```cpp
UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    World, NiagaraSystem, Location, Rot, FVector(1.0f),
    /*bAutoDestroy=*/ false,
    /*bAutoActivate=*/ true,
    ENCPoolMethod::AutoRelease   // ⭐ 5.x 표준
);
```

→ **모든 NiagaraSystem = `UNiagaraEffectType` 지정 의무**. 품질 5종 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2 SpawnCountScale).

## 5. Significance — 다수 NPC 표준

```cpp
void AMyAI::BeginPlay() {
    Super::BeginPlay();
    if (auto* Sig = USignificanceManager::Get<USignificanceManager>(GetWorld())) {
        Sig->RegisterObject(this, TEXT("AIChar"),
            [](FManagedObjectInfo* I, const FTransform& V) {
                FVector L = Cast<AActor>(I->GetObject())->GetActorLocation();
                return FMath::InvSqrt(FVector::DistSquared(L, V.GetLocation()));
            },
            EPostSignificanceType::Sequential,
            [](FManagedObjectInfo* I, float O, float N, bool) {
                auto* C = Cast<AMyAI>(I->GetObject());
                if (N > 0.5f) C->SetTickInterval(0.f);
                else if (N > 0.1f) C->SetTickInterval(0.1f);
                else C->SetTickInterval(1.f);
            });
    }
}
```

## 6. Baseline Grep 의무

함정 키워드: `UAbilitySystemComponent` / `UAttributeSet` / `UGameplayAbility` / `FGameplayEffect` / `FGameplayTag` / `UNiagaraComponent` / `ENCPoolMethod::AutoRelease` / `USignificanceManager` / `FManagedObjectInfo`.

## 7. 거부 조건

- 일반 Component / Actor — 다른 specialist
- UMG / Slate — `ue-slate-umg-specialist`
- Editor 도구 — `ue-editor-specialist`

## 8. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-gameframework]] (Pawn vs PlayerState) · [[sources/ue-agent-animation]] (Niagara + Anim 페어)
- sub-skill: [[sources/ue-gas-skill]] · [[sources/ue-niagara-skill]] · [[sources/ue-significance-skill]]
- 정책 페어: [[sources/ue-ref-12-assetoptimizationpolicy]] §5 (Niagara Quality)
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 9 절. GAS 5종 + 결정 매트릭스 + Niagara Pool/EffectType + Significance |
