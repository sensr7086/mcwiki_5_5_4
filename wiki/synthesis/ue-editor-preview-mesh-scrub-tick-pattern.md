---
type: synthesis
title: "UE Editor — PreviewMesh Scrub-driven Tick Pattern (3축 명시 Tick override)"
slug: ue-editor-preview-mesh-scrub-tick-pattern
created: 2026-05-19
last_updated: 2026-05-19
project_role: knowledge-pattern
project: cross-project
sources:
  - "[[sources/ue-editor-advancedpreviewscene]]"
  - "[[sources/ue-editor-personatoolkit]]"
  - "[[sources/ue-animation-animinstance]]"
entities:
  - "[[entities/SWidget]]"
concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
status: living
tags: [synthesis, ue-editor, preview-scene, debugskelmesh, animsinglenodeinstance, scrub, tick-override, kmcproject-verified, sequencer-lite, silent-fail-trap]
citation_disclosure: "🟢 8 (Engine source 직접 인용 + KMCProject Phase 5a 실측 검증)"
---

# UE Editor — PreviewMesh Scrub-driven Tick Pattern (3축 명시 Tick override)

> **One-liner**: Editor PreviewScene 안 `UDebugSkelMeshComponent` 에 scrub-driven (사용자 시간 입력) preview 를 구현할 때 `SetPosition` 만 호출하면 *silent fail* — Slate Tick override 안 `World->Tick` + `TickAnimation` 3축 명시 호출 의무.

## 1. 문제 — Silent Fail

```cpp
// ❌ Anti-pattern — 빌드 성공, 에러 0, 로그 0, 그러나 mesh 정지
PreviewMeshComponent->SetSkeletalMesh(...);
PreviewMeshComponent->SetAnimationMode(EAnimationMode::AnimationSingleNode);
PreviewMeshComponent->SetAnimation(Montage);
PreviewMeshComponent->Stop();                              // = SetPlaying(false)
PreviewMeshComponent->SetPosition(Time, /*bFireNotifies=*/false);  // ← 시간만 갱신, pose 미갱신
```

scrub UI 가 매 frame `SetPosition(NewTime)` 호출하지만 mesh 는 정지.

## 2. Engine 권위 — Editor world Tick 조건

### 2.1 `SetPosition` 의 한계

`Source/Runtime/Engine/Private/Animation/AnimSingleNodeInstance.cpp` L354-396 `SetPositionWithPreviousTime`:
```cpp
FAnimSingleNodeInstanceProxy& Proxy = GetProxyOnGameThread<FAnimSingleNodeInstanceProxy>();
Proxy.SetCurrentTime(FMath::Clamp<float>(InPosition, 0.f, GetLength()));
// ↑ Proxy 시간만 갱신. Pose 재평가는 별도 Tick 경유 의무.
```

### 2.2 SkeletalMeshComponent Editor 분기

`Source/Runtime/Engine/Private/Components/SkeletalMeshComponent.cpp`:

```cpp
bool ShouldUpdateTransform(bool bLODHasChanged) const  // L1682
{
    if (GetWorld()->WorldType == EWorldType::Editor) {
        if (bUpdateAnimationInEditor) return true;     // L1689
        // ...
        return bLODHasChanged;                          // ← default false 시 SKIP
    }
}

bool ShouldTickPose() const                             // L1718
{
    if (GetWorld()->WorldType == EWorldType::Editor) {
        if (bUpdateAnimationInEditor) return true;     // L1732
    }
}
```

→ **Editor world** 안 `bUpdateAnimationInEditor=false` (default) 시 transform/pose tick 양쪽 SKIP.

### 2.3 `FAdvancedPreviewScene` WorldType 함정

`FPreviewScene` 의 기본 WorldType 은 `EWorldType::EditorPreview` — *not* `EWorldType::Editor`. 위 두 함수의 `EWorldType::Editor` 분기에 진입 *안 함* → `bUpdateAnimationInEditor` 플래그가 무효한 경우가 있음 → **명시 Tick 호출이 더 안전**.

### 2.4 Persona scrub 기준 패턴

`Source/Editor/Persona/Private/SAnimationScrubPanel.cpp`:
- L385: `PreviewInstance->SetPosition(NewValue, bFireNotifies)` — 시간 set
- L760-790 `SetPlaybackMode(Stopped)`: `SetPlaying(false)` — auto-advance off

Persona 는 별도 PreviewScene Tick path (PersonaToolkit 내부) 가 World tick + AnimInstance tick 보장하므로 SetPosition 만으로 충분.
**자체 SEditorViewport 자손에서는 본 path 가 없으므로 명시 호출 필수**.

## 3. 표준 패턴 — 3축 명시 Tick override

