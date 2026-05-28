---
type: synthesis
title: "KMCProject 캐릭터 피격/사망 표준 시퀀스 — Soft 자산 비동기 로드 + Ragdoll + PhysAnim + Hit Direction + Validation Policy + Hit Bone Curve 통합"
slug: mc-character-hit-reaction-pipeline
created: 2026-05-10
last_updated: 2026-05-14
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-components-physicscomponents]]"
  - "[[sources/ue-assetclasses-mesh]]"
  - "[[sources/ue-assetclasses-assetuserdata]]"
  - "[[sources/ue-components-primitivecomponent]]"
  - "[[sources/ue-components-charactermovementdeep]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
  - "[[sources/ue-editor-propertyeditor]]"
  - "[[sources/ue-editor-toolmenus]]"
  - "[[sources/ue-editor-personatoolkit]]"
  - "[[sources/ue-editor-asseteditorapi]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/ACharacter]]"
concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
status: living
tags: [synthesis, kmcproject, ragdoll, physanim, validation, hit-reaction, hit-bone-curve, additive-transform, on-register-tabs-delegate, ue-macro-identifier-collision]
---

# KMCProject 캐릭터 피격/사망 표준 시퀀스

## 1. Thesis

KMCProject 의 모든 SkeletalMesh 캐릭터는 `UMCSoftSkeletalMeshComponent` 를 호스트로 한다. 이 컴포넌트는 **(1) Mesh + AnimClass + PhysicsAsset + Materials 모두 `TSoftObjectPtr` 비동기 로드** ([[concepts/Soft-Reference-vs-Hard]]) 로 SpawnActor 4단 히칭 회피, **(2) `OnHitReceived(Bone, Dir, Strength, Profile, bFull)` 한 호출에 ragdoll 활성 + PhysAnim 본별 모터 + 방향성 임펄스를 묶음** ([[sources/mc-soft-skeletalmesh-ragdoll]] §9.3), **(3) 모든 silent return 가드를 [[concepts/MC-Asset-Validation-Policy]] 의 LOG 19 + ensure 1 로 가시화**. ⭐ **§6 Hit Bone Curve 시스템 (Phase 1+2+4+dangling fix+Cycle 5b+Phase 5 Preview)** — `UMCHitBoneCurveUserData` 가 SkeletalMesh 의 AssetUserData 로 부착되어 본별 hit additive transform 커브 제공 → Hit reaction 모션 다양화.

## 2. 3 단계 파이프라인 매트릭스

### 2.1 Setup (BeginPlay)

| 단계 | 호출 | 정책 |
| -- | -- | -- |
| 1 | `Super::BeginPlay()` | [[sources/ue-ref-04-overrideindex]] §6.1 — Super FIRST |
| 2 | `CachedOwner = GetOwner()` (1회) | [[concepts/Component-Policies-6]] §4 |
| 3 | `RequestLoadAsync()` — Mesh + AnimClass + Materials 한 핸들 묶음 | [[concepts/Asset-Loading-Policy]] §2 단계 5 + Pin |
| 4 | `EnsurePhysicalAnimationComponent()` (bAuto=true) | `HasBegunPlay()` ensure 페어 ([[concepts/MC-Asset-Validation-Policy]] (B)) |
| 5 ⭐ | `UMCHitBoneCurveUserData* HitCurveData = Mesh->GetAssetUserData<UMCHitBoneCurveUserData>();` | §6 — Hit Bone Curve 시스템 진입점 (nullable — 디자이너 미설정 가능) |

### 2.2 Hit (gameplay-driven)

