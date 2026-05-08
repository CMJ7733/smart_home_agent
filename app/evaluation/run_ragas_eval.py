import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from utils.logger_handler import logger


def run_nightly_eval(date_str: str | None = None) -> None:
    """
    对指定日期（默认昨天）的 kb_query 路径 eval log 运行 RAGAS 评估。
    低分 case（任意指标 < 0.6）写入 data/bad_cases/YYYY-MM-DD.jsonl，并更新 DB。
    """
    date_str = date_str or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"[RAGAS] 开始评估 {date_str} 的 eval logs")

    from app.db.eval_log_repo import EvalLogRepo
    repo = EvalLogRepo()
    all_logs = repo.query_by_date(date_str)
    logs = [l for l in all_logs if l.get("intent") == "kb_query"]

    if not logs:
        logger.info(f"[RAGAS] {date_str} 无 kb_query 记录，跳过")
        return

    # 构建 RAGAS Dataset
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from ragas.llms import LangchainLLMWrapper
        from langchain_ollama import ChatOllama
    except ImportError as e:
        logger.error(f"[RAGAS] 依赖未安装: {e}，请 pip install ragas datasets")
        return

    data = {
        "question": [l["query"] for l in logs],
        "answer": [l["response"] for l in logs],
        "contexts": [
            json.loads(l["contexts_json"]) if l["contexts_json"] else []
            for l in logs
        ],
    }
    dataset = Dataset.from_dict(data)

    from app.core.config import get_settings
    settings = get_settings()
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    llm_wrapper = LangchainLLMWrapper(ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.chat_model_name,
    ))

    logger.info(f"[RAGAS] 评估 {len(logs)} 条记录...")
    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
            llm=llm_wrapper,
            raise_exceptions=False,
        )
    except Exception as e:
        logger.error(f"[RAGAS] evaluate() 失败: {e}", exc_info=True)
        return

    df = result.to_pandas()
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision"]

    bad_cases = []
    for i, row in df.iterrows():
        scores = {k: float(row[k]) if k in df.columns and row[k] is not None else None for k in metric_cols}
        valid_scores = {k: v for k, v in scores.items() if v is not None}
        if any(v < 0.6 for v in valid_scores.values()):
            bad_entry = {**logs[i], "scores": scores}
            bad_cases.append(bad_entry)
            repo.update_metrics(logs[i]["trace_id"], scores)

    bad_case_dir = Path("data/bad_cases")
    bad_case_dir.mkdir(parents=True, exist_ok=True)
    out_path = bad_case_dir / f"{date_str}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for case in bad_cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    logger.info(f"[RAGAS] 完成: {len(logs)} 条评估，{len(bad_cases)} 条 bad case → {out_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] != "--scheduler":
        # 手动指定日期：python -m app.evaluation.run_ragas_eval 2026-05-08
        run_nightly_eval(sys.argv[1])
    elif "--scheduler" in sys.argv:
        # 持续调度模式：python -m app.evaluation.run_ragas_eval --scheduler
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(run_nightly_eval, "cron", hour=2, minute=0)
        logger.info("[RAGAS] APScheduler 已启动，每天凌晨 2:00 执行评估")
        scheduler.start()
    else:
        # 默认：评估昨天
        run_nightly_eval()
