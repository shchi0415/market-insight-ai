
import json
from pathlib import Path

import marketing_strategy_engine
import strategy_generation_engine
import strategy_evidence_engine
import pdf_report_engine


def run_strategy_pipeline(
    project_dir,
    api_key,
    font_dir=None,
    progress_callback=None,
    reuse_existing=True
):
    # ===== STEP 27-10D-2: PIPELINE ROLLBACK =====
    backup_dir = None
    try:
        project_dir = Path(project_dir)
        strategy_dir = project_dir / "marketing_strategy"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        def progress(step, message):
            if progress_callback:
                progress_callback(step, message)

        # ===== STEP 27-8I-2: PRECHECK =====
        # 입력 데이터를 다시 생성하기 전에 현재 버전 확인
        import strategy_version_engine

        precheck = strategy_version_engine.check_source_version(
            project_dir
        )

        existing_strategy = (
            strategy_dir / "strategy_v2.json"
        )

        if reuse_existing and existing_strategy.exists():
            if precheck.get("status") != "기록된 파일과 일치":
                raise ValueError(
                    "기존 전략의 데이터 버전이 확인되지 않거나 "
                    "분석 데이터가 변경되었습니다. "
                    "새로운 Gemini 전략을 생성해주세요."
                )

        # ===== STEP 27-10C: EARLY BACKUP =====
        # 신규 전략 생성 시 입력 데이터 갱신 전에 기존 결과 백업
        if not reuse_existing:
            import strategy_backup_engine

            backup_dir = strategy_backup_engine.backup_strategy(
                project_dir=project_dir
            )

        # 1. 현재 프로젝트의 시장 데이터 및 검증 인사이트 통합
        progress(1, "시장 데이터 및 소비자 인사이트 통합 중")

        strategy_input, input_path = (
            marketing_strategy_engine.build_strategy_input(
                project_dir=project_dir,
                max_evidence=100
            )
        )

        evidence_count = len(
            strategy_input.get("evidence", [])
        )

        if evidence_count == 0:
            raise ValueError(
                "전략 생성에 사용할 근거 인사이트가 없습니다. "
                "소비자 인사이트 검증을 먼저 진행해주세요."
            )

        # 2. Gemini 전략 생성
        progress(2, "Gemini 시장 진입 전략 생성 중")

        strategy_path = strategy_dir / "strategy_v2.json"

        if reuse_existing and strategy_path.exists():

            # ===== STEP 27-8E: REUSE SAFETY CHECK =====
            import strategy_version_engine

            version_check = strategy_version_engine.check_source_version(
                project_dir
            )

            if version_check.get("status") != "기록된 파일과 일치":
                raise ValueError(
                    "기존 전략의 데이터 버전을 확인할 수 없거나 "
                    "분석 데이터가 변경되었습니다. "
                    "새로운 Gemini 전략을 생성해주세요."
                )

            with open(strategy_path, encoding="utf-8") as f:
                strategy = json.load(f)

            gemini_called = False
        else:
            if not api_key:
                raise ValueError("Gemini API 키가 없습니다.")

            strategy = strategy_generation_engine.generate_strategy(
                strategy_input_path=input_path,
                output_path=strategy_path,
                api_key=api_key
            )
            gemini_called = True

            # 데이터 버전은 전체 파이프라인 성공 후 기록

        # 3. 전략별 근거 ID 존재 여부 확인
        progress(3, "전략별 댓글 근거 확인 중")

        audit, audit_path = (
            strategy_evidence_engine.verify_strategy_evidence(
                project_dir=project_dir
            )
        )

        # 4. 전략별 소비자 반응 및 검증 과제 구조화
        progress(4, "전략 근거 구조화 중")

        structured = []

        for item in audit.get("opportunity_audits", []):
            evidence = item.get("evidence_details", [])

            posts = {
                str(e.get("source_url", "")).strip().rstrip("/")
                for e in evidence
                if str(e.get("source_url", "")).strip()
            }

            needs = []

            if len(evidence) < 3:
                needs.append(
                    "근거 댓글 수가 제한적이므로 추가 소비자 조사 필요"
                )

            if len(posts) <= 1:
                needs.append(
                    "다른 게시물에서도 동일한 소비자 니즈가 확인되는지 검증 필요"
                )

            needs.extend([
                "제품 효능 및 실제 사용 경험 검증",
                "구매 의향과 지불의사 확인",
                "시장 규모 및 경쟁 제품 조사"
            ])

            structured.append({
                "opportunity_number": item.get(
                    "opportunity_number"
                ),
                "opportunity_name": item.get(
                    "opportunity_name", ""
                ),
                "observed_facts": [
                    {
                        "fact": e.get("validated_insight", ""),
                        "comment": e.get("consumer_comment", ""),
                        "source_url": e.get("source_url", ""),
                        "comment_key": e.get("comment_key", "")
                    }
                    for e in evidence
                ],
                "strategic_hypothesis": {
                    "market_opportunity": item.get(
                        "opportunity_name", ""
                    ),
                    "target_customer": item.get(
                        "target_customer", ""
                    ),
                    "positioning": item.get(
                        "positioning", ""
                    )
                },
                "evidence_summary": {
                    "comment_count": len(evidence),
                    "unique_post_count": len(posts),
                    "evidence_status": item.get(
                        "evidence_status", ""
                    )
                },
                "validation_needs": needs,
                "status": "추가 검증이 필요한 전략 가설"
            })

        structured_result = {
            "project": project_dir.name,
            "opportunities": structured,
            "methodology_note": (
                "AI가 판정한 댓글 근거를 기반으로 작성한 "
                "전략 가설이며 인간의 최종 검증을 의미하지 않습니다."
            )
        }

        structured_path = (
            strategy_dir / "strategy_structured.json"
        )

        with open(structured_path, "w", encoding="utf-8") as f:
            json.dump(
                structured_result,
                f,
                ensure_ascii=False,
                indent=2
            )

        # 5. 최신 Markdown 보고서 생성
        progress(5, "Markdown 전략 보고서 생성 중")

        lines = []

        def add(value=""):
            lines.append(str(value))

        add("# AI 기반 시장 진입 전략 보고서")
        add()
        add("> Instagram 댓글 기반 초기 시장 진입 전략 가설입니다.")
        add("> AI 근거 판정은 인간의 최종 검증이 아닙니다.")
        add()

        add("## 1. Executive Summary")
        add()
        add(strategy.get("executive_summary", ""))
        add()

        add("## 2. Market Trends")
        add()

        overview = strategy_input.get("market_overview", {})
        consumer = strategy_input.get("consumer_insights", {})

        add(f"- AI 분석 댓글: {overview.get('analyzed_comments', '확인 필요')}개")
        add(f"- 스킨케어 관련 댓글: {overview.get('relevant_comments', '확인 필요')}개")
        add(f"- 검증한 인사이트: {consumer.get('total_validated', 0)}개")
        add(f"- 전략 근거 후보: {consumer.get('eligible_evidence', 0)}개")
        add()

        add("## 3. Consumer Insights")
        add()

        for name, count in consumer.get(
            "concern_distribution", {}
        ).items():
            add(f"- {name}: {count}개")

        add()
        add("위 분포는 자동 검증을 통과한 근거 후보에 한정됩니다.")
        add()

        add("## 4. Market Entry Opportunities")
        add()

        for op in structured:
            add(
                f"### 가설 {op['opportunity_number']}. "
                f"{op['opportunity_name']}"
            )
            add()

            hypothesis = op["strategic_hypothesis"]
            summary = op["evidence_summary"]

            add(
                f"**타깃 고객 가설:** "
                f"{hypothesis['target_customer']}"
            )
            add(
                f"**포지셔닝 가설:** "
                f"{hypothesis['positioning']}"
            )
            add(
                f"**근거 댓글:** {summary['comment_count']}개"
            )
            add(
                f"**고유 게시물:** {summary['unique_post_count']}개"
            )
            add(
                f"**근거 수준:** {summary.get('evidence_status', '평가 정보 없음')}"
            )
            add(
                "**해석:** 내부 근거 수량 점검 결과이며, "
                "통계적 신뢰도 또는 전략 성공 확률을 의미하지 않습니다."
            )
            add()

            for evidence in op["observed_facts"]:
                add(
                    f"- AI 판정 인사이트: {evidence['fact']}"
                )
                add(
                    f"  - 원문: {evidence['comment']}"
                )
                add(
                    f"  - 출처: {evidence['source_url']}"
                )

            add()
            add("**추가 검증 과제**")

            for need in op["validation_needs"]:
                add(f"- {need}")

            add()

        add("## 5. STP & Positioning Strategy")
        add()

        recommended = strategy.get(
            "recommended_strategy", {}
        )

        for label, key in [
            ("Targeting", "targeting"),
            ("Positioning", "positioning"),
            ("Product Direction", "product_direction"),
            ("Core Message", "messaging"),
            ("Channel Strategy", "channel_strategy")
        ]:
            add(
                f"- **{label}:** "
                f"{recommended.get(key, '')}"
            )

        add()
        add("## 6. Marketing Action Plan")
        add()

        for action in recommended.get(
            "execution_plan", []
        ):
            add(f"### {action.get('action', '')}")
            add(f"- 목적: {action.get('purpose', '')}")
            add(f"- KPI: {action.get('kpi', '')}")
            add()

        add("## 7. Validation Roadmap")
        add()

        for index, experiment in enumerate(
            strategy.get("validation_experiments", []),
            start=1
        ):
            add(f"### 실험 {index}")
            add(
                f"- 가설: {experiment.get('hypothesis', '')}"
            )
            add(
                f"- 방법: {experiment.get('experiment', '')}"
            )
            add(
                f"- 지표: {experiment.get('metric', '')}"
            )
            add(
                f"- 의사결정 기준: "
                f"{experiment.get('decision_rule', '')}"
            )
            add()

        add("## 8. Research Limitations")
        add()

        for limitation in strategy_input.get(
            "research_limitations", []
        ):
            add(f"- {limitation}")

        add()
        add("---")
        add(
            "본 보고서는 후속 시장조사 및 제품 검증을 위한 "
            "의사결정 보조 자료입니다."
        )

        md_path = (
            strategy_dir / "market_strategy_report_v2.md"
        )

        md_path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        # 6. Noto Sans KR PDF 생성
        progress(6, "PDF 보고서 생성 중")

        pdf_path = pdf_report_engine.generate_pdf_report(
            project_dir=project_dir,
            font_dir=(font_dir or Path(__file__).resolve().parent / "fonts")
        )

        # ===== STEP 27-8H: SAVE VERSION AFTER SUCCESS =====
        # 새 Gemini 전략을 생성한 경우에만 버전 기록
        if gemini_called:
            import strategy_version_engine

            strategy_version_engine.save_source_version(
                project_dir=project_dir
            )

        progress(7, "모든 작업 완료")

        return {
            "project": project_dir.name,
            "gemini_called": gemini_called,
            "evidence_count": evidence_count,
            "opportunity_count": len(structured),
            "strategy_input": str(input_path),
            "strategy_json": str(strategy_path),
            "evidence_audit": str(audit_path),
            "structured_json": str(structured_path),
            "markdown_report": str(md_path),
            "pdf_report": str(pdf_path)
        }

    except Exception:
        if backup_dir is not None:
            import strategy_backup_engine
            strategy_backup_engine.restore_strategy(
                project_dir=project_dir,
                backup_dir=backup_dir
            )
        raise
