import os
import shutil
import yaml
import importlib.resources

from smolagents import ActionStep, TaskStep

from dotenv import load_dotenv
from mcp import StdioServerParameters
from smolagents import LiteLLMModel, ToolCallingAgent
from smolagents.tools import ToolCollection
from contextlib import AsyncExitStack
import asyncio

# ——— Load environment variables ———
load_dotenv()
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BRAVE_API_KEY:
    raise RuntimeError("BRAVE_API_KEY not set in .env")
if not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY not set; OpenAI-backed LLMs may not work")

# ——— Define MCP server parameters ———
brave_server_params = StdioServerParameters(
    command=shutil.which("npx"),
    args=["-y", "@modelcontextprotocol/server-brave-search"],
    env={**os.environ, "BRAVE_API_KEY": BRAVE_API_KEY},
)

crawl4ai_server_params = StdioServerParameters(
    command="uv",
    args=[
        "--directory",
        "/your-path-to-mcp/crawl4ai-mcp",
        "run",
        "main.py"
    ],
    transportType="stdio"
)


# ——— Your custom system prompt ———
SYSTEM_PROMPT_TEMPLATE = """
You are a helpful assistant that can use tools to answer questions.

Available tools:
{%- for tool in tools.values() %}
- {{tool.name}}: {{tool.description}}
  Inputs: {{tool.inputs}}
  Returns: {{tool.output_type}}
{%- endfor %}
"""

class SmolAgentWithMCP:
    def __init__(self, server_params_list):
        print("🔎 SmolAgents + Multiple MCP Servers Example")
        self._exit_stack = AsyncExitStack()
        self.tool_collections = []
        all_tools = []

        # ——— 2. Spin up the MCP stdio servers and wrap their tools ———
        for params in server_params_list:
            try:
                tc_context = ToolCollection.from_mcp(params, trust_remote_code=True)
                # Use the with statement correctly to get the ToolCollection instance
                tc = self._exit_stack.enter_context(tc_context)
                self.tool_collections.append(tc)
                all_tools.extend(list(tc.tools))
                tool_names = [t.name for t in tc.tools]
                print(f"✅ Loaded tools from {params.command}: {tool_names}")
            except Exception as e:
                print(f"❌ Failed to load tools from {params.command}: {e}")
                # Continue with other servers even if one fails
                continue


        # ——— 1. Load default prompt templates & override "system_prompt" ———
        raw = importlib.resources.files("smolagents.prompts") \
                .joinpath("toolcalling_agent.yaml") \
                .read_text()
        prompt_templates = yaml.safe_load(raw)
        prompt_templates["system_prompt"] = SYSTEM_PROMPT_TEMPLATE

        # ——— 3. Initialize model and agent ———
        model = LiteLLMModel(model_id="gpt-4o-mini")
        self.agent = ToolCallingAgent(
            tools=all_tools,
            model=model,
            prompt_templates=prompt_templates,
        )

    def run(self):
        """Runs the main interaction loop with the agent."""
        print("🤖 Agent ready. Type a query or 'exit' to quit.")

        # Need to run the interaction loop within an async context to properly manage the exit stack
        asyncio.run(self._run_async())

    async def _run_async(self):
        """Asynchronous part of the interaction loop."""
        async with self._exit_stack:
            while True:
                q = input("\n[You] ").strip()
                if q.lower() in ("exit", "quit"):
                    print("👋 Goodbye!")
                    break

                try:
                    print("\n[Agent]")
                    # Add the user query as a new TaskStep
                    self.agent.memory.steps.append(TaskStep(task=q, task_images=[]))

                    final_answer = None
                    # Start step numbering from the next available step number
                    step_number = len(self.agent.memory.steps)
                    while final_answer is None:
                        memory_step = ActionStep(
                            step_number=step_number,
                            observations_images=[],
                        )
                        # Run one step.
                        final_answer = self.agent.step(memory_step)
                        self.agent.memory.steps.append(memory_step)
                        step_number += 1

                    print(final_answer)

                except Exception as e:
                    print(f"[Error] {e}")
                    import traceback
                    traceback.print_exc()

    def __del__(self):
        """Ensures the exit stack is closed when the app is deleted."""
        # The AsyncExitStack should be closed by the async with statement in _run_async
        # This __del__ is just a fallback, but the primary cleanup happens in _run_async
        pass


def main():
    # Define the list of MCP server parameters
    server_list = [
        brave_server_params,
        crawl4ai_server_params
        # Add other server parameters here as needed
    ]
    app = SmolAgentWithMCP(server_list)
    app.run()

if __name__ == "__main__":
    main()
