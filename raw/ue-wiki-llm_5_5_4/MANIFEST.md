---
type: manifest
title: "ue-wiki-llm 5.5.4 raw content manifest"
imported: 2026-05-09
forked: 2026-05-27
source: "C:\Unreal\UnrealEngine\LLM_Wiki"
fork_from: "E:\MCWiki\raw\ue-wiki-llm (5.7.4 baseline)"
fork_target: "E:\UE_5_5_4\UE_5.5\Engine\ue-wiki-llm_5_5_4"
engine_version: "5.5.4"
total_md_files: 223
total_bytes: 2213838
---

# ue-wiki-llm — raw content manifest

> 본 폴더는 사용자의 기존 UE 5.5.4 LLM Wiki (`C:\Unreal\UnrealEngine\LLM_Wiki`) 의 *content* 를 그대로 복사한 것. **불변** (Karpathy LLM Wiki 패턴의 raw layer).
>
> 운영 인프라 (`agents/`, `commands/`, `eval/`, `meta/`, `templates/`, `.claude-plugin/`, `.plugin`) 는 의도적으로 제외 — 그것은 *그 wiki 시스템 자체* 의 인프라이지 source 가 아니다.

## 1. 무엇이 들어왔는가

| 폴더 | 역할 | md 파일 수 |
| -- | -- | -- |
| `README.md` | 프로젝트 메인 entry | 1 |
| `skills/` | 18 카테고리 × N sub-skill 의 본 SSoT | 129 |
| `references/` | 전역 정책 문서 (00~19 + deep/) | 24 |
| `catalog/` | 클래스/구조체 카탈로그 | 2 |
| `docs/` | 사용자/개발자 문서 | 2 |
| **총계** | | **160 (md) / 2.2 MB** |

## 2. 카테고리별 sub-skill 분포

| 카테고리 | sub-skill 수 | 우선순위 (ingest 순서 권장) | 메모 |
| -- | -- | -- | -- |
| `skills/CoreUObject/` | 14 | 1 (가장 베이스) | UObject + Reflection + GC 등 모든 토대 |
| `skills/Components/` | 18 | 2 | Component 6대 정책 |
| `skills/GameFramework/` | 9 | 3 | Actor/Pawn/Controller/GameMode |
| `skills/AssetClasses/` | 11 | 4 | Mesh/Material/Texture 등 자산 |
| `skills/Animation/` | 8 | 5 | AnimInstance + IK Rig |
| `skills/Editor/` 🛠 | 19 | 6 | UnrealEd + AssetTools 등 |
| `skills/Slate/` 🛠 | 15 | 7 | SWidget + Editor framework |
| `skills/SlateCore/` 🛠 | 11 | 8 | SWidget 베이스 |
| `skills/UMG/` | 10 | 9 | Widget Blueprint |
| `skills/Input/` | 6 | 10 | Enhanced Input |
| `skills/AI/` | 1 | 11 | AAIController + BT/EQS |
| `skills/Blueprint/` | 1 | 12 | BP 시스템 전반 |
| `skills/Build/` | 1 | 13 | UBT + UAT |
| `skills/GAS/` | 1 | 14 | Plugin |
| `skills/Networking/` | 1 | 15 | Replication + RPC |
| `skills/Niagara/` | 1 | 16 | Plugin |
| `skills/Significance/` | 1 | 17 | Plugin |
| `skills/Subsystem/` | 1 | 18 | 5종 Subsystem 통합 |

## 3. references/ 핵심 정책 (cross-reference 가 가장 잦은 곳)

| 파일 | 역할 |
| -- | -- |
| `07_ProfilingScopeRule.md` | TRACE_CPUPROFILER_EVENT_SCOPE 의무 (모든 Tick/Update/Notify) |
| `09_GlobalIteratorPolicy.md` | TObjectIterator/TActorRange 금지 + 등록 패턴 |
| `10_ComponentPolicies.md` | UPROPERTY + TObjectPtr + Mobility 등 6대 정책 |
| `11_AssetLoadingPolicy.md` | SoftObjectPtr + StreamableManager + 4단 패턴 |
| `12_AssetOptimizationPolicy.md` | Bone LOD + URO + Significance 통합 |
| `15_EvaluatorRecipe.md` | 8단계 평가 (Generator/Evaluator 분리) |
| `16_PolicyPriority.md` | Article 1~10 |
| `17_QualityCriteria.md` | 100점 채점 |
| `18_ModelEvolutionAudit.md` | 분기별 staleness 8단계 |
| `19_ExternalSourcesGuide.md` | 외부 출처 인용 가이드 |

본 vault 의 `CLAUDE.md` (스키마) 는 위 정책들 중 핵심을 단순화·일반화한 형태. ingest 시 LLM 이 두 schema 간 매핑을 자동 인식해야.

## 4. 다음 단계 (사용자)

### 4.1. 즉시 검증

```bash
cd E:\MCWiki
python tools/lint.py            # raw/ 는 lint 대상 아님 — wiki/ 만
python tools/stats.py            # raw_files: 180 표시
```

### 4.2. 첫 ingest (single)

가장 작은 것부터:

```bash
python tools/ingest_seed.py \
  "UE Animation 카테고리" \
  raw/ue-wiki-llm/skills/Animation/SKILL.md \
  text \
  --slug ue-animation
```

→ Claude Code 에서: `"wiki/sources/ue-animation.md 를 ingest 마무리. CLAUDE.md §5.1 따라 entity (UAnimInstance, FAnimInstanceProxy 등) + concept (URO, Inertialization 등) 페이지 자동 생성."`

### 4.3. batch ingest (한 번에 여러 개)

```bash
python tools/bulk_seed.py raw/ue-wiki-llm/skills/Animation/
# → wiki/sources/ 에 8 개 stub 자동 생성, log.md 에 batch entry.
# 이후 LLM 에 발화: "방금 seed 한 8 개 stub 의 본문을 우선순위대로 ingest"
```

### 4.4. 카테고리 정복

`skills/CoreUObject/` (14 sub-skill) → `skills/Components/` (18) → ... 우선순위 순서대로 (위 §2 표).

총 129 sub-skill 을 모두 정복하면, 이 vault 가 사용자의 기존 ue-wiki-llm plugin 의 *재합성된 압축본* 이 된다 (Karpathy 의 "compounding artifact").

## 5. 영향받지 않은 원본

원본 (`C:\Unreal\UnrealEngine\LLM_Wiki`) 은 **건드리지 않음**. 본 폴더는 그것의 *복사본*. 원본의 변경은 본 vault 에 자동 반영되지 않음 — 갱신이 필요하면 사용자가 다시 sync (`cp -r ...`) 하거나 LLM 에 "sync raw/ue-wiki-llm/ from C:\Unreal\UnrealEngine\LLM_Wiki" 발화.

## 6. 충돌 (raw vs vault schema)

원본의 `references/15_EvaluatorRecipe.md` 등은 본 vault 의 `00_meta/03_EvaluatorRecipe.md` 와 *유사* 하지만 *다른 도메인용*. ingest 시 LLM 은:

- 본 vault 의 `CLAUDE.md` 를 schema 로 절대시.
- raw 의 references 는 *content* 로 다룸 (entity/concept 페이지로 흡수).
- 같은 이름의 정책이 raw 에 있어도 본 vault 의 `CLAUDE.md` 가 항상 우선.
