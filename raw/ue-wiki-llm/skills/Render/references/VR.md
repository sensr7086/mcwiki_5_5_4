---
name: render-vr
description: VR 렌더링 — Stereo Rendering (Multi-View / Instanced Stereo) + Foveated Rendering + OpenXR + Quest/Vive/Index. 90fps/120fps 유지 + 양안 동기 + Reprojection + Mobile VR (Quest) 추가 제약.
---

# Render/VR — Stereo + Foveated + OpenXR + Quest/Vive

> **위치**: `Engine/Plugins/Runtime/OpenXR/` + `Engine/Plugins/Runtime/OculusVR/` (5.x deprecated, OpenXR 통합) + `Engine/Source/Runtime/Renderer/`
> **요지**: VR 렌더링 = **양안 동시 렌더 + 90/120fps 유지 + Foveated Rendering + Mobile VR 제약**. 일반 Render 대비 추가 의무 다수.

---

## 🚨 공통 정책

| 정책 | VR 적용 |
|------|--------|
| 🚨 90fps 의무 | Quest 2/3 = 72/90fps / Index = 120fps / PC = 90~120fps. **30fps 떨어지면 멀미** |
| 🚨 양안 동기 | Stereo Pass = 양쪽 눈 동시 렌더 (Multi-View / Instanced Stereo) |
| 🚨 Reprojection 의무 | 프레임 드롭 시 Reprojection (Quest) — 시스템 자동 |
| 🚨 Mobile VR (Quest) | Mobile Forward + Lumen/Nanite 비활성 + PSO Cache 의무 |

---

## 1. VR 표준 — OpenXR (5.x 통합)

### 1.1 OpenXR (5.x 표준)
- 모든 VR HMD 추상 (Quest / Vive / Index / WMR / PSVR2)
- 5.x = OculusVR / SteamVR Plugin Deprecated → OpenXR 통합

```ini
; DefaultEngine.ini
[/Script/Engine.HMDPluginSettings]
DefaultPlugin=OpenXR

; OpenXR 활성
[/Script/HeadMountedDisplay.HeadMountedDisplay]
bUseOpenXR=true
```

### 1.2 5.x deprecated VR Plugins
- ❌ OculusVR (5.4+ 제거)
- ❌ SteamVR (5.4+ 제거)
- ✅ OpenXR (모든 HMD 통합)
- ✅ Meta XR (Quest 전용 — OpenXR 위에 추가 기능)

---

## 2. Stereo Rendering 모드 3종

### 2.1 Standard Stereo (가장 호환)
- 양쪽 눈 = 별도 패스 (2x DrawCalls)
- 호환성 ↑ / 비용 ↑

### 2.2 Instanced Stereo (PC 표준)
- 양쪽 눈 = 단일 Instance Draw (1x DrawCalls)
- 메모리 ↑ (Vertex Shader 분기)
- 활성: `vr.InstancedStereo=1`

### 2.3 Multi-View (Mobile VR 표준)
- Quest / Mobile = Multi-View Extension (Vulkan / OpenGL ES)
- 5.x — Multi-View Extension 자동
- 활성: `vr.MobileMultiView=1`

```ini
[/Script/Engine.RendererSettings]
vr.InstancedStereo=1                  ; PC VR 표준
vr.MobileMultiView=1                  ; Mobile VR (Quest)
vr.MobileMultiViewDirect=1            ; Direct Multi-View (Quest 2/3)
```

---

## 3. Foveated Rendering (5.x 표준)

### 3.1 정의
- 중앙 = 풀 해상도 / 주변부 = 저해상도
- GPU 비용 절감 (30~50%)
- Eye Tracking (Quest Pro / Vive Eye Pro) 또는 Fixed Foveation

### 3.2 활성

```ini
; Quest 2/3 — Fixed Foveation
[/Script/Engine.RendererSettings]
vr.OpenXR.HeadsetFoveationLevel=2         ; 0 = 비활성 / 1 = Low / 2 = Medium / 3 = High
vr.OpenXR.HeadsetFoveationDynamic=1       ; 동적 조정

; Quest Pro / Eye-Tracked Foveated Rendering (5.x)
vr.OpenXR.EyeTrackedFoveation=1
```

