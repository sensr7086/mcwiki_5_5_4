---
name: claude-wiki-honest-limits
description: 본 위키의 정직한 한계 자백 — 6대 본질 문제 + 현실적 기대치 + 사용 조건. 위키를 만능 도구로 오해하지 말 것. Anthropic 글 1 의 "self-evaluation bias 방지" 정신으로 위키 자체에 적용.
---

# Wiki 정직한 한계 — 영구 기록

> **본 문서는 위키 자체에 대한 외부 비판 분석을 영구 기록**. 미래의 Claude / 사용자가 이 위키를 받았을 때 **"마법 도구가 아님"** 을 즉시 알게 하기 위함.
>
> Anthropic 글 1 의 "Generator + Evaluator 분리" 정신을 위키 자체에 적용 — 위키 작성자 (저 자신 포함) 가 위키 평가하면 self-eval bias.

---

## 0. 한 줄 요약

> 위키는 **"비숙련 + 게임 로직 + UE 5.5.x + 검증 루프 같이"** 일 때만 +15~25%p 이득. 그 외엔 토큰 / 속도 / staleness 비용이 이득보다 클 수 있음.

---

## 1. 현실적 기대치 매트릭스 ⭐

### 1.1 예측 (가설)

| 작업 유형 | 위키 없이 | 위키 있어 | 예측 마진 | 사유 |
|----------|----------|----------|----------|------|
| Components / GameFramework 일반 | 70% | 85% | **+15%p** | 6대 정책 + 라이프사이클 11단계 자동 |
| Animation 5.x (IK Rig 등) | 55% | 80% | **+25%p** | 5.x 신규 API + Native* 분리 + IK Rig 표준 |
| Editor 인하우스 툴 (4단 분리) | 50% | 78% | **+28%p** | 가장 큰 효과 — 함정이 워낙 많음 |
| Slate / UMG 인밸리데이션 | 65% | 80% | **+15%p** | InvalidationHotspots 인덱스 |
| **AssetLoading (어셋 로드 함정)** | 50% | 90% | **+40%p** | Cooked Build 함정의 대부분 — Soft+Pin+IsValid+Cancel |
| ~~Render (RDG / USF)~~ ⚠ 갱신 (2026-05-08): | | | | |
| **Render (RDG / Shader / Material / Lumen+Nanite)** | 55% | 78% | **+23%p** | **신설 8 sub-skill** — 3축 스레드 분리 + RDG + Shader Permutation + Lumen/Nanite 호환 + PSO Precache |
| ~~Render (저수준 RHI Vulkan / D3D12)~~ | 60% | 65% | **+5%p** | RHI 깊이 부분만 — Vulkan 특화 / Driver 디버그 등 |
| 일반 C++ / 비-UE 코드 | 80% | 80% | **0%p** | 영향 없음 |

### 1.2 실측 (누적 — [`measurements/_summary.md`](./measurements/_summary.md))

| 일자 | 시나리오 | 카테고리 | 예측 마진 | **실측 마진** | 신뢰도 | 비고 |
|------|---------|---------|----------|--------------|--------|------|
| 2026-05-08 | MCSoftStaticMesh | Components / AssetLoading | +15~+40 | **+60** ⭐ | ⭐ | Critical 3종 (FStreamable Pin / IsValid / EndPlay Cancel) — Cooked Shipping 함정 |

> **⭐ 신뢰도 = 낮음** (가상 No-Wiki baseline — 같은 Claude 가 자기 가짜 비교 대상 작성). Self-eval bias 위험 영역.
> 진짜 별도 세션 측정 (⭐⭐⭐) 누적 시 가설 보정 진행.

### 1.3 결론

**1건 측정 + ⭐ 신뢰도** = 통계적 결론 보류. 다만:
- ✅ 어셋 로드 함정 시나리오 = 위키가 강하게 작용함 (직관과 일치)
- ⚠️ 마진 +60 이 진짜인지 가상 baseline 의 strawman 인지 = **별도 세션 No-Wiki 측정 필요**
- 🚨 Critical 3종 (Cooked Build 환경 특이 함정) 회피는 정량 검증됨 — 위키 가치의 핵심

**잠정 결론**: 위키는 **"있는 게 분명히 낫다" 지만 "있으면 만사형통" 은 절대 아닙니다**. 마진 (+15~60%p, 시나리오별) 를 얻는 대신 **토큰 13.5배** (실측), 반응 속도 3~5배, 분기별 감사 부담을 받습니다. 그리고 위키가 틀렸을 때 그 거짓을 더 그럴듯하게 코드로 옮기는 위험도 동반.

→ **"비싸고 부지런히 관리해야 작동하는 도구"** 로 보시는 게 맞습니다.

---

## 2. 위키가 있을 때 (이상적 케이스 — 변호 X, 사실)