| 시나리오 | 진입점 | 내부 절차 |
| -- | -- | -- |
| 본 + 방향 알 때 | `OnHitReceived(Bone, Dir, Strength, Profile, bFull)` | Mesh 검증 → Ragdoll → MotorProfile + Fade → Dir+UpwardBias → ApplyHitImpulse → **(Phase 3 후속) HitCurveData->SampleAdditiveTransform(Bone, TimeSec, Dir, Strength)** |
| `FHitResult` 그대로 | `OnHitFromResult(Hit, ...)` | `Hit.BoneName` 비면 `FindClosestBone(bRequiresPhysicsAsset=true)`, 방향=`-ImpactNormal` |
| 폭발 / 광역 | `EnableFullRagdoll() + ApplyRadialHitImpulse(Origin, R, S)` | RIF_Linear / RIF_Constant |
| 본별 모터만 (idle 흔들림) | `ApplyMotorProfileBelow(Bone, Profile)` | Profile + SetSimulate 페어 자동 |
| ⭐ **본별 additive 모션** (Phase 3) | `HitCurveData->SampleAdditiveTransform(Bone, TimeSec, Dir, Strength)` | §6 — UCurveVector 어셋 (X=Pitch, Y=Yaw, Z=Roll) sample + DirectionInfluence yaw 가중 |

### 2.3 Cleanup (Death cooldown / Disable)

| 단계 | 호출 | 정책 |
| -- | -- | -- |
| 1 | `RagdollLoadHandle->CancelHandle()` | [[concepts/Asset-Loading-Policy]] §2 단계 5 — 도착 후 재활성 회피 |
| 2 | `SetSimulatePhysics(false)` + `SetAllBodiesSimulatePhysics(false)` | |
| 3 | `SetConstraintProfileForAll(NAME_None, true)` | [[sources/ue-assetclasses-physics]] §3 — Default 복원 |
| 4 | 콜리전 / AnimClass 복원 (캐싱된 값) | `bRestoreAnimClassOnDisable` |
| 5 | (optional) `SnapMeshToOwnerCapsule()` — Capsule 위치로 본 snap-back | ACharacter 면 Capsule, 일반 Actor 면 Root |
| 6 | `OnRagdollStateChanged.Broadcast(this, false)` | |

## 3. 시나리오별 호출 사례

**시나리오 A — 적 NPC 가슴 피격 (가장 흔함)**

```cpp
const FVector HitDir = (Target - Attacker->GetActorLocation()).GetSafeNormal();
EnemyMesh->OnHitReceived(TEXT("spine_03"), HitDir);   // 기본 Strength + "HitReaction" Profile + 부분 ragdoll
```

**시나리오 B — 사망 (강한 일격)**

```cpp
EnemyMesh->OnHitReceived(TEXT("pelvis"), HitDir * 2.f, 2000.f, NAME_None, /*bUseFullRagdoll=*/true);
```

**시나리오 C — 충돌 콜백 그대로**

```cpp
void AEnemy::OnComponentHit(UPrimitiveComponent* HitComp, AActor* Other, ..., const FHitResult& Hit)
{
    EnemyMesh->OnHitFromResult(Hit, Damage * 30.f);
}
```

**시나리오 D — 폭발 (광역)**

```cpp
EnemyMesh->EnableFullRagdoll();
EnemyMesh->ApplyRadialHitImpulse(BombOrigin, 500.f, 3000.f, RIF_Linear);
```

**시나리오 E — Idle 본별 흔들림 (Hit 없이 모터만)**

```cpp
FPhysicalAnimationData Data;
Data.bIsLocalSimulation = true; Data.OrientationStrength = 200.f;
Mesh->ApplyMotorSettingsBelow(TEXT("spine_03"), Data);
Mesh->FadeMotorStrength(0.3f);
```

**시나리오 F — Hit Curve 기반 본별 additive 모션 (Phase 3 후속)** ⭐

```cpp
// AnimNotify 또는 Tick 안 호출 — Hit 후 N 초간 본별 additive transform 합성
const FTransform AdditiveT = HitCurveData->SampleAdditiveTransform(
    /*Bone=*/ TEXT("spine_03"),
    /*TimeSec=*/ TimeSinceHit,
    /*HitDirection=*/ HitDir,
    /*ExternalStrength=*/ 1.5f);

// AnimGraph 측에서 ApplyAdditive 노드 또는 BoneController 가 적용
// 본 데이터 — UCurveVector (X=Pitch, Y=Yaw, Z=Roll) + Duration + IntensityScale + DirectionInfluence
```

## 4. 함정 / 열린 질문

