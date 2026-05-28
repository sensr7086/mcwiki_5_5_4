---
type: meta
title: "Vault Citation & Inference Disclosure Rule"
slug: 06_VaultCitationRule
created: 2026-05-11
last_updated: 2026-05-11
tags: [meta, governance, citation, inference]
---

# Vault Citation & Inference Disclosure Rule

> 본 룰은 mcwiki MCP 를 통해 vault 를 *읽고 답변하는* 모든 agent (Cowork / Claude Code / specialist subagent) 에게 의무 적용된다. CLAUDE.md §13 의 정밀판.
>
> 핵심: **vault 인용과 일반 지식 추론을 *항상* 명시 구분**. "vault 에 있다고 거짓 인용" 또는 "추론을 vault 인 것처럼 위장" 둘 다 금지. 사용자가 한 줄로 vault 의 자산성과 LLM 의 인퍼런스를 식별 가능해야 한다.

## 1. 3-Tier 분류

agent 가 답변에 포함하는 모든 *사실 주장* 은 다음 3 tier 중 하나로 명시:

| Tier | 의미 | 마커 |
| -- | -- | -- |
| **🟢 VAULT** | `read_page` / `read_raw` / `search` 결과로 *직접 확인* | `[[wikilink]]` 인용 또는 `wiki://uri` |
| **🟡 PARTIAL** | vault 에서 *근거 일부* 만 발견 + agent 가 *조합·외삽* 한 부분 | "(vault 근거: [[…]] · 외삽)" 같은 짧은 주석 |
| **🔴 INFERRED** | vault 에 *없음* — 일반 지식 / 코드 베이스 추론 / 외부 docs | "**추론** (vault 미확정)" 같은 prefix 또는 별도 섹션 |

🔴 INFERRED 한 주장은 그대로 두면 *위장된 거짓* 이 된다. 명시는 *불편하지만 강제*.

## 2. 의무 운영 흐름

```text
사용자 질문
  ↓
[Step 1] mcwiki:search query="<keywords>"   → vault 매치 확인
[Step 2] 매치된 페이지를 mcwiki:read_page 로 본문 수집
[Step 3] 본문에서 직접 답 가능?
   ├─ Yes → 🟢 VAULT, [[wikilink]] 인용
   ├─ Partially → 🟡 PARTIAL, 근거 + 외삽 부분 분리 표기
   └─ No  → 🔴 INFERRED 섹션 분리, 매 항목 "vault 미확인" 표시
[Step 4] mcwiki:query_recap 로 filing-back 결정 (특히 🔴 가 가치 있으면 propose_synthesis)
```

## 3. 형식 예시

### ✅ 올바른 답변 형식 (3 tier 명시)

```markdown
**🟢 vault 인용**:

- [[entities/UStaticMeshComponent]] 의 `SetStaticMesh()` 는 BeginPlay 후 호출 시 collision 재계산 트리거.
- [[concepts/Asset-Loading-Policy]] 5대 정책 중 #3 (Soft-Reference + StreamableManager) 적용.

**🟡 PARTIAL — vault 근거 + 외삽**:

- AssetEditorSubsystem 의 OnAssetOpenedInEditor 이벤트가 존재함 ([[sources/ue-editor-assettools]] L190 — "AssetEditorSubsystem" 언급 3건만). 시그니처 (UObject*, IAssetEditorInstance*) 는 vault 에 없음 — 외삽.

**🔴 INFERRED — vault 미확정 (내 일반 UE 지식)**:

1. `IStaticMeshEditor::GetStaticMeshComponent()` 시그니처 — vault 미확인
2. `EditorName == FName("StaticMeshEditor")` 문자열 — vault 미확인
3. `static_cast<IStaticMeshEditor*>(IAssetEditorInstance*)` 의 안전성 — "UE 표준" 이라 했지만 vault 확인 안 됨, 내 일반 지식
```

### ❌ 위반 예시

