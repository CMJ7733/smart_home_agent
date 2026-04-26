# TODO (Phase 3): Bad Case 提取与 SFT 数据集格式化
# 输入: data/bad_cases/YYYY-MM-DD.jsonl（由 run_ragas_eval.py 生成）
# 输出: data/finetune_dataset/train.jsonl（SFT 格式，含 agentic trajectory）
# SFT 格式: {"instruction": ..., "input": ..., "output": ..., "trajectory": [...]}

def parse_bad_cases(date_str: str) -> list[dict]:
    raise NotImplementedError("Phase 3: 待实现 Bad Case 解析")


def format_as_sft(cases: list[dict]) -> list[dict]:
    raise NotImplementedError("Phase 3: 待实现 SFT 格式转换")
