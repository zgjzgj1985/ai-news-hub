"""本地LLM客户端 - 连接Ollama/Qwen3.5 9B"""

import json
import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv

# 尝试加载.env文件
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)  # 强制覆盖系统环境变量

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM响应封装"""
    content: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None


class LLMClient:
    """
    本地LLM客户端 - 通过Ollama API调用Qwen3.5 9B

    使用方式：
    ```python
    client = LLMClient()
    if client.is_available():
        response = await client.chat([{"role": "user", "content": "你好"}])
    ```
    """

    DEFAULT_MODEL = "qwen3.5:9b"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_TIMEOUT = 120

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        temperature: float = 0.1,
        max_retries: int = 2
    ):
        """初始化LLM客户端"""
        self.model = model or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("LLM_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建异步HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={"Accept-Charset": "utf-8"}
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        """
        同步检查LLM服务是否可用

        返回:
            bool: 服务可用返回True
        """
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM服务不可用: {e}")
            return False

    async def a_is_available(self) -> bool:
        """
        异步检查LLM服务是否可用
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM服务不可用: {e}")
            return False

    def list_models(self) -> List[str]:
        """
        获取已安装的模型列表

        返回:
            List[str]: 模型名称列表
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []

    async def chat(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """
        发送对话请求

        参数:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            json_mode: 是否要求JSON输出
            temperature: 温度参数
            stream: 是否流式输出

        返回:
            str: LLM响应内容
        """
        client = await self._get_client()

        # 构建请求
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature or self.temperature,
            }
        }

        # JSON模式配置
        if json_mode:
            payload["format"] = "json"

        # 添加思考标签以适配Qwen3/Qwen3.5
        if "qwen3" in self.model.lower():
            payload["think"] = False

        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()

                # 解析响应（Ollama可能返回流式或单条响应）
                data = response.json()
                content = data.get("message", {}).get("content", "")

                # 确保内容是有效的字符串，并正确处理Unicode转义
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                elif not isinstance(content, str):
                    content = str(content)

                # 如果内容是被转义的JSON字符串，需要再次解析
                # Ollama有时会返回 {"greeting": "\u4f60\u597d"} 这样的字符串
                try:
                    # 尝试解析content本身是否是JSON
                    inner = json.loads(content)
                    if isinstance(inner, dict):
                        # 递归处理内部的值
                        content = json.dumps(inner, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    # content不是JSON字符串，保持原样
                    pass

                return content

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP错误: {e.response.status_code}"
                retry_count += 1
            except Exception as e:
                last_error = str(e)
                retry_count += 1

            if retry_count < self.max_retries:
                import asyncio
                await asyncio.sleep(1 * retry_count)  # 指数退避

        logger.error(f"LLM请求失败，已重试{self.max_retries}次: {last_error}")
        raise RuntimeError(f"LLM请求失败: {last_error}")

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: Optional[float] = None,
        json_mode: bool = False
    ) -> str:
        """
        生成文本（简化接口）

        参数:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            json_mode: 是否要求JSON输出

        返回:
            str: 生成的文本
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, json_mode=json_mode, temperature=temperature)

    async def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON响应，处理可能的markdown代码块

        参数:
            response: LLM原始响应

        返回:
            Dict: 解析后的JSON对象，失败返回None
        """
        import re

        # 确保响应是有效的UTF-8
        try:
            response = response.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            response = response.encode('utf-8', errors='replace').decode('utf-8')

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取markdown代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)

        if json_match:
            json_str = json_match.group(1).strip()
            try:
                result = json.loads(json_str)
                # 确保结果中的中文正确
                return self._ensure_chinese(result)
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号包裹的JSON
        brace_match = re.search(r'\{[\s\S]*\}', response)
        if brace_match:
            try:
                result = json.loads(brace_match.group())
                return self._ensure_chinese(result)
            except json.JSONDecodeError:
                pass

        logger.warning(f"无法解析JSON响应: {response[:200]}...")
        return None

    def _ensure_chinese(self, obj):
        """确保JSON对象中的中文正确处理"""
        if isinstance(obj, dict):
            return {k: self._ensure_chinese(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_chinese(item) for item in obj]
        elif isinstance(obj, str):
            # 尝试重新编码以确保中文正确
            try:
                return obj.encode('utf-8').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                return obj.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        return obj


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端实例（每次返回新实例，避免跨事件循环复用导致连接池失效）"""
    return LLMClient()
