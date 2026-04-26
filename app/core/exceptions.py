class SmartHomeAgentError(Exception):
    """项目基础异常"""


class IntentRouteError(SmartHomeAgentError):
    """意图路由失败"""


class DeviceControlError(SmartHomeAgentError):
    """设备控制失败"""


class RAGRetrievalError(SmartHomeAgentError):
    """RAG 检索失败"""


class MemoryAccessError(SmartHomeAgentError):
    """记忆系统访问失败"""
