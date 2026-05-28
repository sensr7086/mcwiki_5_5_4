---
type: concept
title: "Motion-to-Photon Latency (VR 멀미 회피 임계)"
aliases: ["MTP latency", "M2P latency", "Async Reprojection 근거"]
sources:
  - "[[sources/ue-render-vr]]"
related_concepts: []
tags: [render, vr, latency, motion-sickness, reprojection, spacewarp]
last_updated: 2026-05-13
---

# Motion-to-Photon Latency

## 정의

사용자의 머리 / 핸드 컨트롤러 *움직임* 이 디스플레이 *광자 출력* 으로 전환되는 데까지의 *전체 지연 시간*. VR 멀미 회피의 *유일한* 정량 임계.

```
Sensor → IMU 샘플 → CPU 처리 → 게임 로직 → Render Thread → GPU → Display Scan-out → Photon
```

## 임계 (vault 외 일반 VR 표준)

| 임계 | 평가 |
|------|------|
| < 11 ms | 최적 (90+ fps + Async Reprojection) |
| 11-20 ms | ✅ 통과 (멀미 회피 안정) |
| 20-30 ms | ⚠ 민감 사용자 멀미 |
| > 30 ms | ❌ 광범위 멀미 |

[[sources/ue-render-vr]] raw 는 "90 fps = 11 ms / frame" 산술만 언급. 전체 sensor→photon 분해는 본 concept 의 외삽 (🟡 PARTIAL).

## UE 5.x 의 대응 기술

### Async Reprojection / Timewarp (모든 헤드셋)

마지막 렌더 프레임 + 최신 head pose 로 *2D warp* 적용 → 실제 fps 가 60 이어도 90/120 fps 표시. M2P latency 11 ms 유지.

### Async Spacewarp (Quest 전용)

45 fps 실제 렌더 + 외삽 보간 프레임 → 90 fps 표시. 빠른 움직임에서 ghosting 단점 있으나 GPU 비용 절반.

### Late-Latching (Quest)

`PreRenderViewFamily_RenderThread` 직전 head pose 최신화 → 11 ms 비용 추가 절감.

## 함정

- ❌ `r.OneFrameThreadLag=1` (디폴트) — Render Thread 가 1 frame 늦음. VR 에서 항상 비활성 → `r.OneFrameThreadLag=0`
- ❌ Async Compute heavy work → Render Thread block → M2P latency ↑
- ❌ Tone mapping 등 PostProcess 가 final present 직전 GPU 시간 → M2P latency 누적
- ✅ Vsync / FreeSync 정합 + Display refresh = render rate

## Cross-link

- 권위 source: [[sources/ue-render-vr]]
- 페어: [[sources/ue-render-sceneviewextension]] (PreRenderView Hook 시점 = late-latching 진입점)
- 후속 synthesis 후보: `vr-production-checklist` (vault 미생성)
