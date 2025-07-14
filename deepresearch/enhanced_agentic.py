# enhanced_magentic.py
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from collections.abc import Awaitable

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.orchestration.magentic import (
    MagenticManagerBase,
    MagenticManagerActor,
    MagenticAgentActor,
    MagenticOrchestration,
    MagenticContext,
    MagenticStartMessage,
    MagenticRequestMessage,
    MagenticResponseMessage,
    MagenticResetMessage,
    ProgressLedger,
    StandardMagenticManager,
    DefaultTypeAlias,
    TIn,
    TOut,
)
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import message_handler
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.feature_stage_decorator import experimental

from .logging_manager import (
    MagenticLoggingManager,
    LogLevel,
    LogType,
    get_global_logging_manager
)

logger = logging.getLogger(__name__)


@experimental
class EnhancedMagenticManager(StandardMagenticManager):
    """ログ機能を追加したMagenticManager"""
    
    def __init__(
        self,
        *args,
        logging_manager: Optional[MagenticLoggingManager] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.logging_manager = logging_manager or get_global_logging_manager()
    
    async def plan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """プランニング処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.TASK_PLANNING,
            "EnhancedMagenticManager",
            "Starting task planning",
            details={
                "task": magentic_context.task.content,
                "participants": list(magentic_context.participant_descriptions.keys()),
                "round_count": magentic_context.round_count
            },
            round_count=magentic_context.round_count
        )
        
        try:
            result = await super().plan(magentic_context)
            
            self.logging_manager.log(
                LogLevel.INFO,
                LogType.TASK_PLANNING,
                "EnhancedMagenticManager",
                "Task planning completed successfully",
                details={
                    "task_ledger_facts": self.task_ledger.facts.content if self.task_ledger else None,
                    "task_ledger_plan": self.task_ledger.plan.content if self.task_ledger else None,
                },
                round_count=magentic_context.round_count
            )
            
            return result
            
        except Exception as e:
            self.logging_manager.log(
                LogLevel.ERROR,
                LogType.ERROR_MESSAGE,
                "EnhancedMagenticManager",
                f"Error during task planning: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                round_count=magentic_context.round_count
            )
            raise
    
    async def replan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """再プランニング処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.TASK_REPLANNING,
            "EnhancedMagenticManager",
            f"Starting task replanning (stall_count: {magentic_context.stall_count})",
            details={
                "stall_count": magentic_context.stall_count,
                "reset_count": magentic_context.reset_count,
                "round_count": magentic_context.round_count
            },
            round_count=magentic_context.round_count
        )
        
        try:
            result = await super().replan(magentic_context)
            
            self.logging_manager.log(
                LogLevel.INFO,
                LogType.TASK_REPLANNING,
                "EnhancedMagenticManager",
                "Task replanning completed successfully",
                details={
                    "updated_facts": self.task_ledger.facts.content if self.task_ledger else None,
                    "updated_plan": self.task_ledger.plan.content if self.task_ledger else None,
                },
                round_count=magentic_context.round_count
            )
            
            return result
            
        except Exception as e:
            self.logging_manager.log(
                LogLevel.ERROR,
                LogType.ERROR_MESSAGE,
                "EnhancedMagenticManager",
                f"Error during task replanning: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                round_count=magentic_context.round_count
            )
            raise
    
    async def create_progress_ledger(self, magentic_context: MagenticContext) -> ProgressLedger:
        """プログレスレジャー作成（ログ付き）"""
        self.logging_manager.log(
            LogLevel.DEBUG,
            LogType.PROGRESS_LEDGER,
            "EnhancedMagenticManager",
            "Creating progress ledger",
            details={"round_count": magentic_context.round_count},
            round_count=magentic_context.round_count
        )
        
        try:
            result = await super().create_progress_ledger(magentic_context)
            
            self.logging_manager.log(
                LogLevel.INFO,
                LogType.PROGRESS_LEDGER,
                "EnhancedMagenticManager",
                "Progress ledger created",
                details={
                    "is_request_satisfied": result.is_request_satisfied.answer,
                    "is_in_loop": result.is_in_loop.answer,
                    "is_progress_being_made": result.is_progress_being_made.answer,
                    "next_speaker": result.next_speaker.answer,
                    "instruction_or_question": result.instruction_or_question.answer,
                    "ledger_reasons": {
                        "request_satisfied": result.is_request_satisfied.reason,
                        "in_loop": result.is_in_loop.reason,
                        "progress_being_made": result.is_progress_being_made.reason,
                        "next_speaker": result.next_speaker.reason,
                        "instruction": result.instruction_or_question.reason
                    }
                },
                round_count=magentic_context.round_count
            )
            
            return result
            
        except Exception as e:
            self.logging_manager.log(
                LogLevel.ERROR,
                LogType.ERROR_MESSAGE,
                "EnhancedMagenticManager",
                f"Error creating progress ledger: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                round_count=magentic_context.round_count
            )
            raise
    
    async def prepare_final_answer(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """最終回答準備（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.FINAL_ANSWER,
            "EnhancedMagenticManager",
            "Preparing final answer",
            details={"round_count": magentic_context.round_count},
            round_count=magentic_context.round_count
        )
        
        try:
            result = await super().prepare_final_answer(magentic_context)
            
            self.logging_manager.log(
                LogLevel.INFO,
                LogType.FINAL_ANSWER,
                "EnhancedMagenticManager",
                "Final answer prepared",
                details={
                    "final_answer": result.content,
                    "round_count": magentic_context.round_count
                },
                round_count=magentic_context.round_count
            )
            
            return result
            
        except Exception as e:
            self.logging_manager.log(
                LogLevel.ERROR,
                LogType.ERROR_MESSAGE,
                "EnhancedMagenticManager",
                f"Error preparing final answer: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                round_count=magentic_context.round_count
            )
            raise


@experimental
class EnhancedMagenticManagerActor(MagenticManagerActor):
    """ログ機能を追加したMagenticManagerActor"""
    
    def __init__(
        self,
        manager: MagenticManagerBase,
        internal_topic_type: str,
        participant_descriptions: Dict[str, str],
        result_callback: Optional[Callable[[DefaultTypeAlias], Awaitable[None]]] = None,
        logging_manager: Optional[MagenticLoggingManager] = None,
    ):
        super().__init__(manager, internal_topic_type, participant_descriptions, result_callback)
        self.logging_manager = logging_manager or get_global_logging_manager()
    
    @message_handler
    async def _handle_start_message(self, message: MagenticStartMessage, ctx: MessageContext) -> None:
        """開始メッセージ処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.SYSTEM_MESSAGE,
            "EnhancedMagenticManagerActor",
            "Received start message",
            details={
                "task": message.body.content,
                "participants": list(self._participant_descriptions.keys())
            }
        )
        
        await super()._handle_start_message(message, ctx)
    
    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        """応答メッセージ処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.AGENT_RESPONSE,
            "EnhancedMagenticManagerActor",
            "Received agent response",
            details={
                "content": message.body.content,
                "from_agent": message.body.name,
                "role": message.body.role.name if message.body.role else None
            },
            agent_name=message.body.name,
            round_count=self._context.round_count if self._context else None
        )
        
        await super()._handle_response_message(message, ctx)
    
    async def _run_inner_loop(self, cancellation_token: CancellationToken) -> None:
        """内部ループ実行（ログ付き）"""
        if self._context is None:
            raise RuntimeError("The Magentic manager is not started yet.")
        
        self.logging_manager.log(
            LogLevel.DEBUG,
            LogType.MANAGER_DECISION,
            "EnhancedMagenticManagerActor",
            f"Starting inner loop (round {self._context.round_count + 1})",
            details={
                "round_count": self._context.round_count,
                "stall_count": self._context.stall_count,
                "reset_count": self._context.reset_count
            },
            round_count=self._context.round_count
        )
        
        await super()._run_inner_loop(cancellation_token)
    
    async def _reset_for_outer_loop(self, cancellation_token: CancellationToken) -> None:
        """外部ループリセット（ログ付き）"""
        self.logging_manager.log(
            LogLevel.WARNING,
            LogType.SYSTEM_MESSAGE,
            "EnhancedMagenticManagerActor",
            "Resetting for outer loop due to stalling",
            details={
                "stall_count": self._context.stall_count if self._context else None,
                "reset_count": self._context.reset_count if self._context else None
            },
            round_count=self._context.round_count if self._context else None
        )
        
        await super()._reset_for_outer_loop(cancellation_token)
    
    async def _prepare_final_answer(self) -> None:
        """最終回答準備（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.FINAL_ANSWER,
            "EnhancedMagenticManagerActor",
            "Task completed, preparing final answer",
            details={
                "round_count": self._context.round_count if self._context else None
            },
            round_count=self._context.round_count if self._context else None
        )
        
        await super()._prepare_final_answer()