- 위 함정들이 06/07/08/10/11/12 인덱스로 명시되어 있어 Claude 가 읽으면 회피 가능
- 5.x 신규 API 가 카테고리별 SKILL.md 에 정리되어 있어 환각 줄어듦
- 4단 에디터 분리, 6대 Component 정책, Super 호출 규약 같은 팀 컨벤션 자동 적용
- 체감 정확도: **80~85%**. 즉 위키로 얻는 마진은 대략 +15~20%p

---

## 3. 6대 본질 문제 ⚠️

### 3.1 토큰 폭주

```
시나리오별 Read 양 (실측):
- [Animation] 발 IK 추가:   ~95KB  / 40K 토큰
- [Components] Pawn 작성:   ~120KB / 50K 토큰
- [Editor] AssetEditorToolkit: ~140KB / 60K 토큰
```

200KB 컨텍스트 소비 후 코드 작성 = Claude 작업 메모리 절반 사용 (200K 컨텍스트 모델 기준). **긴 세션에서 컨텍스트 압박 + 비용 증가**.

### 3.2 반응 속도 하락

작업 1개당 **10~15회 Read 툴 호출**이 코드 작성 전에 발생. 첫 응답까지 체감 **3~5배 느림**. UI 체감으로 = 사용자 경험에 실제 비용.

### 3.3 위키 자체 staleness 위험 ⭐ (가장 구체적)

116 SKILL.md 가 라인 번호 ("Pawn 598", "Character 1,095") 까지 적혀있음 → **UE 마이너 버전 올라가면 즉시 깨짐**. `18_ModelEvolutionAudit` 가 분기별 감사를 의무화한 건 정직한 신호 — **"이거 곧 썩는다" 는 자기 인정**.

### 3.4 검증 부재의 환각 리스크 ⭐⭐ (가장 깊은 우려)

116 SKILL.md 를 누가 작성했든 (사람 / LLM 혼합), **일부는 grep 검증 없이 추론으로 채워졌을 가능성**이 있음.
- Claude 가 SKILL.md 를 신뢰하고 코드 짜면 → **틀린 가이드를 그대로 신뢰하는 새로운 환경**이 생김
- Generator / Evaluator 패턴 (15_EvaluatorRecipe) 이 있지만 **Evaluator 도 결국 Claude 라 비슷한 사각지대 공유**

**복합 위험**: 위키 = 신뢰 소스 → Claude 가 신뢰 → 코드도 자신감 ↑ → 사용자도 신뢰 → 디버깅 시 위키 의심 못 함 (cascade error).

### 3.5 지시 준수 감소

컨텍스트가 길수록 LLM 의 instruction-following 이 떨어짐 (Anthropic 도 long_conversation_reminder 를 만들 정도). **"6대 정책" 다 읽어도 작업 중반엔 1~2개 빠뜨림**.

### 3.6 위키 커버 안 된 영역은 그대로

```
실제 커버리지:
✅ Components / GameFramework / Animation / Input / UMG / Slate
✅ AssetClasses / Editor
⚠️ Render — sub-skill 적음 (CLAUDE.md §4 영역 정의만)
❌ RDG (Render Dependency Graph) — 0
❌ USF / Custom Shader / Global Shader — 0
❌ SceneViewExtension — 0
❌ FRDGBuilder / FRDGTexture / FRDGBufferRef — 0
❌ Build.cs 깊이 / Build Toolchain — 0
❌ 플랫폼 SDK (Steam / EOS / PSN / Switch) — 0
❌ Online Subsystem — 0
❌ Networking 깊이 (Iris / Push Model 5.x) — 부분만
```

**RDG / USF / SceneViewExtension 깊이 작업은 위키 없이와 거의 동일**. 빌드 / 패키징 / 플랫폼 SDK 도 스코프 밖.

---

## 4. 위키 가치가 진짜로 발휘되는 조건

### 4.1 가치 큼 ✅
1. Claude 가 무에서 작성 → 위키 도움 큼 (베이스라인 60% → 80%)
2. 사용자가 UE 처음 → 위키 읽기만 해도 함정 회피
3. 컴파일 / Cooked Build 검증 루프 같이 → 신뢰성 보강
4. UE 5.5 ± 1 분기 안 → staleness 영향 미미

### 4.2 가치 작음 ⚠️
1. 숙련 UE 개발자 (이미 알고 있음 — 위키 = 책값)
2. Render / RDG / Shader 작업 (커버 X)
3. UE 5.8 / 5.9 후 분기 감사 안 하면
4. Cooked Build 검증 안 하면 (틀린 가이드도 PIE 만 통과)

---

## 5. 사용 가이드 (위키 운영자 / Claude 모두에게)

### 5.1 위키 사용 전 체크리스트

```
□ 작업 카테고리가 위키 커버 영역? (Render/RDG = X)
□ UE 버전이 5.5.x? (5.8+ = 라인 번호 깨짐 가능)
□ 컴파일 / Cooked Build 검증 가능? (없으면 위키 신뢰성 검증 못 함)
□ 최종 사용