### 3.3 Variable Rate Shading (VRS)
- 5.x — DX12 / Vulkan 지원
- Foveated Rendering 의 SW 구현
- 활성: `r.VRS.Enable=1`

---

## 4. VR 메모리 / 성능 매트릭스

| HMD | Resolution (per eye) | FPS | GPU | 권장 설정 |
|-----|---------------------|-----|-----|---------|
| Quest 2 | 1832x1920 | 72/90 | Snapdragon XR2 | Mobile + Multi-View + Foveated |
| Quest 3 | 2064x2208 | 90/120 | Snapdragon XR2+ | Mobile Deferred + Multi-View + Foveated |
| Quest Pro | 1832x1920 | 90 | XR2+ | + Eye-Tracked Foveation |
| Valve Index | 2880x1600 (per eye 1440x1600) | 90/120/144 | PC GPU | PC + Instanced Stereo + VRS |
| HTC Vive Pro | 2880x1600 | 90 | PC GPU | PC + Instanced Stereo |
| PSVR2 | 2000x2040 | 90/120 | PS5 GPU | Console + Instanced Stereo + Eye-Tracked Foveation |
| WMR / Pimax | 다양 | 90 | PC GPU | PC + Instanced Stereo |

---

## 5. VR Render 제약 (PC vs Mobile VR)

### 5.1 PC VR (Index / Vive Pro)

```
✅ 활성 가능:
- Lumen (HWRT 또는 Software RT)
- Nanite (정적 메시)
- 모든 PostProcess
- HWRT Reflection / Shadow

⚠ 비용 큰 항목:
- Bloom Quality 3+ (90fps 못 맞춤)
- TAA (Reprojection 충돌)

❌ 비활성:
- Motion Blur (멀미 유발)
```

### 5.2 Mobile VR (Quest 2/3)

```
❌ 비활성 의무:
- Lumen / Nanite
- HWRT
- Tessellation
- 무거운 PostProcess (Bloom / DOF / SSR)

✅ 활성:
- Mobile Forward (Quest 2) / Mobile Deferred (Quest 3)
- Multi-View (양안 동시 렌더)
- Foveated Rendering (Fixed)
- Lightmap Static Lighting
- 단순 ToneMapper + LUT

⚠ 권장:
- 메모리 < 1GB (Quest 2)
- DrawCalls < 800 (Quest 2) / < 1200 (Quest 3)
- Triangles < 1.5M (Quest 2) / < 3M (Quest 3)
```

---

## 6. VR 함정 — 멀미 회피 (Production 의무)

### 6.1 Frame Rate 드롭 = 즉시 멀미
```
- 90fps Quest 2 = 11ms / Frame
- 88fps 떨어져도 = Reprojection 발동 (시스템)
- Custom Render Pass = 11ms 이내 처리 의무
```

### 6.2 Stereo Mismatch
```
- 양쪽 눈 = 동일 Pass / 동일 Material 의무
- View 의존 PostProcess = 양쪽 눈 별도 처리
- ✅ Stereo Layer (UI 등) = 같은 Texture Sampling
```

### 6.3 Motion Blur — 비활성 의무
```
- VR + Motion Blur = 즉시 멀미
- 모든 VR 빌드 = Motion Blur 비활성 의무
r.MotionBlur.Enable=0   ; VR Project Settings
```

---

## 7. SceneViewExtension VR 분기

```cpp
class FMyVRViewExtension : public FSceneViewExtensionBase
{
    virtual bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Ctx) const override
    {
        // VR 빌드만
        return GEngine && GEngine->XRSystem.IsValid() && GEngine->XRSystem->IsHeadTrackingAllowed();
    }

    virtual void PrePostProcessPass_RenderThread(...) override
    {
        // Multi-View 처리 — View 별 분기
        if (View.StereoPass != EStereoscopicPass::eSSP_FULL)
        {
            // 양안 모드 — Multi-View 안전 의무
            int32 EyeIndex = (View.StereoPass == EStereoscopicPass::eSSP_LEFT_EYE) ? 0 : 1;
            // ...
        }
    }
};
```

