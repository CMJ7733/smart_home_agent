# TODO (Phase 2): 长期记忆 / 用户偏好图谱
# 会话结束后由 FastAPI BackgroundTask 异步触发
# 流程:
#   1. 输入本轮 chat_history
#   2. LLM 抽取结构化偏好: {room_temp_preference, light_color_preference, ...}
#   3. 写入 Milvus 独立 collection（user_preferences），标量索引 user_id
#   4. entity_extractor_node 遇到模糊指代时调用 query_preferences(user_id) 补全


class MemoryGraph:
    def extract_and_save(self, user_id: str, chat_history: list) -> None:
        raise NotImplementedError("Phase 2: 待实现长期偏好抽取")

    def query_preferences(self, user_id: str) -> dict:
        raise NotImplementedError("Phase 2: 待实现偏好查询")
