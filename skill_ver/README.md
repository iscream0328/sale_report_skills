# Skill Ver: 브랜드 URL 기반 포트폴리오 매칭 워크플로우

이 폴더는 기존 `api/`, `web/` 프로그램과 분리된 기획/스펙 공간이다. 현재 앱 구현을 건드리지 않고, 자사몰 또는 인스타 URL을 입력해 브랜드 이미지를 분석한 뒤 보유 포트폴리오와 연결하는 별도 워크플로우를 설계한다.

## 목표

브랜드 URL 하나로 아래 산출물을 만든다.

1. 브랜드 페이지에서 상품 이미지 10장, 기획전/콜라보/프로젝트 이미지 10장 후보 수집
2. 보유 포트폴리오와 유사한 이미지 5장 추천
3. 보유 포트폴리오와 반대되거나 보완되는 이미지 5장 추천
4. 사용자가 영업에 보낼 포트폴리오 이미지를 직접 선택
5. 선택 결과를 바탕으로 영업 메일 초안과 이미지 포함 제안서 초안 생성

## 선행 작업

가장 먼저 `portfolio/` 폴더의 이미지를 메타화한다. 기존 이미지 파일은 그대로 두고, 분석 결과만 별도 인덱스로 만든다.

권장 출력:

- `skill_ver/data/portfolio_index.jsonl`: 포트폴리오 이미지별 검색/매칭 메타
- `skill_ver/data/portfolio_embeddings.jsonl`: 이미지/텍스트 임베딩 또는 벡터 참조
- `skill_ver/data/portfolio_review_notes.jsonl`: 사람이 수정한 태그와 제안 문구

위 `data/` 출력물은 추후 구현 단계에서 만들 예정이며, 현재는 기획 문서와 스키마만 정의한다.

## 문서 구성

- `01_workflow_plan.md`: 전체 제품 흐름과 구현 단계
- `02_portfolio_metadata_plan.md`: 포트폴리오 사전 메타화 기준
- `03_matching_and_proposal_spec.md`: 유사/반대 매칭과 메일/제안서 생성 기준
- `04_brand_url_matching_workflow.md`: 브랜드 URL 이미지 수집과 포트폴리오 유사/보완 10개 추천 실행 기준
- `schemas/portfolio_image.schema.json`: 포트폴리오 이미지 메타 스키마
- `schemas/brand_source_image.schema.json`: 브랜드 URL에서 수집한 이미지 메타 스키마
- `schemas/brand_portfolio_match_result.schema.json`: 유사/보완 추천 결과 스키마
- `prompts/analysis_and_proposal_prompts.md`: 이미지 분석/제안서 생성 프롬프트 초안

## 운영 원칙

- 자동 추천은 최종 발송물이 아니라 담당자 선택을 돕는 큐레이션이다.
- 인스타그램은 자동 수집 안정성과 권한 문제가 있으므로, MVP에서는 공개 URL 수집 실패 시 사용자 업로드 또는 승인된 export를 대체 경로로 둔다.
- 브랜드에게 보내는 제안서에는 사용자가 선택한 이미지와 명확히 연결되는 주장만 쓴다.
- "반대되는 이미지"는 무작위로 다른 이미지를 뜻하지 않는다. 현재 브랜드 이미지에서 부족한 컷 유형, 톤, 커머스 역할을 보완하는 전략적 대비 이미지로 정의한다.
