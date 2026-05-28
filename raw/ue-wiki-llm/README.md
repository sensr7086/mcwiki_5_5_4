# UE 5.7.4 LLM Wiki — Claude Code Plugin

> Unreal Engine 5.7.4 — 19 카테고리 + 116+ sub-skill + 15 횡단 인덱스 + Evaluator Workflow + **6개 위키 액션 커맨드**.
> Anthropic Skills Plugin 표준 준수.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UE 5.7.4](https://img.shields.io/badge/Unreal_Engine-5.7.4-blue)](https://www.unrealengine.com/)
[![Plugin Version](https://img.shields.io/badge/Plugin-v1.4.0-green)](.claude-plugin/plugin.json)

---

## ⚠️ 사용 전 필수 — 정직한 한계 인지

**위키는 마법 도구가 아닙니다**. 사용 전 의무 Read:
- 🚨 [`meta/CLAUDE-wiki-honest-limits.md`](meta/CLAUDE-wiki-honest-limits.md) — 6대 본질 문제 + 현실적 기대치
- 🛠 [`meta/improvement-roadmap.md`](meta/improvement-roadmap.md) — 해결 방안 매트릭스

**한 줄 요약**: 위키는 "비숙련 + 게임 로직 + UE 5.7.x + Cooked Build 검증 같이" 일 때만 +15~25%p. 그 외엔 토큰/속도/staleness 비용 ↑.

---

## 📁 폴더 구조 (Claude Code Plugin 표준)

```
LLM_Wiki/
├── .claude-plugin/              # Plugin 메타데이터
│   ├── plugin.json              # ⭐ Plugin manifest (v1.3.0)
│   ├── marketplace.json
│   ├── agents/                  # 12 sub-agents (opus model)
│   │   ├── ue-orchestrator.md
│   │   ├── ue-evaluator.md
│   │   ├── ue-animation-specialist.md
│   │   └── ... (9 more)
│   └── commands/                # Slash commands
│       └── evaluate.md          # /evaluate
│
├── skills/                      # ⭐ 14 카테고리 + 116 sub-skill
│   ├── CoreUObject/             (Tier 1, 13)
│   ├── Components/              (Tier 1, 15)
│   ├── GameFramework/           (Tier 1, 6)
│   ├── Animation/               (Tier 1, 7 — 5.x IK Rig 포함)
│   ├── AssetClasses/            (Tier 1, 9)
│   ├── Input/                   (Tier 1, 5)
│   ├── SlateCore/               (Tier 3, 10)
│   ├── Slate/                   (Tier 3, 12)
│   ├── UMG/                     (Tier 3, 7)
│   ├── Editor/                  (18, 4단 분리)
│   ├── Subsystem/               (Tier 0, 1)
│   ├── Significance/            (Plugin)
│   ├── GAS/                     (Plugin)
│   └── Niagara/                 (Plugin)
│
├── references/                  # 14 횡단 인덱스 + 03_WikiHarness
│   ├── 03_WikiHarness.md        # ⭐ 시나리오 라우팅 마스터
│   ├── 04_OverrideIndex.md      # virtual + Super 호출
│   ├── 07_ProfilingScopeRule.md # 의무
│   ├── 09_GlobalIteratorPolicy.md
│   ├── 10_ComponentPolicies.md  # 6대 정책
│   ├── 11_AssetLoadingPolicy.md
│   ├── 12_AssetOptimizationPolicy.md
│   ├── 14_TaskHandoffTemplate.md
│   ├── 15_EvaluatorRecipe.md    # ⭐ 8단계 평가
│   ├── 16_PolicyPriority.md     # 점수 기반 충돌 해결
│   ├── 17_QualityCriteria.md    # 4기준 가중치
│   ├── 18_ModelEvolutionAudit.md# 분기별 staleness
│   └── deep/                    # Level 3 references
│
├── catalog/                     # 모듈 카탈로그
│   ├── RuntimeIndex.md          # Runtime 모듈 (189)
│   └── EditorDevIndex.md        # Editor + Developer
│
├── eval/                        # ⭐ Evaluator Workflow
│   ├── README.md                # 사용법
│   ├── EVAL_REQUEST_TEMPLATE.md # 새 세션 복사-붙여넣기용
│   ├── EVAL_REPORT_TEMPLATE.md  # 평가자 출력 표준
│   └── EXAMPLE_REPORT.md        # 95점 vs 32점 비교
│
├── meta/                        # Wiki 메타 / governance / 한계 인정
│   ├── CLAUDE-wiki-governance.md
│   ├── CLAUDE-wiki-honest-limits.md  # ⭐ 6대 본질 문제
│   ├── improvement-roadmap.md       # 해결 매트릭스
│   ├── confidence-tags.md           # 3단계 신뢰도
│   └── corrections.md               # 사용자 발견 거짓 로그
│
├── templates/                   # 신규 프로젝트용 템플릿
│   └── ProjectCLAUDE_Template.md
│
└── docs/                        # 진입점 문서
    ├── CLAUDE.md                # ⭐ 메인 진입점 (Claude Code 자동 로드)
    └── INSTALL.md               # 설치 가이드 (4 방법)
```

---

## 🚀 빠른 시작

### 1. 설치 — `docs/INSTALL.md` 참조 (4가지 방법)

```bash
# 방법 1: Claude Code Plugin 설치 (권장)
claude /plugin install local <이 폴더 경로>

# 방법 2: Symlink
mklink /D "<프로젝트>\LLM_Wiki" "<이 폴더 경로>"

# 방법 3: Git Submodule
git submodule add https://github.com/sensr7086/ue-wiki-llm LLM_Wiki

# 방법 4: docs/CLAUDE.md import 한 줄
# `@import LLM_Wiki/docs/CLAUDE.md` (다른 프로젝트의 CLAUDE.md 안)
```

### 2. 사용

```
# 카테고리 prefix 로 specialist 자동 호출
[Animation] 캐릭터에 발 IK 추가
[Components] 새 ShapeComponent 작성
[Editor] 인하우스 에셋 에디터

# 코드 평가 (외부 평가자)
/evaluate Source/MyGame/Private/MyChar.cpp

# v1.4.0 — 6개 위키 액션 커맨드 (한국어 위키 룩업)
/wiki-explain UAbilitySystemComponent             # 개념/용어 6단 위키 설명
/wiki-lookup UCharacterMovementComponent          # API/클래스 레퍼런스 카드
/wiki-example BehaviorTree에서 EQS로 가장 가까운 적 찾기  # 정책-준수 코드 예제
/wiki-debug Cooked Shipping에서만 ULinkerLoad 크래시       # 디버깅 가이드
/wiki-perf 50명 NPC 동시 전투 신                          # 4기준 성능 체크리스트
/wiki-migrate Legacy Input -> Enhanced Input             # 마이그레이션 절차
```

### 3. 진입점

- **메인 진입점**: [`docs/CLAUDE.md`](docs/CLAUDE.md)
- **시나리오 라우팅**: [`references/03_WikiHarness.md`](references/03_WikiHarness.md)
- **설치 가이드**: [`docs/INSTALL.md`](docs/INSTALL.md)
- **Plugin manifest**: [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)

---

## 🤖 12 Sub-Agents (Orchestrator-Workers Pattern)

모두 `opus` 모델. Anthropic Article 2 Orchestrator-Workers 패턴.

| Agent | Trigger | 역할 |
|-------|---------|------|
| `ue-orchestrator` | 카테고리 prefix 자동 식별 | 메인 라우터 |
| `ue-evaluator` | 코드 작성 후 자동 (의무) | Self-eval bias 방지 |
| `ue-wiki-maintainer` | `[Wiki]` | 위키 메타 작업 |
| `ue-audit-agent` | 분기별 / UE 버전 업그레이드 | Staleness 감사 |
| `ue-components-specialist` | `[Components]` | Tick / 콜리전 / 6대 정책 |
| `ue-gameframework-specialist` | `[GameFramework]` / `[Subsystem]` | Actor 라이프사이클 |
| `ue-slate-umg-specialist` | `[Slate]` / `[UMG]` / `[SlateCore]` | UI / HUD / 위젯 |
| `ue-editor-specialist` | `[Editor]` | 인하우스 툴 / 4단 분리 |
| `ue-asset-specialist` | `[AssetClasses]` | 자산 + 어셋 로드 + 최적화 |
| `ue-input-specialist` | `[Input]` | Enhanced Input |
| `ue-animation-specialist` | `[Animation]` | AnimInstance / IK Rig / 5중 최적화 |
| `ue-plugin-specialist` | `[GAS]` / `[Niagara]` / `[Significance]` | Plugin 작업 |

---

## 📊 위키 가치 (정직한 측정)

| 작업 유형 | 위키 없이 | 위키 있어 | 마진 |
|----------|----------|----------|------|
| Components / GameFramework 일반 | 70% | 85% | **+15%p** |
| Animation 5.x (IK Rig 등) | 55% | 80% | **+25%p** |
| Editor 인하우스 툴 (4단 분리) | 50% | 78% | **+28%p** (가장 큰 효과) |
| Slate / UMG 인밸리데이션 | 65% | 80% | **+15%p** |
| Render (RDG / USF) | 60% | 65% | **+5%p** (위키 얇음) |
| 일반 C++ / 비-UE 코드 | 80% | 80% | **0%p** |

**전제**: 컴파일 + Cooked Build 검증 + UE 5.7.x ± 1 분기 안 + 비숙련 사용자.

---

## 🛡 Anthropic 3-Article 패턴 통합

### Article 1 (harness-design-long-running-apps)
- ✅ Generator/Evaluator 분리 (`eval/` + `references/15_EvaluatorRecipe.md`)
- ✅ 멀티 세션 인계 표준 (`references/14_TaskHandoffTemplate.md` — handoff 파일은 Plugin 외부 사용자 폴더에 저장)
- ✅ Cooked Build 검증 의무 (`references/15_EvaluatorRecipe.md` Stage 2)
- ✅ Self-eval bias 방지 (별도 인스턴스 의무)

### Article 2 (building-effective-agents)
- ✅ Orchestrator-Workers (12 agents)
- ✅ Routing (카테고리 prefix → specialist)
- ✅ Parallelization (멀티 카테고리 동시 호출)
- ✅ Evaluator-Optimizer Loop

### Article 3 (equipping-agents-for-the-real-world-with-agent-skills)
- ✅ Anthropic Skills 표준 (frontmatter + description)
- ✅ Progressive disclosure (Level 1 / 2 / 3)
- ✅ Plugin manifest (`.claude-plugin/plugin.json`)
- ✅ Slash commands (`/evaluate`)

---

## 📝 라이선스

MIT License — 자유롭게 사용 / 수정 / 배포.

---

## 👤 Author

**민철** (sensr7086@naver.com)
GitHub: [sensr7086/ue-wiki-llm](https://github.com/sensr7086/ue-wiki-llm)

---

## 📋 변경 이력

| Version | 날짜 | 주요 변경 |
|---------|------|---------|
| 1.4.0 | 2026-05-08 | **위키 액션 커맨드 6개** (/wiki-explain, /wiki-lookup, /wiki-example, /wiki-debug, /wiki-perf, /wiki-migrate) + 누락 토픽 5개 sub-skill (Blueprint, Networking, AI, Build, Audio/Metasound) + `references/19_ExternalSourcesGuide.md` (docs / GitHub / forum 외부 검증 표준) |
| 1.3.0 | 2026-05-07 | Evaluator Workflow + /evaluate command + 정직한 한계 영구 기록 |
| 1.2.0 | 2026-05-07 | Animation IK 카테고리 신설 (5.x IK Rig + IK Retargeter) |
| 1.1.0 | 2026-05-07 | Animation 카테고리 신설 (6 sub-skill) + ue-animation-specialist |
| 1.0.0 | 2026-05-07 | Anthropic Skills Plugin 표준 패키징 + 12 sub-agent |

---

## 🆕 v1.4.0 — 위키 액션 커맨드

| 커맨드 | 용도 | 출력 형식 |
|--------|------|----------|
| `/wiki-explain` | 개념/용어 위키 설명 | 정의 → 핵심 클래스 → 라이프사이클 → 패턴 → 함정 → 관련 sub-skill (6단) |
| `/wiki-lookup` | API/클래스 레퍼런스 룩업 | 분류 → 시그니처 → 멤버 표 → virtual hook → 패턴 → 정책 |
| `/wiki-example` | 정책-준수 코드 예제 생성 | 가정 → 코드 (h+cpp+Build.cs) → 정책 체크리스트 → Cooked 검증 |
| `/wiki-debug` | 에러/크래시 디버깅 가이드 | 입력 → 원인 후보 N개 → 검증 절차 → 수정 패턴 → Cooked vs PIE 차이 |
| `/wiki-perf` | 4기준 성능 점검 | 4기준 표 (35/25/15/25%) + 측정 절차 + P0/P1/P2 권장 |
| `/wiki-migrate` | 마이그레이션 / 셋업 가이드 | 사전 점검 → 단계별 절차 → 시나리오별 핵심 → 사후 의무 |

**모든 커맨드는 다음 의무를 준수**:

1. `references/03_WikiHarness.md` 라우팅 후 sub-skill 로드
2. 신뢰도 태그 — `[verified]` / `[grep-listed]` / `[external-verified]` / `[community]` / `[inferred]`
3. 위키에 없을 때 → `references/19_ExternalSourcesGuide.md` 절차로 docs / GitHub / forum 외부 검증
4. 거짓 발견 → `meta/corrections.md` 누적 안내
                                                                    