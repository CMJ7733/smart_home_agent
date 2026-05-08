import json
import sys
from datetime import datetime
from pathlib import Path


def parse_bad_cases(date_str: str) -> list[dict]:
    """从 data/bad_cases/{date_str}.jsonl 读取 bad case 列表"""
    path = Path(f"data/bad_cases/{date_str}.jsonl")
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def format_as_sft(cases: list[dict]) -> list[dict]:
    """将 bad case 转换为 SFT 微调格式"""
    sft = []
    for case in cases:
        try:
            trajectory = json.loads(case.get("trajectory_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            trajectory = []
        sft.append({
            "instruction": "你是智能家居助手，请根据用户问题给出准确、有依据的回答。",
            "input": case.get("query", ""),
            "output": case.get("response", ""),
            "trajectory": trajectory,
            "scores": case.get("scores", {}),
        })
    return sft


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    cases = parse_bad_cases(date_str)
    if not cases:
        print(f"[log_parser] {date_str}: 无 bad case 文件或内容为空")
        sys.exit(0)

    sft = format_as_sft(cases)
    out_dir = Path("data/finetune_dataset")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "train.jsonl"
    with open(out_path, "a", encoding="utf-8") as f:
        for item in sft:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[log_parser] {date_str}: {len(sft)} bad cases → {out_path}")
