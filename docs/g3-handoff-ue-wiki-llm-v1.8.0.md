# G3 게이트 작업 인계 — ue-wiki-llm plugin v1.6.0 → v1.8.0 (LevelSequence + SpatialPartition 통합)

> **인계 대상**: ue-wiki-llm plugin 담당 다른 에이전트 (mcwiki main session 영역 X)
> **작성**: 2026-05-15 · mcwiki vault v0.2.1 release 후 + Cycle #11/#12 ingest 완료
> **목적**: Phase II G3 게이트 통과 — `ue-spatial-partition-specialist` + `ue-levelsequence-specialist` plugin 활성화 + orchestrator §5.4 (6단 self-check) 명문화
> **이전 버전**: `g3-handoff-ue-wiki-llm-v1.7.0.md` (1 agent 만, Cycle #11 시점) — 본 v1.8.0 으로 *대체*

---

## 0. 현 상태 (2026-05-15)

### Plugin 권한 매트릭스

| 항목 | raw (E:\MCWiki\raw\ue-wiki-llm\) | plugin (Cowork install) |
|------|----------------------------------|------------------------|
| **agent** `ue-spatial-partition-specialist.md` | ✅ 존재 (189L) | ❌ 누락 (Cycle #11) |
| **agent** `ue-levelsequence-specialist.md` | ✅ 존재 (250L) | ❌ 누락 (Cycle #12) |
| **skills/SpatialPartition/** | ✅ 5 파일 | ❌ 없음 |
| **skills/LevelSequence/** | ✅ 11 파일 (SKILL + 10 ref) | ❌ 없음 |
| **agents/ue-orchestrator.md** §5.4 | ⚠ `[SpatialPartition]` + `[LevelSequence]` prefix 만 | ⚠ §5.4 boundary protocol 섹션 없음 |
| **plugin.json** | — | v1.6.0 |

→ **2 agent + 2 skills 디렉토리 + orchestrator §5.4** 모두 plugin 측 갱신 필요.

### Plugin 위치

- **Windows 원본 (사용자 빌드 source)**: `C:\Unreal\UnrealEngine\LLM_Wiki\`
- **Mount path (read-only)**: `/sessions/pensive-gracious-franklin/mnt/.remote-plugins/plugin_019SPM4GSPfAfagqWFsrexY4/`
- **Cowork install path**: `C:\Users\김민철\AppData\Roaming\Claude\local-agent-mode-sessions\11afa6ca-099c-461d-91ad-c4ce8c45ecff\3e9ec507-52ef-4d6f-92ee-3b9186b79803\rpm\plugin_019SPM4GSPfAfagqWFsrexY4\`

---

## 1. 필요 변경 7건 (v1.7.0 — 1 agent vs v1.8.0 — 2 agent)

| # | 작업 | 출발지 → 도착지 |
|---|------|----------------|
| 1 | `plugin.json` version + description + keywords | v1.6.0 → **v1.8.0** |
| 2 | agent (Cycle #11) | `raw/agents/ue-spatial-partition-specialist.md` → `plugin/agents/` |
| 3 | agent (Cycle #12) ⭐ | `raw/agents/ue-levelsequence-specialist.md` → `plugin/agents/` |
| 4 | skills (Cycle #11) | `raw/skills/SpatialPartition/*` → `plugin/skills/SpatialPartition/*` (5 파일) |
| 5 | skills (Cycle #12) ⭐ | `raw/skills/LevelSequence/*` → `plugin/skills/LevelSequence/*` (11 파일) |
| 6 | orchestrator §5.4 섹션 삽입 | `plugin/agents/ue-orchestrator.md` 의 `## 출력 형식` 앞에 §5.4 본문 (6단 self-check) |
| 7 | `.mcpb` 재빌드 | `mcpb pack .` → `dist/ue-wiki-llm-1.8.0.mcpb` |

### orchestrator §5.4 본문 (Self-check 6단 v0.4 기준)

```markdown
## §5.4 Agent Boundary Protocol (vault 와의 인터페이스 의무)

> Vault 와 통신하는 도구 (`mcwiki` MCP) 는 main Cowork 만 보유. specialist 는 raw/wiki 파일 시스템만 접근 → §5.2 QUERY workflow 가 specialist 안에서 시행 불가 → **main 이 boundary 마다 §5.2 를 wrap**.

### 5단계 boundary

```
[A] PRE-DELEGATE  vault 정찰 (read_index + search + read_page)
        ↓
[B] DELEGATE      Task(specialist, prompt) — vault 컨텍스트 + §13 의무 명시
        ↓
[C] POST-RECEIVE  (1) §13 tier 분해 (🟢/🟡/🔴) + 보너스 발견
                  (2) 5-tier 카운트 정합 검사 (자산 추가/제거 cycle)
        ↓
[D] FILE-BACK     사용자 OK 게이트 → write_page / synthesis_finalize
        ↓
[E] LOG           append_log (op=query|synthesis|...) 의무
```

### POST-RECEIVE 검증 의무 (2026-05-13 보강)

- ❌ bash `wc -c` / `ls -la` 단독 의존 금지 — mount stale false negative 위험
- ✅ file `Read` tool 또는 mcwiki `read_page` — vault 의 진짜 view
- ⭐ 두 방법 cross-check 권장

### Specialist 권한 매트릭스

| 작업 | Specialist | main (orchestrator) |
|------|-----------|---------------------|
| raw/wiki 파일 Read/Write | ✅ | ✅ |
| mcwiki MCP (read_index / search / read_page) | ❌ | ✅ |
| mcwiki MCP (write_page / append_log / synthesis_*) | ❌ | ✅ |
| log.md 직접 edit (Bash) | ❌ 금지 (mcwiki append_log 의무) | — |

### Self-check 6단 (2026-05-13 v0.4 확장)

| 단계 | self-check |
|------|-----------|
| §A | read_index + search + read_page 호출 했나? |
| §B | prompt 안 vault 컨텍스트 + §13 의무 명시? |
| §C-1 | specialist 반환을 §13 tier 분류 표 작성? |
| §C-2 | 자산 추가/제거 시 5-tier 카운트 정합 검사? (자산 변경 없는 cycle 은 N/A) |
| §D | 사용자 OK 게이트 거쳤나? |
| §E | append_log 호출? cycle 측정 데이터 포함? |

6/6 ✅ = cycle 인정.

### Cycle 등재 표준

매 specialist 호출 후 main 이:

1. `read_page kind=synthesis slug=agent-boundary-cycles-2026-q2` — cycle 로그 읽음
2. `write_page` — §4 cycle 로그에 새 entry append
3. 집계 메트릭 갱신 + G2 진행률 갱신
4. cycle #10 도달 시 Phase II 결정 트리 적용

> 정밀판: `00_meta/07_AgentBoundaryProtocol.md` · 마스터: `CLAUDE.md §5.4`
```

---

## 2. 자동화 도구 — `tools/pack-plugin.ps1` 갱신 권장

기존 `tools/pack-plugin.ps1` 은 v1.7.0 (1 agent) 기준. v1.8.0 (2 agent) 빌드 시 *2 가지 옵션*:

**옵션 A — 스크립트 그대로 + 수동 1 회 추가** (간단):
```powershell
# 1. 스크립트 실행 (SpatialPartition 만 자동)
E:\MCWiki\tools\pack-plugin.ps1 -DryRun
E:\MCWiki\tools\pack-plugin.ps1

# 2. 본 빌드 *전* 또는 *후* 에 LevelSequence 수동 복사
robocopy E:\MCWiki\raw\ue-wiki-llm\skills\LevelSequence C:\Unreal\UnrealEngine\LLM_Wiki\.claude-plugin\skills\LevelSequence /E
copy E:\MCWiki\raw\ue-wiki-llm\agents\ue-levelsequence-specialist.md C:\Unreal\UnrealEngine\LLM_Wiki\.claude-plugin\agents\

# 3. (스크립트 안 mcpb pack 단계가 이미 발생했다면) 재빌드
cd C:\Unreal\UnrealEngine\LLM_Wiki
Remove-Item dist\ue-wiki-llm-*.mcpb -Force
mcpb pack . dist\ue-wiki-llm-1.8.0.mcpb
```

**옵션 B — 스크립트 갱신** (정합):
- `pack-plugin.ps1` 의 §3 단계 (skills 복사) 에 LevelSequence 도 추가
- §4 단계 (plugin.json) version 1.8.0 + LevelSequence keywords 추가
- 향후 plugin 빌드 시 항상 정합

본 인계 문서 §3 (plugin.json 본문) 에 v1.8.0 본문 stage. 스크립트 갱신은 별도 후속 작업.

---

## 3. 수동 단계 (자동화 스크립트 미사용 시)

```powershell
# 0. 작업 디렉토리 이동
cd C:\Unreal\UnrealEngine\LLM_Wiki

# 1. Backup
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
Compress-Archive -Path .claude-plugin -DestinationPath "backup-pre-v1.8.0-$ts.zip" -Force

# 2. SpatialPartition 5 + agent 1 = 6 파일 (Cycle #11)
robocopy E:\MCWiki\raw\ue-wiki-llm\skills\SpatialPartition .claude-plugin\skills\SpatialPartition /E
copy E:\MCWiki\raw\ue-wiki-llm\agents\ue-spatial-partition-specialist.md .claude-plugin\agents\

# 3. LevelSequence 11 + agent 1 = 12 파일 (Cycle #12)
robocopy E:\MCWiki\raw\ue-wiki-llm\skills\LevelSequence .claude-plugin\skills\LevelSequence /E
copy E:\MCWiki\raw\ue-wiki-llm\agents\ue-levelsequence-specialist.md .claude-plugin\agents\

# 4. plugin.json 갱신 (§4 본문 참조)
notepad .claude-plugin\plugin.json

# 5. ue-orchestrator.md §5.4 섹션 삽입 (## 출력 형식 앞에 — §1 본문 참조)
notepad .claude-plugin\agents\ue-orchestrator.md

# 6. mcpb 재빌드
mcpb pack . dist\ue-wiki-llm-1.8.0.mcpb

# 7. 검증
python -c "import zipfile, json; z=zipfile.ZipFile('dist/ue-wiki-llm-1.8.0.mcpb'); m=json.loads(z.read('.claude-plugin/plugin.json').decode()); print('version:', m['version']); print('keywords:', len(m['keywords']))"

# 8. Cowork uninstall (v1.6.0) → install (v1.8.0) → 재시작
```

---

## 4. `plugin.json` 새 본문 (v1.8.0 — 2 agent 통합)

```json
{
  "name": "ue-wiki-llm",
  "version": "1.8.0",
  "description": "Unreal Engine 5.7.4 LLM Wiki — 21 카테고리 + 145+ sub-skill (Render 12 — RDG/Shader/Material/MaterialExpression/SceneViewExtension/MeshDrawing/PostProcess/Lumen+Nanite/RHI/Vulkan/Mobile/VR + SpatialPartition 4 — TOctree2/TQuadTree/StaticSpatialIndex/WorldPartitionRuntime + LevelSequence 10 — MovieScene/Tracks/LevelSequencePlayer/Director/CineCamera/Sequencer/MovieRenderPipeline/EntitySystemECS/SequencerScripting/TemplateSequence + Subsystem 2 — 5종+Online) + 15 횡단 인덱스 + Evaluator Workflow + §5.4 Agent Boundary Protocol (6단 self-check) + 15 specialist (spatial-partition + levelsequence 신규). Cross-Platform 게임 (DX12/Vulkan/Metal) + Mobile 60fps + VR 90fps + Online + 대규모 월드 (1km+) AActor 공간 인덱싱 + 시네마틱/컷씬/Movie Render Queue 표준 통합. Generator/Evaluator 분리.",
  "author": {"name": "민철", "email": "sensr7086@naver.com"},
  "homepage": "https://github.com/sensr7086/ue-wiki-llm",
  "license": "MIT",
  "keywords": ["unreal-engine", "ue5", "ue-5.7", "cpp", "gamedev", "slate", "umg", "components", "gameframework", "subsystem", "editor", "animation", "blueprint", "networking", "ai", "build", "metasound", "render", "rdg", "shader", "lumen", "nanite", "rhi", "vulkan", "mobile", "vr", "online", "spatial-partition", "octree", "worldpartition", "levelsequence", "sequencer", "cinematic", "moviescene", "cinecamera", "movierenderpipeline", "wiki", "evaluator", "boundary-protocol", "korean"]
}
```

---

## 5. 검증 (install 후)

### Cowork UI 안

```
1. Plugin 관리 → ue-wiki-llm v1.8.0 확인
2. Task tool spawn — 2 agent 활성 확인:
   - ue-wiki-llm:ue-spatial-partition-specialist
   - ue-wiki-llm:ue-levelsequence-specialist
3. prefix 명령 라우팅 동작:
   - [SpatialPartition] / [Octree] / "다수 AActor 반경 쿼리"
   - [LevelSequence] / [Sequencer] / "시네마틱 컷씬"
4. orchestrator system_prompt 안 §5.4 6단 self-check 노출 확인
```

### .mcpb 사전 검증

```powershell
python -c "import zipfile, json; z=zipfile.ZipFile('dist/ue-wiki-llm-1.8.0.mcpb'); m=json.loads(z.read('.claude-plugin/plugin.json').decode()); print('version:', m['version']); print('keywords:', len(m['keywords']))"
# 예상: version: 1.8.0 / keywords: 40+
```

---

## 6. G3 통과 후 Phase II 게이트 진행

| 게이트 | 통과 후 상태 |
|--------|-------------|
| G1 (1개월 MCP 안정) | 🟡 진행 — mcwiki v0.2.1 install (2026-05-13) → **2026-06-13~14 자동 PASS** |
| ✅ G2 (10 cycle 검증) | PASS (10/10 + 보너스 37건) |
| ⏳ G3 (orchestrator §5.4) | **본 작업 통과 시 PASS** |

→ 3 게이트 모두 통과 시 **Phase II C 적용 검토 시작** = orchestrator agent 에 mcwiki MCP 6종 권한 추가 (별도 plugin upgrade — v1.9.0 후보).

---

## 7. Cross-link

- [[CLAUDE.md#§5.4]] — 마스터 schema §5.4 boundary protocol
- [[00_meta/07_AgentBoundaryProtocol]] — 정밀판 (§2.4 5-tier + §5.1 POST-RECEIVE 검증)
- [[synthesis/agent-boundary-cycles-2026-q2]] — G2 게이트 cycle 로그
- [[sources/ue-agent-spatial-partition]] — Cycle #11 agent
- [[sources/ue-agent-levelsequence]] — Cycle #12 agent
- [[sources/ue-spatialpartition-skill]] — 20번째 카테고리
- [[sources/ue-levelsequence-skill]] — 21번째 카테고리

---

## 8. 작업 완료 보고

작업 완료 시 vault 측에 통보 (수동):

```text
mcwiki:append_log
  op=feature
  title="G3 게이트 PASS — ue-wiki-llm v1.8.0 release"
  body="plugin 15 agents 활성 (spatial-partition + levelsequence 추가) + 2 카테고리 (SpatialPartition + LevelSequence) + orchestrator §5.4 (6단 self-check) 명문화 + Phase II G3 통과 ..."
```

또는 main session 에 단순 보고. main 이 vault entry append.

다음 cycle 부터 orchestrator 가 §5.4 boundary protocol 자동 적용 → main wrap 부담 ↓.

---

## 9. 직전 v1.7.0 인계 문서 처리

- `docs/g3-handoff-ue-wiki-llm-v1.7.0.md` = 본 v1.8.0 으로 *대체*
- v1.7.0 = SpatialPartition (Cycle #11) 만 / v1.8.0 = + LevelSequence (Cycle #12)
- v1.7.0 적용 *전* → 본 v1.8.0 만 적용
- v1.7.0 적용 *후* → LevelSequence (변경 3+5) + orchestrator §5.4 갱신 (§5.4 본문 자체는 v1.7.0 과 동일 — 본 §1 본문 그대로)
