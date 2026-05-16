"""ReAct Agent实现 - 推理与行动结合的智能体"""

import re
import json
import traceback
from typing import Optional, List, Tuple
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.config import Config
from ..core.message import Message
from ..tracing import (
    ErrorPayload,
    FinishPayload,
    LLMResponsePayload,
    ParsedActionPayload,
    RunStartPayload,
    ToolCallPayload,
    ToolResultPayload,
    TraceEvent,
    TraceEventPayload,
    TraceLogger,
    UserInputPayload,
    summarize_messages,
)
from ..tools.registry import ToolRegistry

# 默认ReAct提示词模板
DEFAULT_REACT_PROMPT = """
你是一个具备推理和行动能力的AI助手. 你可以通过思考分析问题, 然后调用合适的工具来获取信息, 最终给出准确的答案. 
我接下来将使用markdown语法来对你的输出内容进行约束, 请只关注接下来的markdown文本中的内容, 忽略其标记符号:

## 输出约束
### 输出结构
请严格按照以下结构进行回应, 每次只能执行一个步骤:
```
Thought: <分析当前问题，思考需要什么信息或采取什么行动>
Action: <需要执行的行动>
```
### 补充说明
- "```"块中的内容才是需要输出的结构, 输出中不要包含"```"块
- "Action: <action>"中的action只能是以下两种结构之一:
    - `<tool name>[<tool parameters>]`
    - `Finish[<最终回应>]`
- "``"中的内容才是真实需要输出的内容, 输出结果中不应包含"``"块
- "<>"是占位符, 其中填放真实的内容, 输出结果中不应包含"<>"

## 你可用的工具
{tools}

## 重要提醒
1. 每次回应必须包含Thought和Action两部分
2. 工具调用的格式必须严格遵循：工具名[参数], 方括号中的"参数"必须是合法JSON对象
3. 只有当你确信有足够信息回答问题时, 才使用Finish
4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数

## 工具调用示例
function[{{"foo": "bar", "foo1": "bar1"}}]

## 结束示例
Finish[我完成了任务.]

## 对话历史
{conversation_history}

## 本次需要完成的任务
Question: {question}

## 本次执行历史
{history}

现在开始你的推理和行动："""

