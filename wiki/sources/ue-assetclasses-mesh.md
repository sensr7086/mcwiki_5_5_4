---
type: source
title: "UE AssetClasses — Mesh sub-skill"
slug: ue-assetclasses-mesh
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Mesh.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B priority audit
related_entities:
  - "[[entities/UStaticMesh]]"
  - "[[entities/USkeletalMesh]]"
related_concepts:
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, asset, mesh, const-overload, c2440]
---

# UE AssetClasses — Mesh sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Mesh.md]]
> Parent: [[sources/ue-assetclasses-skill]]
> 보강 2026-05-14 — §3 USkeletalMesh::GetSkeleton const/non-const 오버로드 표 + C2440 함정

## 1. Summary

[[entities/UStaticMesh]] (2,543) + [[entities/USkeletalMesh]] (3,248) + USkeleton (1,037) + UPhysicsAsset (444). 5.x Nanite + Compatible Skeleton + Virtual Bones + Ragdoll + LOD chain. ⭐ **§3 const 오버로드** — `GetSkeleton` / `GetPhysicsAsset` 등 const 메서드 안 호출 시 자동 const propagation (KMCProject 2026-05-14 검증).

## 2. Key claims

- StaticMesh: RenderData (vertex/index buffer BulkData) + LOD chain (ScreenSize) + Material slots + 5.x Nanite (활성 시 LOD 무관 virtualized geo).
- SkeletalMesh: Skeleton 의존 + LODRenderData + Skin Weights + UPhysicsAsset (Ragdoll).
- Skeleton: FReferenceSkeleton (본 계층). Compatible Skeletons (5.x) — 다른 Skeleton 의 모션 재사용. Virtual Bones (5.x) — 런타임 가상 본.
- [[concepts/Bone-LOD]]: USkeletalMeshLODSettings + BonesToRemove (LOD 별 제거) + BonesToPrioritize (강제 보존).
- UPhysicsAsset: Ragdoll 표현 — 본별 SimplePrimitive (Capsule / Box / Sphere) + Constraint.
- Material slots: Mesh default + Component override (SetMaterial(Index, Material)).
- BulkData (DDC): Cooked 빌드 시 플랫폼별 변환 (compressed mesh data). [[concepts/BulkData]] · [[concepts/Cooked-vs-Uncooked]].

## 3. ⭐ USkeletalMesh / UStaticMesh const 오버로드 매트릭스 (2026-05-14 추가) 🟢

### 3.1 USkeletalMesh::GetSkeleton 오버로드

`Engine/Source/Runtime/Engine/Classes/Engine/SkeletalMesh.h` — 2 오버로드:

```cpp
class USkeletalMesh : public USkinnedAsset
{
public:
    /** 비-const 객체용 — modify 가능한 참조 반환 */
    USkeleton*       GetSkeleton();

    /** const 객체용 — 읽기 전용 참조 반환 */
    const USkeleton* GetSkeleton() const;
};
```

→ const 객체의 메서드 호출 시 **자동 const 오버로드** 호출 (오버로드 해상도) → `const USkeleton*` 반환.

### 3.2 const 컨텍스트에서 호출 매트릭스

| 컨텍스트 | OwnerMesh 타입 | GetSkeleton 호출 | 받는 변수 타입 |
| -- | -- | -- | -- |
| 비-const 메서드 (예: `PostEditChangeOwner`) | `USkeletalMesh*` | 비-const 오버로드 | `USkeleton*` |
| const 메서드 (예: `IsDataValid` const) | `const USkeletalMesh*` | const 오버로드 | `const USkeleton*` 의무 |
| const-cast 강제 | `const_cast<USkeletalMesh*>(...)` | 비-const 오버로드 | `USkeleton*` (❌ 권장 안 함) |

⭐ **함정**: const 컨텍스트에서 `USkeleton* X = OwnerMesh->GetSkeleton();` 작성 시 C2440 — `'const USkeleton *'에서 'USkeleton *'(으)로 변환할 수 없습니다`.

### 3.3 USkeletalMesh 의 다른 const 오버로드 함수

