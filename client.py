from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool as MCPTool
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam as OpenAITool, ChatCompletionMessageParam as OpenAIChatCompletionMessageParam, ChatCompletion as OpenAIChatCompletion
from openai.types import FunctionDefinition as OpenAIFunctionDefinition
import asyncio
from dotenv import load_dotenv
from typing import List
import json
import os

def parse_tool_for_openai(tool: MCPTool) -> OpenAITool:
    """
    Converts a Tool object into OpenAI API-compatible tool format.
    """
    return OpenAITool(
        type="function",
        function=OpenAIFunctionDefinition(
            name=tool.name,
            description=tool.description.strip(),
            parameters={
                "type": "object",
                "properties": tool.inputSchema.get("properties", {}),
                "required": tool.inputSchema.get("required", [])
            }
        )
    )

async def main():
    server_url = os.getenv("MCP_SERVER_URL")
    model = "gpt-4o-mini"
    openai_client = OpenAI()
    messages: List[OpenAIChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to tools",
        }
    ]
    try:
        async with sse_client(server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream=read_stream, write_stream=write_stream) as session:
                await session.initialize()
                print(f"Connected to server at {server_url}")
                
                # List available tools
                list_tools_result = await session.list_tools()
                tools = [parse_tool_for_openai(tool) for tool in list_tools_result.tools]
                
                query = input("Question: ")
                messages.append({
                    "role": "user",
                    "content": query
                })
                
                while query != "q":
                    try:
                        openai_chat_response: OpenAIChatCompletion = openai_client.chat.completions.create(
                            model=model,
                            tools=tools,
                            tool_choice="auto",
                            temperature=0,
                            messages=messages
                        )
                        message_content = openai_chat_response.choices[0].message.content
                        if message_content != None:
                            print(message_content)
                    except Exception as e:
                        print(f"Error calling OpenAI: {e}")
                        return
                    messages.append(openai_chat_response.choices[0].message)
                    finish_reason = openai_chat_response.choices[0].finish_reason
                    if finish_reason == "tool_calls":
                        tool_calls = openai_chat_response.choices[0].message.tool_calls
                        for tool_call in tool_calls:
                            try:
                                allow_tool_call = input(f"Allow tool call {tool_call.function.name} with arguments {json.loads(tool_call.function.arguments)}? (y/n) ")
                                if allow_tool_call.lower() == 'y':
                                    tool_response = await session.call_tool(
                                        name=tool_call.function.name,
                                        arguments=json.loads(tool_call.function.arguments)
                                    )
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": tool_response.content[0].text
                                    })
                                else:
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": "The tool call request was refused by the user."
                                    })
                            except Exception as e:
                                print(f"Error calling tool: {e}")
                                return
                    else:
                        query = input("Question: ")
                        messages.append({
                            "role": "user",
                            "content": query
                        })
                
    except Exception as e:
        print(f"Error connecting to server: {e}")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())


