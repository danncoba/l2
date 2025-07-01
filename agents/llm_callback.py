from typing import Any, Optional, Sequence, Union
from uuid import UUID

from langchain_core.agents import AgentFinish, AgentAction
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult, GenerationChunk, ChatGenerationChunk
from opentelemetry import trace
from tenacity import RetryCallState


tracer = trace.get_tracer(__name__)


class CustomLlmTrackerCallback(BaseCallbackHandler):

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_llm_new_token") as span:
            span.set_attribute(f"{self._name}_llm.on_llm_new_token.token", token)
            span.set_attribute(f"{self._name}_llm.on_llm_new_token.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_llm_new_token.chunk",
                str(chunk) if chunk is not None else None,
            )
            span.set_attribute(
                f"{self._name}_llm.on_llm_new_token.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_llm_new_token.kwargs", kwargs)

        return super().on_llm_new_token(
            token, chunk=chunk, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_llm_end") as span:
            span.set_attribute(f"{self._name}_llm.on_llm_error.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_llm_error.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_llm_error.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_llm_error.response", response)
        return super().on_llm_end(
            response, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_llm_error") as span:
            span.set_attribute(f"{self._name}_llm.on_llm_error.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_llm_error.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_llm_error.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_llm_error.error", error)
        return super().on_llm_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_chain_end") as span:
            span.set_attribute(f"{self._name}_llm.on_chain_end.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_chain_end.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_chain_end.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_chain_end.outputs", outputs)
        return super().on_chain_end(
            outputs, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_chain_error") as span:
            span.set_attribute(f"{self._name}_llm.on_chain_error.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_chain_error.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_chain_error.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_chain_error.outputs", error)
        return super().on_chain_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_agent_action") as span:
            span.set_attribute(f"{self._name}_llm.on_agent_action.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_agent_action.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_agent_action.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_agent_action.outputs", action)
        return super().on_agent_action(
            action, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_agent_finish") as span:
            span.set_attribute(f"{self._name}_llm.on_agent_finish.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_agent_finish.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_agent_finish.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_agent_finish.outputs", finish)
        return super().on_agent_finish(
            finish, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_tool_end") as span:
            span.set_attribute(f"{self._name}_llm.on_tool_end.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_tool_end.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_tool_end.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_tool_end.outputs", output)
        return super().on_tool_end(
            output, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span(f"{self._name}_on_tool_error") as span:
            span.set_attribute(f"{self._name}_llm.on_tool_error.run_id", run_id)
            span.set_attribute(
                f"{self._name}_llm.on_tool_error.parent_run_id", parent_run_id
            )
            span.set_attribute(f"{self._name}_llm.on_tool_error.kwargs", kwargs)
            span.set_attribute(f"{self._name}_llm.on_tool_error.outputs", error)
        return super().on_tool_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span("on_retriever_error") as span:
            span.set_attribute("llm.on_retriever_error.run_id", run_id)
            span.set_attribute("llm.on_retriever_error.parent_run_id", parent_run_id)
            span.set_attribute("llm.on_retriever_error.kwargs", kwargs)
            span.set_attribute("llm.on_retriever_error.outputs", error)
        return super().on_retriever_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_retriever_end(
        self,
        documents: Sequence[Document],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span("on_retriever_end") as span:
            span.set_attribute("llm.on_retriever_end.run_id", run_id)
            span.set_attribute("llm.on_retriever_end.parent_run_id", parent_run_id)
            span.set_attribute("llm.on_retriever_end.kwargs", kwargs)
            span.set_attribute("llm.on_retriever_end.outputs", documents)
        return super().on_retriever_end(
            documents, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span("on_llm_start") as span:
            span.set_attribute("llm.on_llm_start.run_id", run_id)
            span.set_attribute("llm.on_llm_start.parent_run_id", parent_run_id)
            span.set_attribute("llm.on_llm_start.kwargs", kwargs)
            span.set_attribute("llm.on_llm_start.outputs", serialized)
            span.set_attribute("llm.on_llm_start.prompts", prompts)
            span.set_attribute("llm.on_llm_start.tags", tags)
            span.set_attribute("llm.on_llm_start.metadata", metadata)
        return super().on_llm_start(
            serialized,
            prompts,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            **kwargs,
        )

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        with tracer.start_as_current_span("on_chat_model_start") as span:
            span.set_attribute("llm.on_chat_model_start.run_id", run_id)
            span.set_attribute("llm.on_chat_model_start.parent_run_id", parent_run_id)
            span.set_attribute("llm.on_chat_model_start.kwargs", kwargs)
            span.set_attribute("llm.on_chat_model_start.outputs", serialized)
            span.set_attribute("llm.on_chat_model_start.serialized", serialized)
            span.set_attribute("llm.on_chat_model_start.messages", messages)
            span.set_attribute("llm.on_chat_model_start.metadata", metadata)
        return super().on_chat_model_start(
            serialized,
            messages,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            **kwargs,
        )

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_retriever_start(
            serialized,
            query,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            **kwargs,
        )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_chain_start(
            serialized,
            inputs,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            **kwargs,
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_tool_start(
            serialized,
            input_str,
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            metadata=metadata,
            inputs=inputs,
            **kwargs,
        )

    def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_text(
            text, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_retry(
        self,
        retry_state: RetryCallState,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_retry(
            retry_state, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_custom_event(
        self,
        name: str,
        data: Any,
        *,
        run_id: UUID,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        return super().on_custom_event(
            name, data, run_id=run_id, tags=tags, metadata=metadata, **kwargs
        )

    @property
    def __class__(self):
        return super().__class__

    def __init__(self, name):
        super().__init__()
        self._name = name

    def __new__(cls, name):
        return super().__new__(cls)

    def __setattr__(self, __name, __value):
        super().__setattr__(__name, __value)

    def __delattr__(self, __name):
        super().__delattr__(__name)

    def __eq__(self, __value):
        return super().__eq__(__value)

    def __ne__(self, __value):
        return super().__ne__(__value)

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

    def __hash__(self):
        return super().__hash__()

    def __format__(self, __format_spec):
        return super().__format__(__format_spec)

    def __getattribute__(self, __name):
        return super().__getattribute__(__name)

    def __sizeof__(self):
        return super().__sizeof__()

    def __reduce__(self):
        return super().__reduce__()

    def __reduce_ex__(self, __protocol):
        return super().__reduce_ex__(__protocol)

    def __getstate__(self):
        return super().__getstate__()

    def __dir__(self):
        return super().__dir__()

    def __init_subclass__(cls):
        super().__init_subclass__()

    @classmethod
    def __subclasshook__(cls, __subclass):
        return super().__subclasshook__(__subclass)