```cpp
// .h
class SMyPreviewSceneViewport : public SEditorViewport
{
public:
    virtual void Tick(const FGeometry&, const double InCurrentTime, const float InDeltaTime) override;
    // ... 기타 ...
};

// .cpp
void SMyPreviewSceneViewport::Tick(const FGeometry& AllottedGeometry,
                                    const double InCurrentTime,
                                    const float InDeltaTime)
{
    // ⭐ 1축 — Slate base Tick (SCompoundWidget 자손 의무)
    SEditorViewport::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);

    // ⭐ 2축 — Preview World 전체 tick (Light/Sky/Floor + 모든 component)
    if (PreviewScene.IsValid() && PreviewScene->GetWorld())
    {
        PreviewScene->GetWorld()->Tick(LEVELTICK_All, InDeltaTime);
    }

    // ⭐ 3축 — AnimInstance 명시 tick (SetPosition 이후 pose 재평가 보장)
    if (PreviewMeshComponent)
    {
        PreviewMeshComponent->TickAnimation(InDeltaTime, /*bNeedsValidRootMotion=*/false);
    }
}
```

### 3.1 각 축의 역할

| 축 | API | 효과 |
| -- | -- | -- |
| 1 | `SEditorViewport::Tick` (= `SCompoundWidget::Tick`) | Slate framework 가 매 frame 자동 호출 — override 진입점 |
| 2 | `UWorld::Tick(LEVELTICK_All, DeltaTime)` | Preview World 의 모든 actor/component tick — light/sky/floor 등 시각 일관성 |
| 3 | `USkeletalMeshComponent::TickAnimation(DeltaTime, false)` | AnimInstance 명시 tick → `Proxy.CurrentTime` 기반 pose evaluate → mesh 시각 갱신 |

## 4. 대안 — `SetUpdateAnimationInEditor(true)` (Fallback)

```cpp
#if WITH_EDITOR
    PreviewMeshComponent->SetUpdateAnimationInEditor(true);
#endif
```

**한계**:
- `EWorldType::Editor` 분기에 의존 — `EditorPreview` WorldType 시 무효
- 암묵적 동작 — explicit 검증 어려움
- FAdvancedPreviewScene 가 자체 tick path 안 돌 경우 fallback 불가

**권장**: Tick override 가 1순위. SetUpdateAnimationInEditor 는 보조 (양쪽 모두 적용 — defense-in-depth).

## 5. 함정 매트릭스

| # | 함정 | 정답 |
| -- | -- | -- |
| PS01 ⭐⭐⭐ | `UDebugSkelMeshComponent::SetPosition` 만 호출 → silent fail (시간만 갱신, pose 미갱신) | Slate Tick override 안 `World->Tick` + `TickAnimation` 3축 명시 |
| PS02 ⭐⭐ | `SetUpdateAnimationInEditor(true)` 만 의존 → FAdvancedPreviewScene 의 `WorldType=EditorPreview` 분기 시 무효 | Tick override 우선, 플래그는 보조 |
| PS03 ⭐ | Persona 패턴 (SetPosition + SetPlaying(false)) 그대로 모방 → Persona 의 별도 Tick path 없으면 무동작 | 자체 SEditorViewport 자손 시 명시 Tick 의무 |
| PS04 🟡 | `World->Tick(LEVELTICK_All)` 누락 → mesh 외 light/sky/floor 정지 | Tick override 안 World->Tick 의무 (시각 일관성) |

## 6. 검증 사례 — KMCProject MCComboEditor Phase 5a (2026-05-19)

- 파일: `Source/KMCProject/MCEditorModule/MCComboEditor/SMCComboPreviewSceneViewport.h/.cpp`
- 증상: Timeline scrub drag → SyncToScrubFrame → SetPosition 정상 호출, 그러나 PreviewMesh 정지
- 1차 진단 (vault read): `SetUpdateAnimationInEditor(true)` 권고 — 부분 fix
- 2차 진단 (사용자 검증): Tick override 3축 명시 — 완전 fix
- 검증: ✅ Timeline scrub drag / Play / Prev/Next / Section drag / Diamond drag 모두 mesh pose 실시간 갱신

## 7. Cross-link

- [[sources/ue-editor-advancedpreviewscene]] — FAdvancedPreviewScene 표준 + WorldType
- [[sources/ue-editor-personatoolkit]] §함정 — Trap-PS01/PS02 추가 필요
- [[sources/ue-animation-animinstance]] — UAnimSingleNodeInstance::SetPosition signature + AnimInstance::TickAnimation
- [[synthesis/mc-combo-editor-levelsequence-lite]] §Phase 5a — case study (Sequencer-lite Preview tick)

## 8. 후속 검증 후보

- [ ] `PreviewScene->GetWorld()->Tick` vs `FPreviewScene::Tick` (FPreviewScene 가 자체 Tick override 보유 시 중복 호출 위험) — Engine source 확인 후 분기
- [ ] LEVELTICK_All vs LEVELTICK_TimeOnly vs LEVELTICK_ViewportsOnly 선택 기준 (현재 All — 최대 안전)
- [ ] bNeedsValidRootMotion 파라미터 영향 매트릭스 — root motion 있는 Montage scrub 시 결과 차이