- [ ] **#1 SetSimulatePhysics 페어 누락** ([[sources/ue-assetclasses-mesh]] §7 #6) — `OnHitReceived` 가 `EnableFull/PartialRagdoll` 선행으로 회피
- [ ] **#9 Constructor 안 PhysAnim Apply** ([[sources/ue-components-physicscomponents]] §11 #7) — 본 컴포넌트 *유일한 ensure 사이트* 인 `EnsurePhysicalAnimationComponent` 의 `HasBegunPlay()`
- [ ] **#11 시뮬 안 된 본에 AddImpulse** — `OnHitReceived` 가 ragdoll 활성 후 임펄스
- [ ] **#15 평면 피격** — `HitUpwardBias` 기본 0.25 로 Z 보강
- [ ] AnimMontage GetUp 시퀀스 — [[concepts/Inertialization]] 결합 후 별도 노트 (열린)
- [ ] 멀티플레이 — Ragdoll cosmetic-only vs Authority replicate 결정 ([[sources/ue-networking-skill]] 검토 필요, 열린)
- [ ] PhysAnim Profile 별 데이터 시트 — "HitReaction" / "DeathHard" / "DeathSoft" 표준 (열린)
- [ ] 멀티 본 동시 피격 누적 — `OnHitReceived` 가 한 본 가정 (열린)
- [ ] §6 Phase 3 — `OnHitReceived` 안 `HitCurveData` 호출 통합 (열린 — 후속 작업)

## 5. 관련

(생략 — 변경 없음, sources/entities/concepts/synthesis cross-link 유지)

## 6. ⭐ Hit Bone Curve 시스템 — UMCHitBoneCurveUserData (Phase 1~5, 2026-05-13~14)

### 6.1 목적

Hit reaction 모션 *다양화* — 본 별 + 본 위치 별 *additive rotation 커브* 로 미세한 모션 차이 부여. 데이터 = 디자이너 편집 (UCurveVector 어셋). 런타임 = `SampleAdditiveTransform` 한 호출.

### 6.2 클래스 구조 (재설계 2026-05-14)

```cpp
USTRUCT(BlueprintType)
struct FMCHitBoneAdditiveCurve
{
    UPROPERTY(EditAnywhere) FName BoneName;
    UPROPERTY(EditAnywhere) float Duration = 0.3f;
    UPROPERTY(EditAnywhere) float IntensityScale = 1.0f;
    UPROPERTY(EditAnywhere) float DirectionInfluence = 0.5f;

    // ⭐ UCurveVector 어셋 1개 — X=Pitch / Y=Yaw / Z=Roll (degrees)
    UPROPERTY(EditAnywhere, meta=(DisplayName="Rotation Curve Asset (X=Pitch, Y=Yaw, Z=Roll, degrees)"))
    TObjectPtr<UCurveVector> RotationCurves = nullptr;

    FTransform SampleAtTime(float TimeSec, const FVector& OptionalHitDirection) const;
};

UCLASS(BlueprintType, DefaultToInstanced, EditInlineNew, CollapseCategories)
class MCPLAYMODULE_API UMCHitBoneCurveUserData : public UAssetUserData
{
    UPROPERTY(EditAnywhere, meta=(TitleProperty="BoneName"))
    TArray<FMCHitBoneAdditiveCurve> BoneCurves;

    UPROPERTY(EditAnywhere) float GlobalScale = 1.0f;
    /* BP API + Editor only IsDataValid + 라이프사이클 Reserve(256) — vault §6.5 함정 페어 */
};
```

### 6.3 Phase 진화 매트릭스 (2026-05-13 ~ 2026-05-14)

