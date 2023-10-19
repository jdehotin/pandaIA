"""OpenAI LLM via Microsoft Azure Cloud

This module is to run the OpenAI API when using Microsoft Cloud infrastructure.
Azure has implemented the openai API access to its platform.
For details https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference.

Example:
    Use below example to call AzureOpenAI class

    >>> from pandasai.llm.azure_openai import AzureOpenAI

"""

import os
from typing import Any, Dict, Optional

from litellm import Router
import openai
from ..helpers import load_dotenv

from ..exceptions import APIKeyNotFoundError, MissingModelError
from ..prompts.base import AbstractPrompt
from .base import BaseOpenAI

load_dotenv()


class AzureOpenAI(BaseOpenAI):
    """OpenAI LLM via Microsoft Azure
    This class uses `BaseOpenAI` class to support Azure OpenAI features.
    """

    api_base: str
    api_type: str = "azure"
    api_version: str
    engine: str

    def __init__(
        self,
        api_token: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment_name: str = None,
        is_chat_model: bool = True,
        **kwargs,
    ):
        """
        __init__ method of AzureOpenAI Class.

        Args:
            api_token (str): Azure OpenAI API token.
            api_base (str): Base url of the Azure endpoint.
                It should look like the following:
                <https://YOUR_RESOURCE_NAME.openai.azure.com/>
            api_version (str): Version of the Azure OpenAI API.
                Be aware the API version may change.
            deployment_name (str): Custom name of the deployed model
            is_chat_model (bool): Whether ``deployment_name`` corresponds to a Chat
                or a Completion model.
            **kwargs: Inference Parameters.
        """

        model_list = [{ # list of model deployments 
            "model_name": "gpt-3.5-turbo", # openai model name 
            "litellm_params": { # params for litellm completion/embedding call 
                "model": f"azure/{deployment_name}", 
                "api_key": api_token,
                "api_version": api_version,
                "api_base": api_base
            },
            "tpm": 240000,
            "rpm": 1800
        }]
        if self.api_token is None:
            raise APIKeyNotFoundError(
                "Azure OpenAI key is required. Please add an environment variable "
                "`OPENAI_API_KEY` or pass `api_token` as a named parameter"
            )
        if self.api_base is None:
            raise APIKeyNotFoundError(
                "Azure OpenAI base is required. Please add an environment variable "
                "`OPENAI_API_BASE` or pass `api_base` as a named parameter"
            )
        if self.api_version is None:
            raise APIKeyNotFoundError(
                "Azure OpenAI version is required. Please add an environment variable "
                "`OPENAI_API_VERSION` or pass `api_version` as a named parameter"
            )
        if deployment_name is None:
            raise MissingModelError(
                "No deployment name provided.",
                "Please include deployment name from Azure dashboard.",
            )

        self.router = Router(model_list=model_list)

        self.is_chat_model = is_chat_model
        self.engine = deployment_name

        self.openai_proxy = kwargs.get("openai_proxy") or os.getenv("OPENAI_PROXY")
        if self.openai_proxy:
            openai.proxy = {"http": self.openai_proxy, "https": self.openai_proxy}

        self._set_params(**kwargs)

    @property
    def _default_params(self) -> Dict[str, Any]:
        """
        Get the default parameters for calling OpenAI API.

        Returns:
            dict: A dictionary containing Default Params.

        """
        return {**super()._default_params, "engine": self.engine}

    def call(self, instruction: AbstractPrompt, suffix: str = "") -> str:
        """
        Call the Azure OpenAI LLM.

        Args:
            instruction (AbstractPrompt): A prompt object with instruction for LLM.
            suffix (str): Suffix to pass.

        Returns:
            str: LLM response.

        """
        self.last_prompt = instruction.to_string() + suffix

        if self.is_chat_model:
            response = self.router.completion(self.last_prompt)
        else:
            response = self.router.text_completion(self.last_prompt)

        return response

    @property
    def type(self) -> str:
        return "azure-openai"