```markdown
UStaticMeshComponent 의 SetStaticMesh 는 BeginPlay 후 호출 시 collision 재계산 트리거. 또한
IStaticMeshEditor::GetStaticMeshComponent() 가 mesh editor instance 에서 component 를 반환하며,
EditorName 으로 "StaticMeshEditor" 문자열을 식별할 수 있다.
```

위 답변은 첫 문장은 🟢 VAULT, 나머지 두 문장은 🔴 INFERRED 인데 *구분 없이 평등하게 진술* — 룰 위반. 사용자가 어느 부분이 검증된 자산이고 어느 부분이 LLM 의 추측인지 알 수 없다.

## 4. "vault 검색했지만 결과 없음" — 추론 의존부 분리 의무

`search` 가 0 hits 였거나, 매치된 페이지를 read_page 했는데 답이 안 보이면 그 부분은 **무조건 🔴 INFERRED 섹션** 으로 분리. 적어도 두 가지를 명시:

1. **vault 에 없다는 사실** — "vault 검색했지만 결과 없음" 또는 "vault 에 시그니처 미확정"
2. **추론의 근거** — "일반 UE 지식 / 코드 베이스 추론 / 외부 docs (Epic 공식 문서 등)"

예시 — 화면에서 본 *모범 답안*:

```markdown
### vault 검색했지만 결과 없음 — 추론에 의존한 부분

직전 search 결과:
- `FAdvancedPreviewScene` → no hits
- `IStaticMeshEditor` → no hits
- `GetPreviewMeshComponent` → no hits
- `OnAssetOpenedInEditor` → L190·L85·L225 3건만 — 정확한 시그니처 (UObject*, IAssetEditorInstance*)* 는 vault 에 안 적혀있음

### 즉, 다음은 내 일반 UE 지식 / 추론 — vault 확정 X

1. UAssetEditorSubsystem::OnAssetOpenedInEditor() 가 2-param event (UObject*, IAssetEditorInstance*) — vault 에는 hit 만, 시그니처 미확정.
...
```

이 형식이 *룰의 정확한 구현*.

## 5. filing-back 의무 — INFERRED 가 검증되면 vault 화

🔴 INFERRED 로 답한 부분이 *코드 베이스에서 검증* 되거나 *공식 docs 로 확인* 되면, `mcwiki:write_page` 로 해당 슬러그에 추가 (또는 `query_recap mode=append_to_page` 로 자동) — 다음 번엔 🟢 VAULT 가 된다.

가치 있는 인퍼런스는 *임시 보관 → 검증 → vault 편입* 사이클을 가진다. 이게 Karpathy 의 "*살아있는 vault*" 의 핵심.

## 6. 위반 시 evaluator 의 평가 영향

[[sources/ue-agent-evaluator]] 의 평가 항목에 본 룰 위반 시 감점:

- 🔴 부분을 🟢 처럼 위장 → 큰 감점
- 🟡 의 외삽 표시 누락 → 중간 감점
- search 0 hits 인데 INFERRED 분리 섹션 없음 → 큰 감점

평가 기준은 [[sources/ue-ref-17-qualitycriteria]] + 본 룰 cross-check.

## 7. 자동화 — `query_recap` 와의 정합

`mcwiki:query_recap` 호출 시 mode 선택의 기준:

- 답변이 100% 🟢 VAULT — `mode=append_to_log` (가벼운 기록)
- 답변이 🟡 PARTIAL 포함 + 가치 있음 — `mode=append_to_page` (해당 페이지에 Q&A 보강)
- 답변이 🔴 INFERRED 의존인데 가치 있음 — `mode=propose_synthesis` (synthesis 로 정식화 + 추후 검증 대상)
- 일회성 / 가치 낮음 — `mode=skip`

## 8. 한 줄 정리

> **vault 인용과 LLM 추론을 *시각적으로 분리* 하지 않은 답변은 거짓 인용과 같다.** mcwiki 의 모든 agent 는 답변 안에서 🟢 / 🟡 / 🔴 또는 동등 마커로 *항상* 구분.
