# TODO (Phase 4, 占位): LoRA 微调数据集构建
# 将 Bad Case 整理为 Agentic Trajectory 微调格式
# 目标基座: Qwen2.5-7B（需 GPU: A100/4090 以上）
# 实际训练在 data/finetune/train.py 中执行（future work）

def build_finetune_dataset(bad_case_dir: str, output_path: str) -> None:
    raise NotImplementedError("Phase 4 (占位): 待实现微调数据集构建")
