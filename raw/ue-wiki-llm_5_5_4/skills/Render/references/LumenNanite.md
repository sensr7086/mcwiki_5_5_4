---
name: render-lumennanite
description: 5.x 신규 — Lumen (동적 GI / Reflection) + Nanite (Virtualized Geometry) + GPU Scene + Mesh Shader. 활성화 / 호환성 / 디버그 / 성능 매트릭스 + Mobile/Console 호환. 5.x 게임의 시각 품질 핵심.
---

# Render/LumenNanite — 5.x 신규 기술 (Lumen + Nanite + GPU Scene)

> **위치**: `Engine/Source/Runtime/Renderer/` (Lumen / Nanite 통합) + Project Settings / Console Vars
> **요지**: UE 5.x 의 **시각 혁신 2축** — Lumen (라이팅) + Nanite (지오메트리). 호환성 / 활성화 / 디버그 표준.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 호환성 검사 | 5.x 신규 — 모든 Custom Render 코드 = Lumen / Nanite 호환 검사 의무 |
| 🚨 Mobile / Console | Lumen / Nanite = PC High-End 우선. Mobile 비활성 / Console 부분 지원 |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | Nanite 호환 = StaticMesh 표준. Skeletal Mesh = 5.4+ 부분 지원 |

---

## 1. Lumen (동적 GI / Reflection)

### 1.1 정의
- 동적 Global Illumination + Reflection
- Hardware Ray Tracing (DX12) 또는 Software Ray Tracing (SDF Mesh)
- Pre-baked Lightmap 대체

### 1.2 활성화

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.DynamicGlobalIlluminationMethod=1     ; 1 = Lumen
r.ReflectionMethod=1                     ; 1 = Lumen Reflection
r.Lumen.HardwareRayTracing=1             ; HWRT 활성 (DX12)
r.Lumen.HardwareRayTracing.Inline=1      ; Inline RT
```

### 1.3 Lumen 호환 매트릭스

| 항목 | Lumen 호환 | 비고 |
|------|----------|------|
| Static Mesh + DefaultLit | ✅ | 표준 |
| Skeletal Mesh | ⚠️ | Hit Proxy = SDF Card 만 (정확도 ↓) |
| Translucent Material | ❌ | Lumen 영향 X |
| Custom HLSL | ⚠️ | Material Domain 정확 시 OK |
| Foliage (Instanced) | ✅ | InstancedStaticMesh OK |
| Procedural Mesh | ❌ | Distance Field 미지원 |
| Mobile | ❌ | 미지원 |

### 1.4 Lumen 디버그

```
콘솔 명령:
ShowFlag.LumenSurfaceCacheDirectLighting   - Lumen Surface Cache 시각화
ShowFlag.LumenSceneCardCapture              - Card Capture 시각화
r.Lumen.Visualize 1                         - Lumen 시각화 모드
ShowFlag.VisualizeLumenScene                - Lumen Scene 시각화
```

### 1.5 함정

```
1. Lumen 활성 + Custom Material = Lumen 캡처 누락 (Material 측 검사)
2. Translucent + Lumen = 영향 X (반투명은 별도 처리)
3. Skeletal Mesh + Lumen = SDF Card 정확도 낮음 (Static Mesh 우선)
4. Mobile = Lumen 비활성 → Lightmap fallback 의무
5. 5.x HWRT 의 GPU 부담 = ~10~20% 추가 (저사양 기기 비활성)
```

---

## 2. Nanite (Virtualized Geometry)

### 2.1 정의
- 수백만 폴리곤 자동 LOD
- GPU 측 메시 컬링 + 클러스터 기반
- Pre-baked LOD 0 만 작성 → 자동 LOD 처리

### 2.2 활성화

```cpp
// 1. UStaticMesh 측
StaticMesh->NaniteSettings.bEnabled = true;
StaticMesh->NaniteSettings.PercentTriangles = 1.0f;
StaticMesh->NaniteSettings.FallbackTriangleCount = 5000;   // Fallback Mesh

