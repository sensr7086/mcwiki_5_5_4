---
type: source
title: "UE LLM Wiki — MANIFEST (raw 인벤토리 + Phase 4G 인덱스)"
slug: ue-manifest
source_path: raw/ue-wiki-llm/MANIFEST.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, manifest, index]
---

# UE LLM Wiki — MANIFEST

> Source: [[raw/ue-wiki-llm/MANIFEST.md]]

## 1. Summary

본 vault 의 raw/ue-wiki-llm/ 인벤토리. 18 카테고리 × N sub-skill + references 19 + meta 5 + catalog 2 + docs 2 + READMEs 2. Phase 4G 의 references/catalog/docs/meta source 페이지 인덱스 역할.

## 2. References (19 — UE 정책 / 인덱스 권위 source)

- [[sources/ue-ref-00-readme]] — UE Wiki 진입점 (00 README)
- [[sources/ue-ref-01-layermap]] — L1~L7 의존 계층 (189 모듈)
- [[sources/ue-ref-02-verificationlog]] — 검증 로그 (verified / inferred 분리)
- [[sources/ue-ref-03-wikiharness]] — 시나리오 → sub-skill 매트릭스
- [[sources/ue-ref-04-overrideindex]] — virtual + Super 호출 통합 표
- [[sources/ue-ref-05-editoronlyindex]] — 🛠 Editor only 4단 분리
- [[sources/ue-ref-06-invalidationhotspots]] — Slate Invalidation hotspot 카탈로그
- [[sources/ue-ref-07-profilingscopeRule]] — 🚨 TRACE_CPUPROFILER_EVENT_SCOPE 의무
- [[sources/ue-ref-08-overlaphotspots]] — Overlap 비용 / 핫스팟
- [[sources/ue-ref-09-globaliteratorpolicy]] — 🚨 TActorIterator 사용 금지
- [[sources/ue-ref-10-componentpolicies]] — 🚨 Components 6 대 의무
- [[sources/ue-ref-11-assetloadingpolicy]] — 🚨 어셋 로드 5 대 정책
- [[sources/ue-ref-12-assetoptimizationpolicy]] — 🎯 어셋 최적화 5 대 영역
- [[sources/ue-ref-14-taskhandofftemplate]] — 멀티 세션 인계 표준
- [[sources/ue-ref-15-evaluatorrecipe]] — 8 단계 평가 (Generator/Evaluator)
- [[sources/ue-ref-16-policypriority]] — Tier 1~5 충돌 우선순위
- [[sources/ue-ref-17-qualitycriteria]] — 4 기준 100 점 채점 (UE 특화)
- [[sources/ue-ref-18-modelevolutionaudit]] — 분기별 staleness 감사 (2 축)
- [[sources/ue-ref-19-externalsourcesguide]] — 외부 출처 인용 가이드

## 3. Catalog (2 — 모듈 인덱스)

- [[sources/ue-catalog-runtimeindex]] — Runtime 189 모듈
- [[sources/ue-catalog-editordevindex]] — Editor / Developer 모듈

## 4. Docs (2 — UE 프로젝트 가이드)

- [[sources/ue-docs-claude]] — UE Project CLAUDE.md (명명/디렉토리/스타일)
- [[sources/ue-docs-install]] — 셋업 절차

## 5. Meta (5 — 정직성 / 거버넌스)

- [[sources/ue-meta-honest-limits]] — ⚠️ 6 대 본질 문제 + 현실적 기대치
- [[sources/ue-meta-governance]] — UE 거버넌스 마스터
- [[sources/ue-meta-improvement-roadmap]] — 한계 해결 P0~P3
- [[sources/ue-meta-confidence-tags]] — 3 단계 신뢰도 (verified / grep-listed / inferred)
- [[sources/ue-meta-corrections]] — 사용자 발견 거짓 누적

## 6. Top-level READMEs

- [[sources/ue-readme]] — UE LLM Wiki 메인 README

## 7. Cross-link with vault meta

본 vault 의 [[00_meta/00_QualityCriteria]] / [[00_meta/01_PolicyPriority]] / [[00_meta/03_EvaluatorRecipe]] / [[00_meta/04_AuditPolicy]] / [[00_meta/05_HandoffProtocol]] 와 위 §2 의 references/15-18 가 페어 (CLAUDE.md §0.1.2 매핑).
