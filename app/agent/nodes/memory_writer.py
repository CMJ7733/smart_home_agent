from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import AgentState
from app.memory.short_term import ShortTermMemory
from app.core.config import get_settings
from utils.logger_handler import logger

_memory: ShortTermMemory | None = None


def _get_memory() -> ShortTermMemory:
    global _memory
    if _memory is None:
        s = get_settings()
        _memory = ShortTermMemory(redis_url=s.redis_url, ttl=s.redis_ttl)
    return _memory


def memory_writer_node(state: AgentState) -> AgentState:
    session_id = state.get("session_id", "")
    user_input = state.get("user_input", "")
    final_response = state.get("final_response", "")

    if not session_id or not final_response:
        return {}

    try:
        mem = _get_memory()
        history = mem.load(session_id)
        history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=final_response),
        ])
        mem.save(session_id, history)
    except Exception as e:
        logger.warning(f"memory_writer: Redis write failed [{session_id}]: {e}")

    return {}