---

## 8. OpenXR Plugin Build.cs 의존

```csharp
// MyModule.Build.cs
PrivateDependencyModuleNames.AddRange(new[] {
    "OpenXR",
    "OpenXRHMD",
    "HeadMountedDisplay",
    "XRBase",
});

// Quest 전용 (선택)
if (Target.Platform.IsInGroup(UnrealPlatformGroup.Android))
{
    PrivateDependencyModuleNames.Add("OculusOpenXRLoader");
}
```

---

## 9. VR 디버그

### 9.1 콘솔 명령

```
stat unit                     ; Frame Time (90fps = 11ms 이하)
stat scenerendering          ; DrawCalls
stat memory                   ; 메모리
vr.bUseDistanceCulling 1     ; 거리 컬링
ShowFlag.HMDDistortion 0     ; 디스토션 디버그
ShowFlag.StereoRendering     ; Stereo 시각화

; OpenXR 디버그
xr.OpenXR.LogActions 1
```

### 9.2 RenderDoc VR
```
- Quest 2 Vulkan 캡처 = adb pull / RenderDoc
- PC VR Vulkan 캡처 = RenderDoc UE Plugin
```

---

## 10. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | OculusVR / SteamVR Plugin (5.4+ 제거) | OpenXR 통합 표준 |
| 2 | Motion Blur 활성 (멀미) | r.MotionBlur.Enable=0 의무 |
| 3 | TAA 활성 (Reprojection 충돌) | TAA 대신 MSAA / 기본 비활성 |
| 4 | Stereo 미설정 (단안 렌더) | vr.InstancedStereo=1 또는 vr.MobileMultiView=1 |
| 5 | Quest 2 + Lumen / Nanite 활성 | Mobile = 비활성 의무 |
| 6 | 90fps 못 맞춤 (Custom Pass 비용 큼) | 11ms 이내 + Foveated Rendering |
| 7 | Foveated Rendering 비활성 | Quest = vr.OpenXR.HeadsetFoveationLevel=2 의무 |
| 8 | Eye-Tracked Foveation 미활성 (Quest Pro / PSVR2) | 5.x 신규 — 활성 의무 |
| 9 | View 의존 PostProcess = 양쪽 눈 동일 처리 | EStereoscopicPass 분기 |
| 10 | VR 메모리 한계 초과 (Quest 2 = 1GB) | Texture < 200MB / Mesh < 100MB |

---

## 11. 체크리스트

- [ ] OpenXR Plugin 활성 (5.x 표준)
- [ ] vr.InstancedStereo=1 (PC) 또는 vr.MobileMultiView=1 (Quest)
- [ ] Foveated Rendering 활성 (Quest 2/3)
- [ ] Eye-Tracked Foveation (Quest Pro / PSVR2)
- [ ] r.MotionBlur.Enable=0 (멀미 회피)
- [ ] TAA 비활성 (Reprojection 충돌 회피)
- [ ] Quest = Lumen / Nanite 비활성
- [ ] PostProcess = ToneMapper + LUT 만 (Quest)
- [ ] 90fps 유지 (Quest 2/PC) / 120fps (Index/PSVR2)
- [ ] DrawCalls < 800 (Quest 2) / < 1200 (Quest 3)
- [ ] Stereo View 분기 (EStereoscopicPass)

---

## 12. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/Mobile.md`](../Mobile/SKILL.md) — Quest = Mobile VR
- [`Render/references/SceneViewExtension.md`](../SceneViewExtension/SKILL.md) — VR Hook
- [`Render/references/PostProcess.md`](../PostProcess/SKILL.md) — VR 제한 PostProcess
- [`Render/references/Vulkan.md`](../Vulkan/SKILL.md) — Quest = Vulkan ES
- [`Input/references/InputCore.md`](../../Input/references/InputCore.md) — VR Controller (Motion Source)

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. OpenXR 5.x 통합 + Stereo 3 모드 + Foveated Rendering + VR 메모리 매트릭스 + PC vs Mobile VR + 멀미 회피 + 함정 10대. |
