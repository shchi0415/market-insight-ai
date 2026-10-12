
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


def calculate_input_hash(input_path):
    """전략 입력 JSON의 내용으로 SHA256 해시 계산"""
    input_path = Path(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON 들여쓰기나 키 순서의 차이는 무시
    normalized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def save_strategy_version(project_dir):
    """현재 전략 생성에 사용한 입력 데이터 버전 저장"""
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"

    input_path = strategy_dir / "strategy_input.json"
    strategy_path = strategy_dir / "strategy_v2.json"
    version_path = strategy_dir / "strategy_version.json"

    if not input_path.exists() or not strategy_path.exists():
        raise FileNotFoundError(
            "전략 입력 데이터 또는 전략 결과가 없습니다."
        )

    version = {
        "input_hash": calculate_input_hash(input_path),
        "strategy_file": strategy_path.name,
        "recorded_at_utc": datetime.now(
            timezone.utc
        ).isoformat()
    }

    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(
            version,
            f,
            ensure_ascii=False,
            indent=2
        )

    return version


def check_strategy_version(project_dir):
    """현재 입력 데이터와 저장된 전략 버전 비교"""
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"

    input_path = strategy_dir / "strategy_input.json"
    version_path = strategy_dir / "strategy_version.json"

    if not input_path.exists():
        return {
            "status": "입력 데이터 없음",
            "changed": None
        }

    if not version_path.exists():
        return {
            "status": "버전 기록 없음",
            "changed": None
        }

    with open(version_path, "r", encoding="utf-8") as f:
        saved_version = json.load(f)

    current_hash = calculate_input_hash(input_path)
    saved_hash = saved_version.get("input_hash")

    changed = current_hash != saved_hash

    return {
        "status": (
            "데이터 변경 감지" if changed else "데이터 변경 없음"
        ),
        "changed": changed,
        "current_hash": current_hash,
        "saved_hash": saved_hash
    }


# ===== STEP 27-8B: SOURCE DATA VERSIONING =====

def calculate_file_hash(file_path):
    """파일 내용을 SHA256으로 계산"""
    file_path = Path(file_path)

    digest = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def get_source_fingerprints(project_dir):
    """전략에 사용되는 핵심 분석 결과의 파일 지문"""
    project_dir = Path(project_dir)

    sources = {
        "consumer_insights":
            project_dir / "verified_insights_quality.csv",
        "market_trends":
            project_dir / "market_trends" / "overview.json",
        "strategy_input":
            project_dir / "marketing_strategy" / "strategy_input.json"
    }

    fingerprints = {}

    for name, path in sources.items():
        fingerprints[name] = (
            calculate_file_hash(path)
            if path.is_file()
            else None
        )

    return fingerprints


def save_source_version(project_dir):
    """전략 생성 완료 시점의 소스 지문 기록"""
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"
    strategy_path = strategy_dir / "strategy_v2.json"

    if not strategy_path.is_file():
        raise FileNotFoundError(
            "전략 결과가 없어 버전을 기록할 수 없습니다."
        )

    fingerprints = get_source_fingerprints(project_dir)

    if any(value is None for value in fingerprints.values()):
        raise FileNotFoundError(
            "전략 버전 기록에 필요한 분석 파일이 없습니다."
        )

    record = {
        "source_fingerprints": fingerprints,
        "strategy_hash": calculate_file_hash(strategy_path),
        "recorded_at_utc": datetime.now(
            timezone.utc
        ).isoformat()
    }

    version_path = strategy_dir / "strategy_source_version.json"

    # 버전 기록을 임시 파일에 저장한 후 교체
    temp_path = strategy_dir / "strategy_source_version.tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    temp_path.replace(version_path)

    return record


def check_source_version(project_dir):
    """현재 파일들과 기록된 전략 생성 시점 파일 비교"""
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"
    version_path = strategy_dir / "strategy_source_version.json"
    strategy_path = strategy_dir / "strategy_v2.json"

    if not version_path.is_file():
        return {
            "status": "버전 기록 없음",
            "changed": None,
            "details": {}
        }

    try:
        with open(version_path, "r", encoding="utf-8") as f:
            saved = json.load(f)

        previous = saved["source_fingerprints"]
        current = get_source_fingerprints(project_dir)

        details = {
            name: (
                "변경 없음"
                if current.get(name) == previous.get(name)
                and current.get(name) is not None
                else "변경 또는 파일 누락"
            )
            for name in current
        }

        strategy_changed = (
            not strategy_path.is_file()
            or calculate_file_hash(strategy_path)
            != saved.get("strategy_hash")
        )

        changed = (
            strategy_changed
            or any(
                status != "변경 없음"
                for status in details.values()
            )
        )

        return {
            "status": (
                "데이터 변경 감지"
                if changed else "기록된 파일과 일치"
            ),
            "changed": changed,
            "details": details,
            "strategy_changed": strategy_changed
        }

    except (KeyError, ValueError, TypeError, OSError) as e:
        return {
            "status": "버전 기록 확인 오류",
            "changed": None,
            "details": {},
            "error": str(e)
        }
