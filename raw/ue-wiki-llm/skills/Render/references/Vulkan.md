---
name: render-vulkan
description: RHI 벤더 차이 — DX12 / Vulkan / Metal / OpenGL ES. 플랫폼 분기 + 셰이더 호환성 + 5.x Vulkan 전용 함정 (Render Pass / Pipeline Barrier / Descriptor Set) + Driver 디버그. Cross-Platform 게임 개발 표준.
---

# Render/Vulkan — RHI 벤더 차이 + Cross-Platform 표준

> **위치**: `Engine/Source/Runtime/VulkanRHI/` + `D3D12RHI/` + `MetalRHI/` + `OpenGLDrv/` (Driver 측)
> **요지**: UE 5.x 의 다중 RHI 백엔드 — Driver 별 차이 / 셰이더 호환성 / 플랫폼 분기.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 RHI 추상 우선 | RDG / FRHICommandList = 자동 RHI 추상. 직접 RHI 호출 = 최소화 |
| 🚨 셰이더 호환성 | USF = 모든 RHI 호환 (Driver별 컴파일러 자동) — 단 일부 함수 제한 |
| 🚨 Driver 디버그 | RenderDoc / Vulkan Validation Layer / NSight Graphics 사용 |

---

## 1. RHI 백엔드 5종 매트릭스

| RHI | 플랫폼 | 셰이더 컴파일러 | 특징 |
|-----|-------|---------------|------|
| **D3D12** ⭐ | Windows / Xbox / Console | DXC (DXIL) | 가장 안정 / 5.x HWRT 표준 |
| **Vulkan** ⭐ | Windows / Linux / Switch / Quest / Steam Deck | DXC (SPIR-V) | Cross-Platform 표준 |
| **Metal** | macOS / iOS / Apple Silicon | Metal Shader Compiler (MSL) | Apple 전용 |
| **OpenGL ES** | 5.x — Android / 일부 Linux Mobile (legacy) | GLSL | 점진 deprecated |
| **D3D11** | 5.x — Legacy 호환만 (Mobile Forward 일부) | HLSL FXC | Deprecated, 5.4+ X |

---

## 2. RHI Feature Level (5.x 8단계)

```cpp
// RHIFeatureLevel.h
enum class ERHIFeatureLevel : uint8
{
    ES2_REMOVED = 0,    // 5.x — 제거됨
    ES3_1,              // Mobile (OpenGL ES 3.1 / Vulkan ES)
    SM4_REMOVED,        // 5.x — 제거됨
    SM5,                // PC / Console (D3D11 호환 — Legacy)
    SM6,                // 5.x — D3D12 / Vulkan 표준 (Mesh Shader 지원)
    Num,
};

// 사용 패턴
if (GMaxRHIFeatureLevel >= ERHIFeatureLevel::SM6)
{
    // 5.x 신규 기능 (Mesh Shader / Variable Rate Shading / 등)
}
else if (GMaxRHIFeatureLevel >= ERHIFeatureLevel::SM5)
{
    // PC / Console 표준
}
else
{
    // Mobile (ES3_1)
}
```

---

## 3. 셰이더 컴파일 흐름 (Cross-Platform)

```
USF 작성 (HLSL 표준)
  ↓
HLSL Translator (5.x 통합)
  ↓
DXC (DirectX Shader Compiler)
  ├── D3D12: DXIL (Vulkan/Metal 도 DXC 사용)
  ├── Vulkan: SPIR-V
  └── Metal: MSL (별도 변환)
  ↓
플랫폼별 PSO 캐시
  ↓
Cooked DDC + Pak 안 저장
```

→ **USF 작성 시 호환 의무**: 일부 함수 / 키워드 제한.

---

## 4. RHI 별 함수 / 키워드 제한 매트릭스

| HLSL 기능 | D3D12 | Vulkan | Metal | OpenGL ES |
|----------|:-----:|:------:|:-----:|:---------:|
| Tessellation Stage | ✅ | ✅ | ⚠ | ❌ |
| Mesh Shader | ✅ | ✅ | ⚠ (5.x) | ❌ |
| Compute Shader | ✅ | ✅ | ✅ | ✅ |
| Variable Rate Shading | ✅ | ⚠ | ❌ | ❌ |
| Hardware Ray Tracing | ✅ | ⚠ | ⚠ | ❌ |
| Async Compute | ✅ | ✅ | ⚠ | ❌ |
| Inline UAV in Vertex Stage | ✅ | ✅ | ⚠ | ❌ |
| Wave Operations (`WaveActiveSum` 등) | ✅ (SM6) | ✅ (Subgroup) | ⚠ | ❌ |
| 64bit Atomics | ✅ | ✅ | ⚠ | ❌ |

→ **USF 안 분기 의무**:
```hlsl
#if FEATURE_LEVEL >= FEATURE_LEVEL_SM6
    // SM6 전용
#elif FEATURE_LEVEL >= FEATURE_LEVEL_SM5
    // SM5 표준
#else
    // Mobile / OpenGL ES
#endif
```

---

## 5. Vulkan 특화 함정 (가장 자주 디버그)

### 5.1 Pipeline Barrier (자동 → 수동 시)
```
- D3D12 / RDG = Resource Barrier 자동 (FRDGBuilder)
- Vulkan 직접 RHI = vkCmdPipelineBarrier 수동 시 race 가능
- 권장: RDG 우선
```

### 5.2 Render Pass (Vulkan 전용)
```
- Vulkan = Render Pass 명시 의무 (D3D12 / Metal 자동)
- RDG = Render Pass 자동 추론
- 직접 RHI = BeginRenderPass / EndRenderPass 페어 의무
```

