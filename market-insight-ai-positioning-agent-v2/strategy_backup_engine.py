
from pathlib import Path
from datetime import datetime, timezone
import shutil


STRATEGY_FILES = [
    "strategy_input.json",
    "strategy_v2.json",
    "strategy_evidence_audit.json",
    "strategy_structured.json",
    "strategy_source_version.json",
    "market_strategy_report_v2.md",
    "market_strategy_report_v2.pdf"
]


def backup_strategy(project_dir):
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"

    existing = [
        filename
        for filename in STRATEGY_FILES
        if (strategy_dir / filename).is_file()
    ]

    if not existing:
        return None

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S_%f")

    backup_dir = strategy_dir / "history" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    try:
        for filename in existing:
            shutil.copy2(
                strategy_dir / filename,
                backup_dir / filename
            )
    except Exception:
        shutil.rmtree(backup_dir)
        raise

    return backup_dir


# ===== STEP 27-10D: RESTORE STRATEGY =====

# ===== STEP 27-10D-5: EXACT RESTORE =====

def restore_strategy(project_dir, backup_dir):
    """백업 당시의 전략 결과 파일 상태로 복원."""
    project_dir = Path(project_dir).resolve()
    strategy_dir = (project_dir / "marketing_strategy").resolve()
    history_dir = (strategy_dir / "history").resolve()
    backup_dir = Path(backup_dir).resolve()

    if backup_dir.parent != history_dir:
        raise ValueError(
            "현재 프로젝트의 전략 백업만 복원할 수 있습니다."
        )

    if not backup_dir.is_dir():
        raise FileNotFoundError(backup_dir)

    # 복원 전 백업 파일 모두 읽을 수 있는지 확인
    existing_in_backup = [
        name for name in STRATEGY_FILES
        if (backup_dir / name).is_file()
    ]

    restored = []

    for filename in STRATEGY_FILES:
        source = backup_dir / filename
        destination = strategy_dir / filename

        if filename in existing_in_backup:
            shutil.copy2(source, destination)
            restored.append(filename)

        elif destination.is_file():
            # 백업에 없었던 신규 전략 결과 파일만 정리
            destination.unlink()

    return restored