| Phase | 작업 | 산출물 | 검증 |
| -- | -- | -- | -- |
| **Phase 1** (2026-05-13) | UAssetUserData 데이터 구조 | `MCHitBoneCurveUserData.h/cpp` | ✅ |
| **Phase 2 + 2a + 2b** (2026-05-13) | Persona dock + Focus 추적 + IStructureDetailsView | `SMCHitBoneCurveEditor.h/cpp` + `MCHitBoneCurveEditorMenu.h/cpp` | ⚠ Window 메뉴 불완전 (Cycle 5b 에서 fix) |
| **Phase 3** | (보류) 런타임 OnHitReceived 통합 | `MCSoftSkeletalMeshComponent` 측 | — |
| **Phase 4** (2026-05-13) | Editor Validation (IsDataValid + Validate/Cleanup UI) | `MCHitBoneCurveUserData::IsDataValid` + Toolbar 버튼 | ✅ |
| **Dangling fix** (2026-05-14) | SCurveEditor 0xFF...FF crash — IStructureDetailsView 매번 재생성 + Reserve(256) | §6.5 함정 7 | ✅ |
| ⭐⭐⭐ **Cycle 5b** (2026-05-14) | Persona Window 메뉴 — ToolMenus 폐기 → `FPersonaModule::OnRegisterTabs` + `FWorkflowTabFactory` + EnableTabPadding + Layout cache 정리 | `MCHitBoneCurveEditorMenu` 완전 마이그레이션 | ✅ |
| ⭐ **재설계** (2026-05-14) | UCurveVector 어셋 + Rotation only (Translation 제거) | `FMCHitBoneAdditiveCurve.RotationCurves` | ✅ |
| ⭐ **Phase 5 Preview** (2026-05-14) | Persona PreviewMesh 미리보기 — Play/Stop UI + 매 tick `SetBoneRotationByName` | `SMCHitBoneCurveEditor::HandlePreviewPlay/Stop/OnPreviewTick` | 🟡 빌드 fix 완료 검증 대기 |

### 6.4 Persona Window 메뉴 통합 — Cycle 5b 정정 표준 (2026-05-14)

**이전 (Phase 2, 폐기)**: ToolMenus `ExtendMenu` × 5 후보 fallback — 모두 stub.
**현재 (Cycle 5b, 정답)**: `FPersonaModule::OnRegisterTabs` delegate + `FWorkflowTabFactory` 자손.

→ 상세 코드 vault [[sources/ue-editor-personatoolkit]] §2.7.

### 6.5 함정 매트릭스 (13건) — KMCProject 검증 카탈로그 ⭐

