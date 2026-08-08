"""Reasoning agent: LangChain tool-calling agent wired to a local Ollama model
(section 3.5). This is the ONLY place read-only tools execute inline; any
non-read-only tool call the LLM makes is turned into a PendingAction instead
of a real side effect — see the module docstring in app/agent/tools.py for
why that's safe to do at the tool-wrapper level.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agent.actions import propose_action
from app.agent.tools import ToolSpec, list_tools
from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are Oreo, a helpful personal AI assistant. \
Be concise and speak naturally, as if replying out loud.

The user's current detected emotional state is: {emotion_state}. \
Adjust your tone accordingly (e.g. be extra clear and brief if urgent, \
calm and reassuring if frustrated) without mentioning the detection itself.

Relevant memory from past interactions and documents:
{context_block}

You have tools available. Read-only tools (search, listing things) run \
immediately. Any tool that changes something (creating events, writing \
files, etc.) will NOT execute right away — calling it only queues a \
proposal that the user must approve on their device. Tell the user you've \
queued it and what it will do; don't claim it already happened.
"""


@dataclass
class AgentTurn:
    response_text: str
    proposed_action_id: str | None = None
    tool_calls: list[str] | None = None


def _build_langchain_tool(spec: ToolSpec, db: Session, user_id: str, device_id: str | None):
    """Wrap a ToolSpec as a LangChain StructuredTool.

    Read-only tools call the real executor directly. Non-read-only tools
    call propose_action() instead — the LLM-visible function for a write
    tool literally cannot perform the write; it can only queue one.
    """
    from langchain_core.tools import StructuredTool
    from pydantic import create_model

    fields = {name: (str, ...) for name in spec.args_schema} or {"_unused": (str, "")}
    ArgsModel = create_model(f"{spec.name}_Args", **fields)  # noqa: N806

    if spec.read_only:
        def _run(**kwargs) -> str:
            kwargs.pop("_unused", None)
            return spec.executor(**kwargs)
    else:
        def _run(**kwargs) -> str:
            kwargs.pop("_unused", None)
            summary = f"{spec.name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})"
            action = propose_action(db, user_id, device_id, spec.name, kwargs, summary)
            return f"Queued for your confirmation (action_id={action.id}): {summary}"

    return StructuredTool.from_function(
        func=_run,
        name=spec.name,
        description=spec.description,
        args_schema=ArgsModel,
    )


class ReasoningAgent:
    def __init__(self, model: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from langchain_ollama import ChatOllama

            self._llm = ChatOllama(model=self.model, base_url=self.base_url, temperature=0.4)
        return self._llm

    def _build_executor(self, db: Session, user_id: str, device_id: str | None, tools_override=None):
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        specs = tools_override if tools_override is not None else list_tools()
        lc_tools = [_build_langchain_tool(spec, db, user_id, device_id) for spec in specs]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(self._get_llm(), lc_tools, prompt)
        return AgentExecutor(agent=agent, tools=lc_tools, max_iterations=6, verbose=False)

    def respond(
        self,
        db: Session,
        user_id: str,
        device_id: str | None,
        user_text: str,
        emotion_state: str,
        context_snippets: list[str],
    ) -> AgentTurn:
        context_block = "\n".join(f"- {c}" for c in context_snippets) if context_snippets else "(none)"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(emotion_state=emotion_state, context_block=context_block)

        try:
            executor = self._build_executor(db, user_id, device_id)
            result = executor.invoke({"input": user_text, "system_prompt": system_prompt})
            output_text = result.get("output", "").strip() or "Okay."
        except Exception as exc:  # noqa: BLE001 — Ollama may not be running in dev/CI; degrade gracefully
            logger.warning("reasoning_agent_unavailable", error=str(exc))
            output_text = (
                "I couldn't reach my reasoning model just now, so I can't process that request. "
                "(Is Ollama running? See backend/README.md.)"
            )

        proposed_action_id = None
        if "action_id=" in output_text:
            try:
                proposed_action_id = output_text.split("action_id=", 1)[1].split(")")[0].strip()
            except IndexError:
                proposed_action_id = None

        return AgentTurn(response_text=output_text, proposed_action_id=proposed_action_id)


_default_agent: ReasoningAgent | None = None


def get_reasoning_agent() -> ReasoningAgent:
    global _default_agent
    if _default_agent is None:
        _default_agent = ReasoningAgent()
    return _default_agent
