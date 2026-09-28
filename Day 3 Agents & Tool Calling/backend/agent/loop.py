"""
Agent Tool-Calling Execution Loop for AgentLab AI.
Manages the iterative cycle: User Request -> LLM -> Tool Call -> Tool Result -> LLM -> Final Answer.
Enforces loop limits, cycle detection, disabled tool handling, and execution trace recording.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.agent.prompts import build_system_prompt
from backend.config import settings
from backend.models import ChatMessage, ChatResponse, TraceEvent
from backend.services.llm_service import LLMResult, LLMService, llm_service
from backend.tools.registry import ToolRegistry, default_registry

ALL_KNOWN_TOOLS = ["calculator", "search", "weather", "database", "custom"]


class AgentLoop:
    """Executes the autonomous agent reasoning and tool invocation loop."""

    def __init__(
        self,
        service: Optional[LLMService] = None,
        registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.llm = service or llm_service
        self.registry = registry or default_registry

    def run(
        self,
        user_message: str,
        enabled_tools: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tool_calls: int = 5,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> ChatResponse:
        """
        Executes the full agent loop for a user request.
        """
        trace: List[TraceEvent] = []
        step_counter = 1

        def add_trace(event_type: str, **kwargs: Any) -> None:
            nonlocal step_counter
            now_iso = datetime.now(timezone.utc).isoformat()
            trace.append(
                TraceEvent(
                    step=step_counter,
                    type=event_type,
                    timestamp=now_iso,
                    **kwargs,
                )
            )
            step_counter += 1

        # Step 1: User request received
        add_trace("start", message=f"User request received: '{user_message}'")

        active_tools = enabled_tools if enabled_tools is not None else ALL_KNOWN_TOOLS
        disabled_tools = [t for t in ALL_KNOWN_TOOLS if t not in active_tools]

        system_prompt = build_system_prompt(active_tools=active_tools, disabled_tools=disabled_tools)

        # Prepare messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Append prior conversation history if provided
        if conversation_history:
            for ch in conversation_history:
                messages.append({"role": ch.role, "content": ch.content})

        # Append current user prompt
        messages.append({"role": "user", "content": user_message})

        # Retrieve tool schemas (including disabled markers so gateway doesn't reject 400)
        tool_schemas = self.registry.get_openai_tool_definitions(
            enabled_tools=active_tools,
            include_all_with_disabled_hints=True,
        )

        add_trace(
            "thought",
            message=f"Agent analyzed request. {len(active_tools)} tools active, {len(disabled_tools)} disabled.",
        )

        total_tool_calls_executed = 0
        seen_calls: List[str] = []
        final_answer = ""
        target_model = model or settings.DEFAULT_MODEL

        try:
            while total_tool_calls_executed < max_tool_calls:
                # Call LLM
                try:
                    llm_result: LLMResult = self.llm.call_llm(
                        messages=messages,
                        tools=tool_schemas,
                        model=target_model,
                        temperature=temperature,
                    )
                except Exception as llm_err:
                    err_msg = str(llm_err)
                    # Graceful recovery if gateway complains of tool validation
                    if "tool call validation failed" in err_msg.lower() or "not provided" in err_msg.lower():
                        add_trace("thought", message="Tool is disabled in active settings. Producing fallback explanation.")
                        messages.append({
                            "role": "user",
                            "content": (
                                "Notice: The tool required for this request is currently disabled in settings. "
                                "Please inform the user that the requested tool is disabled and cannot be used, without inventing data."
                            ),
                        })
                        fallback_res = self.llm.call_llm(
                            messages=messages,
                            tools=[],
                            model=target_model,
                            temperature=temperature,
                        )
                        final_answer = fallback_res.content or "The requested tool is currently disabled in agent settings."
                        add_trace("final_answer", message="Direct explanation generated for disabled tool.")
                        break

                    add_trace("error", message=f"LLM API error: {err_msg}")
                    return ChatResponse(
                        success=False,
                        answer=f"An error occurred while communicating with the AI model: {err_msg}",
                        trace=trace,
                        tool_calls_executed=total_tool_calls_executed,
                        model_used=target_model,
                        error=err_msg,
                    )

                # Case A: Model decides to call one or more tools
                if llm_result.has_tool_calls:
                    assistant_msg: Dict[str, Any] = {
                        "role": "assistant",
                        "content": llm_result.content or "",
                        "tool_calls": [tc.to_dict() for tc in llm_result.tool_calls],
                    }
                    messages.append(assistant_msg)

                    for tc in llm_result.tool_calls:
                        if total_tool_calls_executed >= max_tool_calls:
                            add_trace(
                                "thought",
                                message=f"Reached maximum limit of {max_tool_calls} tool calls.",
                            )
                            break

                        call_signature = f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}"
                        if seen_calls.count(call_signature) >= 2:
                            add_trace(
                                "thought",
                                message=f"Detected cyclic repetitive call for tool '{tc.name}'. Skipping duplicate call.",
                            )
                            tool_result = {
                                "tool": tc.name,
                                "success": False,
                                "error": "Repetitive tool call detected. Please provide the final response.",
                            }
                        else:
                            seen_calls.append(call_signature)
                            add_trace(
                                "tool_call",
                                tool=tc.name,
                                arguments=tc.arguments,
                                message=f"Tool selected: '{tc.name}'",
                            )

                            # Execute tool with active_tools check
                            tool_result = self.registry.execute(
                                tool_name=tc.name,
                                arguments=tc.arguments,
                                enabled_tools=active_tools,
                                timeout_seconds=settings.TOOL_TIMEOUT_SECONDS,
                            )

                        total_tool_calls_executed += 1

                        add_trace(
                            "tool_result",
                            tool=tc.name,
                            result=tool_result,
                            duration_ms=tool_result.get("duration_ms", 0.0),
                            message=f"Tool '{tc.name}' executed {'successfully' if tool_result.get('success') else 'with error'}.",
                        )

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.name,
                            "content": json.dumps(tool_result),
                        })

                    # Loop continues
                    continue

                # Case B: Model did not request any tools
                else:
                    final_answer = llm_result.content
                    if total_tool_calls_executed == 0:
                        add_trace(
                            "direct_response",
                            message="No tool required for this request. Direct LLM answer generated.",
                        )
                    else:
                        add_trace(
                            "final_answer",
                            message=f"Agent synthesized final response from {total_tool_calls_executed} tool execution(s).",
                        )
                    break

            # If loop terminated due to reaching max tool calls limit
            if total_tool_calls_executed >= max_tool_calls and not final_answer:
                add_trace("thought", message="Requesting final synthesis after reaching tool limit.")
                messages.append({
                    "role": "user",
                    "content": "You have reached the maximum allowed tool calls. Please synthesize your final response now using the information collected.",
                })
                final_res = self.llm.call_llm(
                    messages=messages,
                    tools=[],
                    model=target_model,
                    temperature=temperature,
                )
                final_answer = final_res.content or "The agent reached the maximum number of tool calls for this request."
                add_trace(
                    "final_answer",
                    message="Final answer produced after maximum tool calls threshold.",
                )

            return ChatResponse(
                success=True,
                answer=final_answer,
                trace=trace,
                tool_calls_executed=total_tool_calls_executed,
                model_used=target_model,
            )

        except Exception as e:
            add_trace("error", message=f"Unexpected error in agent loop: {str(e)}")
            return ChatResponse(
                success=False,
                answer=f"An unexpected error occurred during execution: {str(e)}",
                trace=trace,
                tool_calls_executed=total_tool_calls_executed,
                model_used=target_model,
                error=str(e),
            )