| 함수 | 비-const 반환 | const 반환 | 호출 빈도 |
| -- | -- | -- | -- |
| `GetSkeleton()` | `USkeleton*` | `const USkeleton*` | ⭐⭐⭐ 매우 흔함 |
| `GetPhysicsAsset()` | `UPhysicsAsset*` | `const UPhysicsAsset*` | ⭐⭐ Ragdoll 컴포넌트 |
| `GetRefSkeleton()` (deprecated 5.x — `GetSkeleton()->GetReferenceSkeleton()` 사용) | — | — | (deprecated) |
| `GetImportedModel()` | `FSkeletalMeshModel*` | `const FSkeletalMeshModel*` | ⭐ Editor only (`WITH_EDITORONLY_DATA`) |
| `GetResourceForRendering()` | `FSkeletalMeshRenderData*` | `const FSkeletalMeshRenderData*` | ⭐ Render thread |
| `GetMaterials()` | `TArray<FSkeletalMaterial>&` | `const TArray<FSkeletalMaterial>&` | ⭐⭐ Material slot 조회 |
| `GetLODInfoArray()` | `TArray<FSkeletalMeshLODInfo>&` | `const TArray<FSkeletalMeshLODInfo>&` | ⭐ LOD 조회 |

### 3.4 UStaticMesh 의 const 오버로드 함수

| 함수 | 비-const 반환 | const 반환 | 호출 빈도 |
| -- | -- | -- | -- |
| `GetRenderData()` | `FStaticMeshRenderData*` | `const FStaticMeshRenderData*` | ⭐⭐ Render thread |
| `GetSourceModel(int32 LODIndex)` | `FStaticMeshSourceModel&` | `const FStaticMeshSourceModel&` | ⭐ Editor only |
| `GetStaticMaterials()` | `TArray<FStaticMaterial>&` | `const TArray<FStaticMaterial>&` | ⭐⭐ Material slot 조회 |
| `GetBodySetup()` | `UBodySetup*` | `const UBodySetup*` | ⭐ Collision 조회 |

### 3.5 KMCProject 검증 사례 (2026-05-14)

```cpp
// MCHitBoneCurveUserData.cpp — IsDataValid 는 const 메서드
EDataValidationResult UMCHitBoneCurveUserData::IsDataValid(FDataValidationContext& Context) const
{
    if (const USkeletalMesh* OwnerMesh = Cast<USkeletalMesh>(GetOuter()))   // const Cast (const-correctness)
    {
        // ❌ C2440 — 비-const USkeleton* 변수
        // if (USkeleton* Skeleton = OwnerMesh->GetSkeleton()) { ... }

        // ✅ const USkeleton* 받기
        if (const USkeleton* Skeleton = OwnerMesh->GetSkeleton())
        {
            const FReferenceSkeleton& RefSkel = Skeleton->GetReferenceSkeleton();   // const 메서드 호출 — 자동 const 받음
            // ...
        }
    }
}
```

빌드 에러 (수정 전):

```
MCHitBoneCurveUserData.cpp(266,27): error C2440: '초기화 중':
  'const USkeleton *'에서 'USkeleton *'(으)로 변환할 수 없습니다.
```

log: `[2026-05-14] fix | C2440 fix — USkeletalMesh::GetSkeleton() const 오버로드 const USkeleton* 반환`.

### 3.6 const 메서드 안 작성 체크리스트

```cpp
EDataValidationResult UMyData::IsDataValid(FDataValidationContext& Context) const
{
    // ✅ const Cast — const-correctness 의무
    if (const USkeletalMesh* Mesh = Cast<USkeletalMesh>(GetOuter()))
    {
        // ✅ const 받기 — propagate
        if (const USkeleton* Skeleton = Mesh->GetSkeleton())
        {
            // ✅ const 메서드만 호출
            const int32 NumBones = Skeleton->GetReferenceSkeleton().GetNum();
            const FName BoneName = Skeleton->GetReferenceSkeleton().GetBoneName(0);
        }

        if (const UPhysicsAsset* PA = Mesh->GetPhysicsAsset())
        {
            // ✅ const 메서드만 호출
        }

        // ✅ Context modify 는 허용 — Context 는 비-const 참조
        Context.AddError(LOCTEXT("Foo", "Bar"));
    }
    return EDataValidationResult::Valid;
}
```

