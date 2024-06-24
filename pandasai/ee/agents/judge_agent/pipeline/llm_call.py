from typing import Any

from pandasai.exceptions import InvalidOutputValueMismatch
from pandasai.helpers.logger import Logger
from pandasai.pipelines.base_logic_unit import BaseLogicUnit
from pandasai.pipelines.logic_unit_output import LogicUnitOutput
from pandasai.pipelines.pipeline_context import PipelineContext


class LLMCall(BaseLogicUnit):
    """
    LLM Code Generation Stage
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def execute(self, input: Any, **kwargs) -> Any:
        """
        This method will return output according to
        Implementation.

        :param input: Your input data.
        :param kwargs: A dictionary of keyword arguments.
            - 'logger' (any): The logger for logging.
            - 'config' (Config): Global configurations for the test
            - 'context' (any): The execution context.

        :return: The result of the execution.
        """
        pipeline_context: PipelineContext = kwargs.get("context")
        logger: Logger = kwargs.get("logger")

        retry_count = 0
        while retry_count <= pipeline_context.config.max_retries:
            response = pipeline_context.config.llm.call(input, pipeline_context)

            logger.log(
                f"""LLM response:
                    {response}
                    """
            )
            try:
                result = False
                if "<Yes>" in response:
                    result = True
                elif "<No>" in response:
                    result = False
                else:
                    raise InvalidOutputValueMismatch("Invalid response of LLM Call")

                pipeline_context.add("llm_call", response)

                return LogicUnitOutput(
                    result,
                    True,
                    "Code Generated Successfully",
                    {"content_type": "string", "value": response},
                )
            except Exception:
                if retry_count == pipeline_context.config.max_retries:
                    raise

                retry_count += 1