| # | 함정 | 회피 | log | vault |
| -- | -- | -- | -- | -- |
| 1 | UINTERFACE meta `CannotImplementInterfaceInBlueprint="false"` — Blueprint Event 멤버 + interface mismatch | `UINTERFACE(MinimalAPI, Blueprintable, BlueprintType)` | `[2026-05-13] feature` 1차 + 2차 재현 | [[sources/ue-coreuobject-interface]] §5 #1 |
| 2 | C2355 `'this'` — static BPFunction 안 `MC_LOGRET_*` 매크로 사용 | file-local `MCSP_LOGRET_*` 매크로 우회 | `[2026-05-13] feature` | [[sources/mc-asset-validation-policy]] §6 |
| 3 ⭐⭐⭐ | C4264 name hiding — `IsDataValid()` 무인자 BP 헬퍼 vs UObject `IsDataValid(FDataValidationContext&)` | 이름 변경 `HasValidBoneCurves()` + Phase 4 override | `[2026-05-13] fix` | [[sources/ue-coreuobject-uobject]] §2.8 |
| 4 | C1083 `IAssetEditorInstance.h` 미존재 | include 제거 — UE 5.x 별도 헤더 없음 | `[2026-05-13] fix` | [[sources/ue-editor-personatoolkit]] §2.3 |
| 5 ⭐⭐⭐ | C2440 const propagation — `IsDataValid` const 메서드 안 `const USkeletalMesh*->GetSkeleton()` 의 const 오버로드 → const 변수 의무 | `const USkeleton* Skeleton = ...` | `[2026-05-14] fix` | [[sources/ue-coreuobject-uobject]] §2.10 |
| 6 | Persona Window 메뉴 ToolMenus 5 후보 fallback (원인 B = TabManager 자체) | Cycle 5b 정답 = `FPersonaModule::OnRegisterTabs` (함정 8) | `[2026-05-13]` → `[2026-05-14]` | [[sources/ue-editor-toolmenus]] §2.7 |
| 7 ⭐⭐⭐ | SCurveEditor 0xFF...FF dangling pointer — IStructureDetailsView 내부 SCurveEditor stale | SBox + IStructureDetailsView 매번 재생성 + Reserve(256) | `[2026-05-14] fix` | [[sources/ue-editor-propertyeditor]] §2.8 + [[sources/ue-coreuobject-uobject]] §2.11 |
| 8 ⭐⭐⭐ | AssetEditor Window 메뉴 = TabManager 자체 시스템 (ToolMenus 외) | `FPersonaModule::OnRegisterTabs` (Persona) / `FLevelEditorModule` (LevelEditor) | `[2026-05-14] fix` Cycle 5b | [[sources/ue-editor-toolmenus]] §2.9 + [[sources/ue-editor-asseteditorapi]] §11 |
| 9 ⭐ | 외부 모듈 `Toolkit->GetEditingObjects()` C2248 protected | `Toolkit->GetObjectsCurrentlyBeingEdited()` public, nullable | `[2026-05-14] fix` | [[sources/ue-editor-personatoolkit]] §2.7.9 |
| 10 ⭐⭐⭐ | `EnableTabPadding()` 호출 누락 — FWorkflowTabFactory 6요소 표준 어김 → 메뉴 미표시 | Persona 표준 6요소 미러 — TabLabel/Icon/**EnableTabPadding**/bIsSingleton/ViewMenuDesc/Tooltip | `[2026-05-14] fix` | [[sources/ue-editor-personatoolkit]] §2.7.5 |
| 11 ⭐⭐ | Editor Layout cache 잔재 — 신규 TabFactory 등록되어도 첫 실행 메뉴 미표시 | Window > Reset Layout 또는 `EditorLayout.ini` 삭제 | `[2026-05-14] fix` | [[sources/ue-editor-personatoolkit]] §2.7.10 |
| **12** ⭐⭐⭐ **신규** ⭐ | **UE 매크로 reserved 식별자 변수 이름 충돌 (C2059)** — `auto* PI = ...` 의 `PI` 가 `#define PI 3.1415926535...` 매크로 치환 → "구문 오류: 상수" | 변수 이름에 *UE 글로벌 매크로 식별자 회피* — `_PreviewInstance` 같이 underscore prefix 또는 명시적 이름 (`AnimPI` 등) | `[2026-05-14] fix` 사용자 직접 진단 | §6.5.12 (아래 매트릭스) |
| **13** ⭐ **신규** | `UCLASS(MinimalAPI)` 외부 모듈 type 직접 사용 — vault 잘못된 진단 (실제 진짜 함정은 #12) | 폐기 — 함정 12 가 진짜 원인 | (잘못된 진단, 자체 평가 후 폐기) | — |

→ ⭐ **자체 평가 (Article 1 Evaluator)**: 함정 13 (`MinimalAPI`) 은 *잘못된 진단* 이었음. 진짜 원인 = 함정 12 (`PI` 매크로). 사용자가 직접 진단 + fix (`auto* PI` → `auto* _PreviewInstance` 변수 이름 변경) 후 vault 정정. 가설 (`MinimalAPI`) 폐기 + 진짜 원인 (UE macro pollution) 등록.

#### 6.5.12 ⭐⭐⭐ UE 글로벌 매크로 reserved 식별자 매트릭스 (2026-05-14 신규)

`Engine/Source/Runtime/Core/Public/Math/UnrealMathUtility.h` 가 글로벌 헤더 — 모든 cpp 가 transitive include. 다음 매크로가 *모든 변수 이름* 충돌:

| 매크로 | 정의 | 위치 | 충돌 위험 |
| -- | -- | -- | -- |
| `PI` | `(3.1415926535897932f)` | UnrealMathUtility.h L65/L129 | ⭐⭐⭐ 매우 흔함 (변수 PI / pi / Pi 도 매크로 치환) |
| `INV_PI` | `(0.31830988618f)` | L79/L150 | ⭐ |
| `HALF_PI` | `(1.57079632679f)` | L80/L151 | ⭐ |
| `TWO_PI` | `(6.28318530717f)` | L81/L152 | ⭐ |
| `SMALL_NUMBER` | `(1.e-8f)` | L66/L130 | ⭐⭐ |
| `KINDA_SMALL_NUMBER` | `(1.e-4f)` | L67/L131 | ⭐⭐ |
| `BIG_NUMBER` | (UE_BIG_NUMBER) | L68 | ⭐ |
| `EULERS_NUMBER` | (UE_EULERS_NUMBER) | L69 | ⭐ |
| `MAX_FLT` | (UE_MAX_FLT) | L78 | ⭐ (FLT_MAX std 와 다름) |
| `DELTA` | (Math 측 작은 값) | UnrealMathUtility | ⭐ |
| `CHECK` / `check` | (assert macro) | Build.h | ⭐⭐⭐ (변수 이름 `check` 사용 시 silent macro pollution) |

⭐ **회피 규약** — 모든 KMCProject cpp 안 변수/매개변수 이름에 위 매크로 식별자 사용 금지. 회피 패턴:

```cpp
// ❌ C2059 — 매크로 치환
auto* PI = Mesh->PreviewInstance;
float Pi = 3.14f;
int32 SMALL_NUMBER = 1;

// ✅ 회피 — underscore prefix 또는 도메인 명시
auto* _PreviewInstance = Mesh->PreviewInstance;        // ⭐ KMCProject 채용 (2026-05-14)
auto* AnimPI = Mesh->PreviewInstance;                  // 도메인 prefix
float MyPi = 3.14f;
int32 LocalSmallNumber = 1;
```

KMCProject 검증 (2026-05-14):
- `SMCHitBoneCurveEditor.cpp` 의 `auto* PI = Mesh->PreviewInstance.Get()` — C2059
- fix → `auto* _PreviewInstance = Mesh->PreviewInstance.Get()` — 빌드 통과

→ 진단 함정 — 가설 `UCLASS(MinimalAPI)` 막힘 으로 잘못 추정 (함정 13). 진짜 원인 = 글로벌 매크로 식별자 충돌. *사용자가 직접 진단* (vault 잘못 가이드).

#### 6.5.13 vault 일반화 후보 (Cycle 5d)

⭐ 신규 vault page `[[sources/ue-build-cpp-pitfalls]]` 또는 기존 `[[sources/ue-coreuobject-skill]]` §UE 매크로 식별자 카탈로그 — 위 §6.5.12 매트릭스 정식 등록.

### 6.6 관련 vault 페이지

- [[sources/ue-assetclasses-assetuserdata]] §2.10 — UAssetUserData 자손 IsDataValid 5.x 패턴
- [[sources/ue-coreuobject-uobject]] §2.7-2.11 — UObject virtual + C4264 + IsDataValid 5.x + C2440 + FStructOnScope TArray reallocation
- [[sources/ue-editor-toolmenus]] §2.7-2.9 — ExtendMenu stub + RegisterStartupCallback + TabManager 자체 시스템
- [[sources/ue-editor-personatoolkit]] §2.3-2.5 + §2.7 — IAssetEditorInstance.h + OnAssetEditorOpened + FPersonaModule::OnRegisterTabs + EnableTabPadding + Layout cache
- [[sources/ue-editor-asseteditorapi]] §11 — TabManager Window 메뉴 + OnRegisterTabs 매트릭스 + protected vs public
- [[sources/ue-editor-propertyeditor]] §2.8 — IStructureDetailsView 매번 재생성
- [[sources/mc-asset-validation-policy]] §6 + §11 — static-friendly 매크로 + const-correctness 체크리스트
- [[sources/ue-assetclasses-mesh]] §3 — USkeletalMesh::GetSkeleton const 오버로드
- [[synthesis/instanced-subobject-customization-bypass]] §4.3 — Tab Spawner 패턴

### 6.7 Phase 5 Preview — UAnimPreviewInstance vs SetBoneRotationByName (2026-05-14)

이전 시도 (UAnimPreviewInstance::ModifyBone): C2059 발생 → 잘못된 진단으로 폐기.
진짜 원인 (PI macro) 확정 후 다시 검토 — UAnimPreviewInstance 사용 *가능* (변수 이름만 `_PreviewInstance` 로 변경).

현재 KMCProject 코드 = USkeletalMeshComponent::SetBoneRotationByName (사용자 진행 중인 우회). 작동하면 OK. 추후 UAnimPreviewInstance::ModifyBone 복원 가능 (vault `[[sources/ue-editor-personatoolkit]]` §2.4 PoseModifier 시스템 표준).
