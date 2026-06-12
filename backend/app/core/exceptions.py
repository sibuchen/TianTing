"""
Custom Exceptions
自定义异常类
"""

from typing import Any


class TiantingException(Exception):
    """天听基础异常"""

    def __init__(
        self,
        message: str,
        code: int = 500,
        http_status: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(TiantingException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", code: int = 10001) -> None:
        super().__init__(message, code=code, http_status=401)


class InvalidCredentialsError(AuthenticationError):
    """用户名或密码错误"""

    def __init__(self) -> None:
        super().__init__(message="用户名或密码错误", code=10001)


class UserExistsError(TiantingException):
    """用户已存在"""

    def __init__(self, field: str = "用户名") -> None:
        code = 10002 if field == "用户名" else 10003
        message = f"{field}已存在"
        super().__init__(message, code=code, http_status=400)


class TokenExpiredError(AuthenticationError):
    """Token已过期"""

    def __init__(self) -> None:
        super().__init__(message="Token已过期", code=10004)


class InvalidTokenError(AuthenticationError):
    """Token无效"""

    def __init__(self) -> None:
        super().__init__(message="Token无效", code=10005)


class InvalidRefreshTokenError(AuthenticationError):
    """Refresh Token无效或已过期"""

    def __init__(self) -> None:
        super().__init__(message="Refresh Token无效或已过期", code=10007)


class PasswordTooShortError(TiantingException):
    """密码不符合要求"""

    def __init__(self) -> None:
        super().__init__(
            message="密码不符合要求，最少8位",
            code=10006,
            http_status=400,
        )


class PasswordMismatchError(TiantingException):
    """两次密码输入不一致"""

    def __init__(self) -> None:
        super().__init__(
            message="两次密码输入不一致",
            code=10008,
            http_status=400,
        )


class AgentError(TiantingException):
    """Agent错误基类"""

    def __init__(self, message: str, code: int = 20001, http_status: int = 404) -> None:
        super().__init__(message, code=code, http_status=http_status)


class AgentNotFoundError(AgentError):
    """Agent不存在"""

    def __init__(self) -> None:
        super().__init__(message="Agent不存在", code=20001, http_status=404)


class AgentNameExistsError(AgentError):
    """Agent名称重复"""

    def __init__(self) -> None:
        super().__init__(message="Agent名称重复", code=20002, http_status=400)


class CannotDisableOrchestratorError(AgentError):
    """无法禁用唯一调度Agent"""

    def __init__(self) -> None:
        super().__init__(message="无法禁用唯一调度Agent", code=20003, http_status=400)


class InvalidAgentTypeError(AgentError):
    """Agent类型不合法"""

    def __init__(self) -> None:
        super().__init__(message="Agent类型不合法", code=20004, http_status=400)


class SkillAlreadyAssignedError(AgentError):
    """Skill已分配给此Agent"""

    def __init__(self) -> None:
        super().__init__(message="Skill已分配给此Agent", code=20005, http_status=409)


class SkillError(TiantingException):
    """技能错误基类"""

    def __init__(self, message: str, code: int = 25001, http_status: int = 404) -> None:
        super().__init__(message, code=code, http_status=http_status)


class SkillNotFoundError(SkillError):
    """技能不存在"""

    def __init__(self) -> None:
        super().__init__(message="技能不存在", code=25001, http_status=404)


class SkillBuiltinModifyError(SkillError):
    """内置技能不可修改"""

    def __init__(self) -> None:
        super().__init__(message="内置技能不可修改或删除", code=25002, http_status=403)


class SkillInUseError(SkillError):
    """技能正在被Agent使用"""

    def __init__(self) -> None:
        super().__init__(message="技能正在被Agent使用，无法删除", code=25003, http_status=409)


class NoModelAvailableError(SkillError):
    """没有可用的模型配置"""

    def __init__(self) -> None:
        super().__init__(message="请先配置至少一个模型", code=25004, http_status=400)


class SkillImportError(SkillError):
    """技能导入失败"""

    def __init__(self, message: str = "技能导入失败") -> None:
        super().__init__(message=message, code=25005, http_status=400)


class SkillNameConflictError(SkillError):
    """技能名称冲突"""

    def __init__(self) -> None:
        super().__init__(message="技能名称已存在", code=25006, http_status=409)


class ToolError(TiantingException):
    """工具错误基类"""

    def __init__(self, message: str, code: int = 30001, http_status: int = 404) -> None:
        super().__init__(message, code=code, http_status=http_status)


class ToolNotFoundError(ToolError):
    """工具不存在"""

    def __init__(self) -> None:
        super().__init__(message="工具不存在", code=30001, http_status=404)


class MCPServerConnectionError(ToolError):
    """MCP Server连接失败"""

    def __init__(self) -> None:
        super().__init__(message="MCP Server连接失败", code=30002, http_status=503)


class MCPServerNotFoundError(ToolError):
    """MCP Server不存在"""

    def __init__(self) -> None:
        super().__init__(message="MCP Server不存在", code=30003, http_status=404)


class ToolCallError(ToolError):
    """工具调用参数错误"""

    def __init__(self) -> None:
        super().__init__(message="工具调用参数错误", code=30004, http_status=400)


class KnowledgeError(TiantingException):
    """知识库错误基类"""

    def __init__(self, message: str, code: int = 40001, http_status: int = 400) -> None:
        super().__init__(message, code=code, http_status=http_status)


class UnsupportedFileTypeError(KnowledgeError):
    """文档格式不支持"""

    def __init__(self) -> None:
        super().__init__(message="文档格式不支持", code=40001, http_status=400)


class FileTooLargeError(KnowledgeError):
    """文件大小超限"""

    def __init__(self) -> None:
        super().__init__(message="文件大小超限（最大50MB）", code=40002, http_status=413)


class DocumentNotFoundError(KnowledgeError):
    """文档不存在"""

    def __init__(self) -> None:
        super().__init__(message="文档不存在", code=40003, http_status=404)


class DocumentParseError(KnowledgeError):
    """文档解析失败"""

    def __init__(self) -> None:
        super().__init__(message="文档解析失败", code=40004, http_status=500)


class VectorizationError(KnowledgeError):
    """向量化失败"""

    def __init__(self) -> None:
        super().__init__(message="向量化失败", code=40005, http_status=500)


class QAValidationError(KnowledgeError):
    """Q&A问题和答案不能为空"""

    def __init__(self) -> None:
        super().__init__(message="Q&A问题和答案不能为空", code=40006, http_status=400)


class ConversationError(TiantingException):
    """会话错误基类"""

    def __init__(self, message: str, code: int = 50001, http_status: int = 404) -> None:
        super().__init__(message, code=code, http_status=http_status)


class ConversationNotFoundError(ConversationError):
    """会话不存在或已过期"""

    def __init__(self) -> None:
        super().__init__(message="会话不存在或已过期", code=50001, http_status=404)


class ConversationEndedError(ConversationError):
    """会话已结束无法发送消息"""

    def __init__(self) -> None:
        super().__init__(message="会话已结束无法发送消息", code=50002, http_status=400)


class RateLimitExceededError(ConversationError):
    """消息发送过于频繁"""

    def __init__(self) -> None:
        super().__init__(message="消息发送过于频繁", code=50003, http_status=429)


class HumanServiceError(TiantingException):
    """人工客服错误基类"""

    def __init__(self, message: str, code: int = 60001, http_status: int = 400) -> None:
        super().__init__(message, code=code, http_status=http_status)


class NotTransferredToHumanError(HumanServiceError):
    """对话未被转人工"""

    def __init__(self) -> None:
        super().__init__(message="对话未被转人工", code=60001, http_status=400)


class ConversationAlreadyTakenError(HumanServiceError):
    """对话已被其他客服接手"""

    def __init__(self) -> None:
        super().__init__(message="对话已被其他客服接手", code=60002, http_status=409)


class HumanServiceEndedError(HumanServiceError):
    """人工服务已结束"""

    def __init__(self) -> None:
        super().__init__(message="人工服务已结束", code=60003, http_status=400)


class UserError(TiantingException):
    """用户管理错误基类"""

    def __init__(self, message: str, code: int = 70001, http_status: int = 404) -> None:
        super().__init__(message, code=code, http_status=http_status)


class UserNotFoundError(UserError):
    """用户不存在"""

    def __init__(self) -> None:
        super().__init__(message="用户不存在", code=70001, http_status=404)


class UserFieldExistsError(UserError):
    """用户名或邮箱已被使用"""

    def __init__(self, field: str = "用户名") -> None:
        super().__init__(message=f"{field}已被使用", code=70002, http_status=409)


class ModelConfigError(TiantingException):
    """模型配置错误基类"""

    def __init__(
        self, message: str, code: int = 80001, http_status: int = 503
    ) -> None:
        super().__init__(message, code=code, http_status=http_status)


class ModelAPIConnectionError(ModelConfigError):
    """模型API连接失败"""

    def __init__(self, detail: str = "") -> None:
        msg = f"模型API连接失败: {detail}" if detail else "模型API连接失败"
        super().__init__(message=msg, code=80001, http_status=503)


class InvalidAPIKeyError(ModelConfigError):
    """模型API Key无效"""

    def __init__(self) -> None:
        super().__init__(message="模型API Key无效", code=80002, http_status=401)


class ModelTimeoutError(ModelConfigError):
    """模型调用超时"""

    def __init__(self) -> None:
        super().__init__(message="模型调用超时", code=80003, http_status=500)


class ModelResponseFormatError(ModelConfigError):
    """模型返回格式异常"""

    def __init__(self) -> None:
        super().__init__(message="模型返回格式异常", code=80004, http_status=500)


class ModelConfigInUseError(ModelConfigError):
    """无法删除已被Agent绑定的模型配置"""

    def __init__(self) -> None:
        super().__init__(
            message="无法删除已被Agent绑定的模型配置",
            code=80005,
            http_status=400,
        )


class PermissionDeniedError(TiantingException):
    """权限不足"""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(message, code=403, http_status=403)


class ValidationError(TiantingException):
    """数据校验失败"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=422, http_status=422, details=details)


class RateLimitError(TiantingException):
    """请求过于频繁"""

    def __init__(self, message: str = "请求过于频繁") -> None:
        super().__init__(message, code=429, http_status=429)