### 3.7 함정 / 안티패턴

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | const 메서드 안 `USkeleton* X = Mesh->GetSkeleton()` | `const USkeleton* X = ...` (자동 const propagate) |
| 2 | `const_cast<USkeleton*>(Mesh->GetSkeleton())` | 금지 — Engine 의도 우회 |
| 3 | `GetRefSkeleton()` 직접 호출 (deprecated 5.x) | `GetSkeleton()->GetReferenceSkeleton()` |
| 4 | Render thread 에서 `GetResourceForRendering()` 비-const 호출 | const 한정 의무 — Render thread 안 modify 금지 |
| 5 | `GetMaterials()` 비-const 반환을 비-const 컨텍스트에서 modify | 의도적 — 비-const 컨텍스트 (예: PostEditChangeProperty) 만 허용 |

## 4. 함정 (USkeletalMesh / UStaticMesh 공통)

- [[concepts/Bone-LOD]] 설정 누락 → 다수 NPC 시 본 행렬 비용 폭발
- Compatible Skeleton 의 Virtual Bone 적용 시 retarget 미고려
- StaticMesh Nanite 비활성 + Legacy LOD 누락 → 모바일/저사양 시 fragment shader 비용
- UPhysicsAsset 의 Constraint 가 본 계층과 불일치 → Ragdoll 부자연

## 5. Cross-link

### 페어 카테고리

- [[sources/ue-components-meshcomponents]] (호스트 컴포넌트 — UStaticMeshComponent / USkeletalMeshComponent)
- [[sources/ue-components-skill]] (Components 카테고리 main)

### Related concepts

- [[concepts/Bone-LOD]] · [[concepts/Asset-Optimization-Policy]] · [[concepts/BulkData]] · [[concepts/Cooked-vs-Uncooked]]

### Related sources

- [[sources/ue-coreuobject-uobject]] §2.10 — UObject 측 const propagation 일반 함정 (본 §3 의 베이스)
- [[sources/mc-asset-validation-policy]] §11 — KMCProject Validation 메서드 작성 시 const-correctness 체크리스트
- [[sources/ue-assetclasses-assetuserdata]] §2.10 — UAssetUserData 자손 IsDataValid 패턴 (KMCProject Phase 4)

### Related fix log

- `[2026-05-14] fix | C2440 fix — USkeletalMesh::GetSkeleton() const 오버로드 const USkeleton* 반환` — §3.5 1차 검증


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-render-lumennanite]] (inbound=3, suggest_missing_cross_link high confidence)
## 6. Open questions

- [ ] Nanite 활성 vs Legacy LOD 결정 트리 (모바일 / 저사양)
- [ ] Compatible Skeleton 5.x 의 retarget 동작
- [ ] §3.4 UStaticMesh const 오버로드 매트릭스 — 실제 Engine source 라인 인용 (현재는 5.x 일반 패턴 기반 — 향후 검증)
- [ ] §3.5 KMCProject 검증 매트릭스 확장 — `UMCPartsLoaderComponent` / `UMCSoftSkeletalMeshComponent` 안 const 컨텍스트 검증

## 7. 신뢰도 매트릭스 (3-tier)

| 영역 | tier | 근거 |
| -- | -- | -- |
| §2 USkeletalMesh / UStaticMesh / USkeleton / UPhysicsAsset 베이스 | 🟢 | UE Wiki raw 인용 |
| §3.1 GetSkeleton 2 오버로드 | 🟢 | SkeletalMesh.h 표준 패턴 + KMCProject 빌드 검증 (2026-05-14) |
| §3.2 const 컨텍스트 매트릭스 | 🟢 | C++ 표준 + KMCProject C2440 검증 |
| §3.3 / §3.4 다른 const 오버로드 매트릭스 | 🟡 | 일반 패턴 추정 — 일부 함수 시그니처 미인용 |
| §3.5 KMCProject 검증 사례 | 🟢 | log entry `[2026-05-14] fix` + 코드 인용 |
| §3.6 체크리스트 | 🟢 | KMCProject 적용 검증 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 변경 0 / 추가 0 / 제거 0 — 단순 수치 또는 미세 변경만. 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/Mesh.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/Mesh.md]]