### 5.3 Descriptor Set
```
- Vulkan = Descriptor Set / Binding Slot 명시
- RDG / SHADER_PARAMETER_STRUCT = 자동 처리
- 직접 RHI = DescriptorSet Allocation 수동
```

### 5.4 Validation Layer 활성

```bash
# Windows
set VK_INSTANCE_LAYERS=VK_LAYER_KHRONOS_validation
"<UE>/Engine/Binaries/Win64/UnrealEditor.exe" -vulkan -d3ddebug

# Linux
VK_INSTANCE_LAYERS=VK_LAYER_KHRONOS_validation ./UnrealEditor -vulkan
```

→ Vulkan Validation Layer 활성 시 = 표준 위반 즉시 에러 출력 (Driver 안전).

---

## 6. RHI Switch (런타임)

```cpp
// FRHIInterfaceType
enum class ERHIInterfaceType : uint32
{
    Hidden = 0,
    Null,
    D3D11,
    D3D12,
    Vulkan,
    Metal,
    Agx,        // 5.x Apple Silicon
};

// 검사
if (GDynamicRHI->GetInterfaceType() == ERHIInterfaceType::Vulkan)
{
    // Vulkan 특화
}
```

---

## 7. RenderDoc / NSight Graphics 디버그

### 7.1 RenderDoc 사용
```cpp
// 빌드 시 활성
// DefaultEngine.ini
[/Script/RenderDoc.RenderDocPlugin]
bEnableRenderDocAtStartup=true

// 콘솔
RenderDoc.CaptureFrame   ; 1프레임 캡처
```

### 7.2 NSight Graphics
```
- D3D12 / Vulkan 전용
- Frame Debugger / GPU Trace
- HWRT Inspector (5.x)
```

### 7.3 Vulkan Validation Layer
```bash
VK_INSTANCE_LAYERS=VK_LAYER_KHRONOS_validation
# 표준 위반 즉시 출력
```

---

## 8. 플랫폼별 Build.cs 분기

```csharp
// MyModule.Build.cs
if (Target.Platform == UnrealTargetPlatform.Win64)
{
    PrivateDependencyModuleNames.Add("D3D12RHI");
    PrivateDependencyModuleNames.Add("VulkanRHI");
}
else if (Target.Platform == UnrealTargetPlatform.Mac)
{
    PrivateDependencyModuleNames.Add("MetalRHI");
}
else if (Target.Platform == UnrealTargetPlatform.Linux)
{
    PrivateDependencyModuleNames.Add("VulkanRHI");
}
else if (Target.Platform.IsInGroup(UnrealPlatformGroup.Android))
{
    PrivateDependencyModuleNames.Add("VulkanRHI");
}
```

---

## 9. Cross-Platform 셰이더 작성 표준

```hlsl
// MyShader.usf — Cross-Platform 표준
#include "/Engine/Public/Platform.ush"

#if FEATURE_LEVEL >= FEATURE_LEVEL_SM6
    // Wave Intrinsics (5.x)
    #define WAVE_OPS 1
#else
    #define WAVE_OPS 0
#endif

#if METAL_PROFILE
    // Metal 특화
#endif

#if VULKAN_PROFILE
    // Vulkan 특화
#endif

#if PLATFORM_IS_MOBILE
    // Mobile 특화
#endif
```

---

## 10. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Vulkan = 직접 vkCmdPipelineBarrier 사용 | RDG 가 자동 처리 — 직접 X |
| 2 | D3D12 전용 함수 (`WaveActiveSum`) Mobile 미지원 | FEATURE_LEVEL 분기 의무 |
| 3 | Tessellation = OpenGL ES 미지원 | Mobile = Tessellation 비활성 |
| 4 | Metal MSL = MULTILINE 매크로 미지원 (드물게) | DXC 표준 사용 |
| 5 | Vulkan Validation Layer 비활성 → race 미검출 | 개발 중 의무 활성 |
| 6 | OpenGL ES = Compute Shader 일부 제한 | ES3.1+ 만 / 단순 Compute |
| 7 | D3D11 Legacy 코드 = 5.4+ 미지원 | 5.x = D3D12 / Vulkan 표준 |
| 8 | Cross-Platform Shader = `#if D3D12_PROFILE` 만 분기 | FEATURE_LEVEL + PLATFORM 양축 분기 |

---

## 11. 체크리스트

- [ ] FEATURE_LEVEL 분기 (SM5 / SM6 / Mobile)
- [ ] PLATFORM_IS_MOBILE 분기 (Mobile 전용)
- [ ] RDG / FRHICommandList 우선 (직접 RHI 최소화)
- [ ] Vulkan Validation Layer (개발 중 활성)
- [ ] RenderDoc 캡처 (디버그)
- [ ] Cross-Platform Shader = USF 표준 함수 우선
- [ ] Build.cs 플랫폼별 RHI 모듈 의존
- [ ] D3D11 Legacy 코드 = 5.x deprecated 인지

---

## 12. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/RHI.md`](../RHI/SKILL.md) — RHI Command List
- [`Render/references/Shader.md`](../Shader/SKILL.md) — Permutation + Path 등록
- [`Render/references/Mobile.md`](../Mobile/SKILL.md) — Mobile 특화
- [`Build/SKILL.md`](../../Build/SKILL.md) — Build.cs 플랫폼 분기

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. RHI 5 백엔드 + Feature Level 8 + 셰이더 컴파일 흐름 + 호환성 매트릭스 + Vulkan 특화 함정 + RenderDoc/NSight + Cross-Platform 표준 + 함정 8대. |
