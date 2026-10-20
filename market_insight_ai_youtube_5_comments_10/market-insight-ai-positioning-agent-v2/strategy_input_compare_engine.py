
import json
import hashlib
from pathlib import Path

import marketing_strategy_engine


def make_hash(data):
    normalized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )
    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def compare_strategy_input(project_dir):
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"

    saved_path = strategy_dir / "strategy_input.json"

    if not saved_path.exists():
        return {
            "status": "기존 입력 없음",
            "changed": None
        }

    with open(saved_path, encoding="utf-8") as f:
        saved_data = json.load(f)

    # 기존 입력 파일을 변경하지 않도록 별도 임시 프로젝트 사용
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as tmp:
        temp_project = Path(tmp) / project_dir.name
        temp_project.mkdir()

        # 현재 분석 결과만 임시 폴더로 복사
        for relative in [
            "market_trends/overview.json",
            "verified_insights_quality.csv"
        ]:
            src = project_dir / relative
            dst = temp_project / relative

            if not src.exists():
                raise FileNotFoundError(src)

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        new_data, _ = (
            marketing_strategy_engine.build_strategy_input(
                project_dir=temp_project,
                max_evidence=100
            )
        )

        # 임시 프로젝트명은 원본과 같게 생성했으므로
        # 저장된 데이터와 직접 비교 가능
        changed = make_hash(saved_data) != make_hash(new_data)

    return {
        "status": (
            "최신 분석 데이터 변경 감지"
            if changed else "최신 분석 데이터 일치"
        ),
        "changed": changed,
        "saved_evidence_count": len(
            saved_data.get("evidence", [])
        ),
        "current_evidence_count": len(
            new_data.get("evidence", [])
        )
    }