class ReActAgent(Agent):
    """
    ReAct (Reasoning and Acting) Agent
    
    结合推理和行动的智能体，能够：
    1. 分析问题并制定行动计划
    2. 调用外部工具获取信息
    3. 基于观察结果进行推理
    4. 迭代执行直到得出最终答案
    
    这是一个经典的Agent范式, 特别适合需要外部信息的任务。
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None,
        trace_logger: Optional[TraceLogger] = None,
        trace_enabled: Optional[bool] = None,
    ):
        """
        初始化ReActAgent

        Args:
            name: Agent名称
            llm: LLM实例
            tool_registry: 工具注册表
            system_prompt: 系统提示词
            config: 配置对象
            max_steps: 最大执行步数
            custom_prompt: 自定义提示词模板
            trace_logger: TraceLogger实例
            trace_enabled: 是否启用Trace
        """
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.trace_logger = trace_logger or self._create_trace_logger(trace_enabled)

        # 设置提示词模板：用户自定义优先，否则使用默认模板
        self.prompt_template = custom_prompt if custom_prompt else DEFAULT_REACT_PROMPT
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        运行ReAct Agent
        
        Args:
            input_text: 用户问题
            **kwargs: 其他参数
            
        Returns:
            最终答案
        """
        self.current_history = []
        current_step = 0
        run_id = self._start_trace_run()
        run_status = "completed"

        self._trace(
            run_id,
            current_step,
            TraceEvent.RUN_START,
            RunStartPayload(agent=self.name, input_chars=len(input_text)),
        )
        self._trace(
            run_id,
            current_step,
            TraceEvent.USER_INPUT,
            UserInputPayload(input=input_text),
        )
        
        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        try:
            while current_step < self.max_steps:
                current_step += 1
                print(f"\n--- 第 {current_step}/{self.max_steps} 步 ---")

                # 构建提示词
                tools_description = self.tool_registry.get_tools_description()
                conversation_history = self._format_conversation_history()
                history_str = "\n".join(self.current_history)
                prompt = self.prompt_template.format(
                    tools=tools_description,
                    question=input_text,
                    conversation_history=conversation_history,
                    history=history_str
                )

                # 调用LLM
                messages = [{"role": "user", "content": prompt}]
                self._trace(
                    run_id,
                    current_step,
                    TraceEvent.LLM_REQUEST,
                    summarize_messages(messages),
                )
                try:
                    response_text = self.llm.invoke(messages, **kwargs)
                except Exception as exc:
                    run_status = "error"
                    self._trace_error(run_id, current_step, "llm_call", exc)
                    raise

                self._trace(
                    run_id,
                    current_step,
                    TraceEvent.LLM_RESPONSE,
                    LLMResponsePayload(content=response_text, usage=None),
                )

                if not response_text:
                    print("❌ 错误：LLM未能返回有效响应。")
                    self._trace(
                        run_id,
                        current_step,
                        TraceEvent.ERROR,
                        ErrorPayload(
                            stage="llm_call",
                            message="LLM未能返回有效响应。",
                            error_type="EmptyLLMResponse",
                            traceback="",
                        ),
                    )
                    run_status = "failed"
                    break

                # 解析输出
                try:
                    thought, action = self._parse_output(response_text)
                except Exception as exc:
                    run_status = "error"
                    self._trace_error(run_id, current_step, "parse_action", exc)
                    raise

                parsed_action_input = self._parse_action_input(action) if action else None
                self._trace(
                    run_id,
                    current_step,
                    TraceEvent.PARSED_ACTION,
                    ParsedActionPayload(
                        thought=thought,
                        action=action,
                        action_input=parsed_action_input,
                    ),
                )

                if thought:
                    print(f"🤔 思考: {thought}")

                if not action:
                    print("⚠️ 警告: 未能解析出有效的Action, 流程终止.")
                    self._trace(
                        run_id,
                        current_step,
                        TraceEvent.ERROR,
                        ErrorPayload(
                            stage="parse_action",
                            message="未能解析出有效的Action。",
                            error_type="ActionParseError",
                            traceback="",
                        ),
                    )
                    run_status = "failed"
                    break

                # 检查是否完成
                if action.startswith("Finish"):
                    final_answer = self._parse_action_input(action)
                    print(f"🎉 最终答案: {final_answer}")
                    self._trace(
                        run_id,
                        current_step,
                        TraceEvent.FINISH,
                        FinishPayload(answer=final_answer),
                    )

                    # 保存到历史记录
                    self.add_message(Message(input_text, "user"))
                    self.add_message(Message(final_answer, "assistant"))

                    self._end_trace_run(run_id, current_step, run_status)
                    return final_answer

                # 执行工具调用
                tool_name, tool_parameters_str = self._parse_action(action)
                try:
                    tool_parameters = json.loads(tool_parameters_str)
                except json.JSONDecodeError as exc:
                    self._trace_error(run_id, current_step, "parse_action", exc)
                    self.current_history.append(f"Action: {action}")
                    self.current_history.append(
                        f"""
                        Observation: JSON解析失败: {exc}. 此次Action格式出现问题.
                        请修复并重新输出同一个工具调用, 不要改变任务计划.
                        Action中的方括号必须包住一个完整的JSON object, 例如
                        file_writer[{"paht": "xxx", "content": "xxx", "overwrite": true}]"""
                    )
                    continue
                except TypeError as exc:
                    run_status = "error"
                    self._trace_error(run_id, current_step, "parse_action", exc)
                    raise

                # TODO: 可以通过后处理代码解决"tool_parameter不是Dict类型"的情况, 不过这里先报错, 让LLM重新生成
                # 不过这样会产生不必要的token消耗
                if not isinstance(tool_parameters, dict):
                    self._trace(
                        run_id,
                        current_step,
                        TraceEvent.ERROR,
                        ErrorPayload(
                            stage="parse_action",
                            message="工具参数必须是JSON对象。",
                            error_type="InvalidToolParameters",
                            traceback="",
                        ),
                    )
                    self.current_history.append(
                        'Observation: 工具参数必须是JSON对象, 例如file_search[{"query": "quick_sort"}]'
                    )
                    continue

                if not tool_name or tool_parameters is None:
                    self._trace(
                        run_id,
                        current_step,
                        TraceEvent.ERROR,
                        ErrorPayload(
                            stage="parse_action",
                            message="无效的Action格式。",
                            error_type="InvalidActionFormat",
                            traceback="",
                        ),
                    )
                    self.current_history.append("Observation: 无效的Action格式, 请检查。")
                    continue

                print(f"🎬 行动: {tool_name}[{tool_parameters_str}]")
                self._trace(
                    run_id,
                    current_step,
                    TraceEvent.TOOL_CALL,
                    ToolCallPayload(tool=tool_name, arguments=tool_parameters),
                )

                # 调用工具
                try:
                    observation = self.tool_registry.execute_tool(tool_name, tool_parameters)
                except Exception as exc:
                    run_status = "error"
                    self._trace_error(run_id, current_step, "tool_execution", exc)
                    raise
                self._trace(
                    run_id,
                    current_step,
                    TraceEvent.TOOL_RESULT,
                    ToolResultPayload(
                        tool=tool_name,
                        result=observation,
                    ),
                )
                print(f"👀 观察: {observation}")

                # 更新历史
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")

            print("⏰ 已达到最大步数，流程终止。")
            final_answer = "抱歉，我无法在限定步数内完成这个任务。"
            self._trace(
                run_id,
                current_step,
                TraceEvent.FINISH,
                FinishPayload(answer=final_answer),
            )

            # 保存到历史记录
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(final_answer, "assistant"))

            self._end_trace_run(run_id, current_step, run_status)
            return final_answer
        except Exception as exc:
            if run_status != "error":
                self._trace_error(run_id, current_step, "run", exc)
            self._end_trace_run(run_id, current_step, "error")
            raise
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析LLM输出，提取思考和行动"""
        thought_match = re.search(r"Thought: (.*)", text)
        action_match = re.search(r"Action: (.*)", text)
        
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        
        return thought, action

    def _format_conversation_history(self) -> str:
        """格式化跨轮对话历史，用于拼接到ReAct提示词中。"""
        if not self._history:
            return "无"

        max_history_length = self.config.max_history_length
        if max_history_length <= 0:
            return "无"

        history = self._history[-max_history_length:]
        return "\n".join(f"{message.role}: {message.content}" for message in history)
    
    def _parse_action(self, action_text: str) -> Tuple[Optional[str], Optional[str]]:
        """解析行动文本，提取工具名称和输入"""
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _parse_action_input(self, action_text: str) -> str:
        """解析行动输入"""
        match = re.match(r"\w+\[(.*)\]", action_text)
        return match.group(1) if match else ""

    def _start_trace_run(self) -> int:
        """启动Trace run，Trace失败时保持静默。"""
        if not self.trace_logger:
            return 0
        try:
            return self.trace_logger.start_run()
        except Exception:
            return 0

    def _trace(
        self,
        run_id: int,
        step: int,
        event: TraceEvent,
        payload: Optional[TraceEventPayload] = None,
    ) -> None:
        """记录Trace事件，任何Trace错误都不影响Agent主流程。"""
        if not self.trace_logger:
            return
        try:
            self.trace_logger.log_event(run_id, step, event, payload or {})
        except Exception:
            pass

    def _trace_error(
        self,
        run_id: int,
        step: int,
        stage: str,
        exc: Exception,
    ) -> None:
        """记录异常Trace事件。"""
        self._trace(
            run_id,
            step,
            TraceEvent.ERROR,
            ErrorPayload(
                stage=stage,
                message=str(exc),
                error_type=type(exc).__name__,
                traceback=traceback.format_exc(),
            ),
        )

    def _end_trace_run(self, run_id: int, step: int, status: str) -> None:
        """结束Trace run。"""
        if not self.trace_logger:
            return
        try:
            self.trace_logger.end_run(run_id, step, status)
        except Exception:
            pass

    @staticmethod
    def _create_trace_logger(trace_enabled: Optional[bool]) -> Optional[TraceLogger]:
        """创建TraceLogger，初始化失败不影响Agent。"""
        try:
            return TraceLogger(enabled=trace_enabled)
        except Exception:
            return None
