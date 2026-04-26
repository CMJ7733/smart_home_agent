# TODO (Phase 3): RAGAS 自动评估脚本（定时任务）
# 执行时机: 每晚定时运行（APScheduler 或外部 cron）
# 流程:
#   1. 从 LangSmith 拉取当天 trace 数据
#   2. 用 RAGAS 计算: faithfulness / answer_relevancy / context_precision / context_recall
#   3. 自定义指标: intent_accuracy / tool_call_correctness
#   4. 低分 case（< 0.6）写入 data/bad_cases/YYYY-MM-DD.jsonl
#   5. 更新 eval_metrics 到评估日志 DB

def run_nightly_eval():
    raise NotImplementedError("Phase 3: 待实现 RAGAS 夜间评估任务")


if __name__ == "__main__":
    run_nightly_eval()