// 2. Project Settings
r.Nanite=1                                ; 전역 활성
r.Nanite.AsyncRasterization=1             ; 비동기 래스터
```

### 2.3 Nanite 호환 매트릭스

| 항목 | Nanite 호환 | 비고 |
|------|-----------|------|
| Static Mesh | ✅ | 표준 |
| Foliage (InstancedStaticMesh) | ✅ | 5.x 표준 |
| Hierarchical InstancedStaticMesh (HISM) | ✅ | OK |
| Skeletal Mesh | ⚠️ | 5.4+ 부분 (제한적) |
| Custom Vertex Factory | ❌ | GPU Scene 호환 필요 |
| Translucent Material | ❌ | Nanite 미지원 |
| Two-sided Material | ❌ | Nanite 미지원 |
| Mobile | ❌ | 미지원 |
| World Position Offset (WPO) | ⚠️ | 제한적 |

### 2.4 Fallback Mesh

```
Nanite 비활성 환경 (Mobile / GPU 부족):
- Static Mesh 의 LOD 0 = Nanite 데이터
- Fallback = LOD 1 또는 별도 Fallback Mesh
- FallbackTriangleCount = 자동 데시메이션 (5000 권장)
```

### 2.5 Nanite 디버그

```
ShowFlag.Nanite                          - Nanite 메시 시각화
r.Nanite.Visualize                        - 다양한 시각화 모드
r.Nanite.MaxNodes                         - GPU 한계 조정
r.Nanite.Fallback                         - Fallback 표시
```

---

## 3. GPU Scene (5.x — Lumen / Nanite 의 베이스)

### 3.1 정의
모든 Primitive 의 Transform / Material / Bounds 를 GPU 측 단일 버퍼로 통합.

### 3.2 영향

```
- CPU 측 명령 수 ↓ (per-Primitive 명령 회피)
- Per-View Culling = GPU 측에서 (CPU 부담 ↓)
- Custom Vertex Factory = GPU Scene 호환 의무
- Lumen / Nanite 동작 베이스
```

### 3.3 활성화 (자동)

```ini
r.GPUSkinCache.Enable=1                  ; Skin Cache
r.GPUSkin.Limit2BoneInfluences=0
```

---

## 4. 5.x Mesh Shader (DX12)

### 4.1 정의
DX12 Mesh Shader Pipeline = Vertex / Geometry Shader 후속. Compute-friendly.

### 4.2 사용
```
- Nanite = 내부적으로 Mesh Shader 사용 (자동)
- Custom Mesh Shader = 5.x 부터 가능 (드물게 사용)
```

---

## 5. 호환성 결정 매트릭스 (시나리오별)

| 시나리오 | Lumen | Nanite | 권고 |
|---------|-------|--------|------|
| AAA 게임 (PC High-End) | ✅ | ✅ | Lumen + Nanite 활성 |
| AAA 게임 (Console) | ⚠️ | ✅ | Nanite 활성 / Lumen Software (HWRT 비활성) |
| Mobile 게임 | ❌ | ❌ | Lightmap + LOD 0/1/2 (Legacy) |
| VR 게임 (Quest 등) | ❌ | ❌ | Mobile 모드 |
| 실내 인테리어 (정적) | ⚠️ | ✅ | Static Lighting + Nanite |
| MOBA / RPG (Skeletal Mesh 다수) | ⚠️ | ⚠️ | Lumen Software / Skeletal Nanite 5.4+ |
| 절차 생성 (Procedural Mesh) | ❌ | ❌ | Legacy 사용 |

---

## 6. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Lumen 활성 + Mobile 빌드 | Mobile = Lumen 비활성 의무 (Lightmap fallback) |
| 2 | Nanite + Translucent / Two-sided Material | Material 측 호환 검사 |
| 3 | Custom Vertex Factory + Nanite | GPU Scene 호환 의무 또는 Nanite 비활성 |
| 4 | Nanite Skeletal Mesh (5.3 이전) | 5.4+ 만 부분 지원 — 사용 X |
| 5 | Lumen Reflection + 거대 Translucent | Lumen 영향 X — 별도 SSR 사용 |
| 6 | r.Nanite=0 인데 NaniteSettings.bEnabled = true | 동시 적용 — Project Settings 와 페어 |
| 7 | Lumen Surface Cache 메모리 부족 | r.LumenScene.SurfaceCache.MaxMeshCardsPerComponent 조정 |
| 8 | Cooked Build 안 Lumen 비활성 (이상 동작) | Cooked Setting 검증 |
| 9 | HWRT 미지원 GPU + r.Lumen.HardwareRayTracing=1 | Software RT fallback 또는 비활성 |
| 10 | Custom PostProcess + Lumen 결과 사용 시 Hook 잘못 | PrePostProcessPass_RenderThread 표준 |

---

## 7. 체크리스트

- [ ] Lumen / Nanite Project Setting 정확
- [ ] Material Domain = Lumen / Nanite 호환 검사
- [ ] Skeletal Mesh + Nanite = 5.4+ 만 사용
- [ ] Custom Vertex Factory = GPU Scene 호환 또는 Nanite 비활성
- [ ] Mobile = Lumen / Nanite 모두 비활성 + Lightmap fallback
- [ ] Console = Lumen Software 또는 부분 활성
- [ ] HWRT 미지원 GPU = Software RT fallback 검증
- [ ] Cooked Build 안 활성 검증
- [ ] Lumen Surface Cache 메모리 검증
- [ ] Custom PostProcess + Lumen 결과 = Hook 시점 정확

---

## 8. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/MeshDrawing.md`](../MeshDrawing/SKILL.md) — GPU Scene 호환
- [`Render/references/Material.md`](../Material/SKILL.md) — Material Domain 호환
- [`Render/references/PostProcess.md`](../PostProcess/SKILL.md) — Lumen 결과 사용 PostProcess
- [`AssetClasses/references/Mesh.md`](../../AssetClasses/references/Mesh.md) — UStaticMesh Nanite 설정

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. **5.x Lumen + Nanite + GPU Scene + Mesh Shader** + 호환성 매트릭스 (PC/Console/Mobile/VR) + Fallback + 디버그 명령 + 함정 10대. |
