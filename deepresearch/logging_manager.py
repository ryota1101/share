# logging_manager.py
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


class LogLevel(Enum):
    """ログレベル定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogType(Enum):
    """ログタイプ定義"""
    MANAGER_DECISION = "MANAGER_DECISION"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    AGENT_REQUEST = "AGENT_REQUEST"
    TASK_PLANNING = "TASK_PLANNING"
    TASK_REPLANNING = "TASK_REPLANNING"
    PROGRESS_LEDGER = "PROGRESS_LEDGER"
    FINAL_ANSWER = "FINAL_ANSWER"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    ERROR_MESSAGE = "ERROR_MESSAGE"


@dataclass
class LogEntry:
    """ログエントリのデータクラス"""
    id: str
    timestamp: datetime
    level: LogLevel
    log_type: LogType
    source: str
    message: str
    details: Optional[Dict[str, Any]] = None
    agent_name: Optional[str] = None
    round_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "log_type": self.log_type.value,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "agent_name": self.agent_name,
            "round_count": self.round_count
        }


class MagenticLoggingManager:
    """Magentic Orchestration用のログマネージャー"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.logs: List[LogEntry] = []
        self.callbacks: List[Callable[[LogEntry], None]] = []
        self.logger = logging.getLogger(f"MagenticLogging_{self.session_id}")
        
    def add_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """ログコールバックを追加"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """ログコールバックを削除"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def log(
        self,
        level: LogLevel,
        log_type: LogType,
        source: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None,
        round_count: Optional[int] = None
    ) -> LogEntry:
        """ログエントリを追加"""
        entry = LogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=level,
            log_type=log_type,
            source=source,
            message=message,
            details=details,
            agent_name=agent_name,
            round_count=round_count
        )
        
        self.logs.append(entry)
        
        # 標準ログにも出力
        self.logger.log(
            getattr(logging, level.value),
            f"[{log_type.value}] {source}: {message}"
        )
        
        # コールバック実行
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                self.logger.error(f"Error in log callback: {e}")
        
        return entry
    
    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        log_type: Optional[LogType] = None,
        agent_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """フィルタリングされたログを取得"""
        filtered_logs = self.logs
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if log_type:
            filtered_logs = [log for log in filtered_logs if log.log_type == log_type]
        
        if agent_name:
            filtered_logs = [log for log in filtered_logs if log.agent_name == agent_name]
        
        if limit:
            filtered_logs = filtered_logs[-limit:]
        
        return filtered_logs
    
    def get_logs_as_dict(self, **kwargs) -> List[Dict[str, Any]]:
        """辞書形式でログを取得"""
        return [log.to_dict() for log in self.get_logs(**kwargs)]
    
    def clear_logs(self) -> None:
        """ログをクリア"""
        self.logs.clear()
        self.log(LogLevel.INFO, LogType.SYSTEM_MESSAGE, "LoggingManager", "Logs cleared")
    
    def export_logs_json(self, filepath: str) -> None:
        """ログをJSONファイルにエクスポート"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_logs_as_dict(), f, indent=2, ensure_ascii=False)
        
        self.log(LogLevel.INFO, LogType.SYSTEM_MESSAGE, "LoggingManager", f"Logs exported to {filepath}")


# グローバルインスタンス
_global_logging_manager: Optional[MagenticLoggingManager] = None


def get_global_logging_manager() -> MagenticLoggingManager:
    """グローバルログマネージャーを取得"""
    global _global_logging_manager
    if _global_logging_manager is None:
        _global_logging_manager = MagenticLoggingManager()
    return _global_logging_manager


def set_global_logging_manager(manager: MagenticLoggingManager) -> None:
    """グローバルログマネージャーを設定"""
    global _global_logging_manager
    _global_logging_manager = manager


def reset_global_logging_manager() -> None:
    """グローバルログマネージャーをリセット"""
    global _global_logging_manager
    _global_logging_manager = None