@experimental
class EnhancedMagenticAgentActor(MagenticAgentActor):
    """ログ機能を追加したMagenticAgentActor"""
    
    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        agent_response_callback: Optional[Callable[[DefaultTypeAlias], Awaitable[None] | None]] = None,
        streaming_agent_response_callback: Optional[
            Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        ] = None,
        logging_manager: Optional[MagenticLoggingManager] = None,
    ):
        super().__init__(agent, internal_topic_type, agent_response_callback, streaming_agent_response_callback)
        self.logging_manager = logging_manager or get_global_logging_manager()
    
    @message_handler
    async def _handle_request_message(self, message: MagenticRequestMessage, ctx: MessageContext) -> None:
        """リクエストメッセージ処理（ログ付き）"""
        if message.agent_name != self._agent.name:
            return
        
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.AGENT_REQUEST,
            "EnhancedMagenticAgentActor",
            f"Agent {self._agent.name} received request",
            details={
                "agent_name": self._agent.name,
                "agent_description": self._agent.description
            },
            agent_name=self._agent.name
        )
        
        await super()._handle_request_message(message, ctx)
    
    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        """応答メッセージ処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.DEBUG,
            LogType.AGENT_RESPONSE,
            "EnhancedMagenticAgentActor",
            f"Agent {self._agent.name} received response message",
            details={
                "message_content": message.body.content,
                "from_agent": message.body.name,
                "to_agent": self._agent.name
            },
            agent_name=self._agent.name
        )
        
        await super()._handle_response_message(message, ctx)
    
    @message_handler
    async def _handle_reset_message(self, message: MagenticResetMessage, ctx: MessageContext) -> None:
        """リセットメッセージ処理（ログ付き）"""
        self.logging_manager.log(
            LogLevel.WARNING,
            LogType.SYSTEM_MESSAGE,
            "EnhancedMagenticAgentActor",
            f"Agent {self._agent.name} received reset message",
            details={"agent_name": self._agent.name},
            agent_name=self._agent.name
        )
        
        await super()._handle_reset_message(message, ctx)


@experimental
class EnhancedMagenticOrchestration(MagenticOrchestration[TIn, TOut]):
    """ログ機能を追加したMagenticOrchestration"""
    
    def __init__(
        self,
        members: List[Agent],
        manager: MagenticManagerBase,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_transform: Optional[Callable[[TIn], Awaitable[DefaultTypeAlias] | DefaultTypeAlias]] = None,
        output_transform: Optional[Callable[[DefaultTypeAlias], Awaitable[TOut] | TOut]] = None,
        agent_response_callback: Optional[Callable[[DefaultTypeAlias], Awaitable[None] | None]] = None,
        streaming_agent_response_callback: Optional[
            Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        ] = None,
        logging_manager: Optional[MagenticLoggingManager] = None,
    ):
        super().__init__(
            members=members,
            manager=manager,
            name=name,
            description=description,
            input_transform=input_transform,
            output_transform=output_transform,
            agent_response_callback=agent_response_callback,
            streaming_agent_response_callback=streaming_agent_response_callback,
        )
        self.logging_manager = logging_manager or get_global_logging_manager()
    
    async def _register_members(self, runtime: CoreRuntime, internal_topic_type: str) -> None:
        """メンバー登録（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.SYSTEM_MESSAGE,
            "EnhancedMagenticOrchestration",
            f"Registering {len(self._members)} agents",
            details={
                "agent_names": [agent.name for agent in self._members],
                "agent_descriptions": {agent.name: agent.description for agent in self._members}
            }
        )
        
        await asyncio.gather(*[
            EnhancedMagenticAgentActor.register(
                runtime,
                self._get_agent_actor_type(agent, internal_topic_type),
                lambda agent=agent: EnhancedMagenticAgentActor(
                    agent,
                    internal_topic_type,
                    self._agent_response_callback,
                    self._streaming_agent_response_callback,
                    self.logging_manager,
                ),
            )
            for agent in self._members
        ])
    
    async def _register_manager(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Optional[Callable[[DefaultTypeAlias], Awaitable[None]]] = None,
    ) -> None:
        """マネージャー登録（ログ付き）"""
        self.logging_manager.log(
            LogLevel.INFO,
            LogType.SYSTEM_MESSAGE,
            "EnhancedMagenticOrchestration",
            "Registering manager",
            details={"manager_type": type(self._manager).__name__}
        )
        
        await EnhancedMagenticManagerActor.register(
            runtime,
            self._get_manager_actor_type(internal_topic_type),
            lambda: EnhancedMagenticManagerActor(
                self._manager,
                internal_topic_type=internal_topic_type,
                participant_descriptions={agent.name: agent.description for agent in self._members},
                result_callback=result_callback,
                logging_manager=self.logging_manager,
            ),
        )