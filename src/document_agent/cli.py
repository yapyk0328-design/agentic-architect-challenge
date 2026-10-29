"""Interactive Gemini document Q&A with session memory and a calculator tool."""

import ast
import json
import operator
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI

DOCUMENT = Path(__file__).resolve().parents[2] / "docs" / "sample-product-faq.md"
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def calculate(expression: str) -> float:
    """Evaluate arithmetic only; never execute arbitrary Python code."""
    if len(expression) > 100:
        raise ValueError("Expression too long")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError("Only basic arithmetic is supported")

    result = evaluate(ast.parse(expression, mode="eval"))
    if abs(result) > 1e12:
        raise ValueError("Result too large")
    return result


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("error: GEMINI_API_KEY is missing. Copy .env.example to .env and add your Gemini API key.", file=sys.stderr)
        return 1
    model = os.getenv("GEMINI_MODEL")
    if not model:
        print("error: GEMINI_MODEL is missing. Set it in .env to a Free Tier model available to your project.", file=sys.stderr)
        return 1
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout=25.0,
        max_retries=0,
    )
    document = DOCUMENT.read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": "Answer questions using only this document and the conversation. Remember the user's name and earlier context in this session. If the document does not answer a factual question, say so. Use the calculator tool only when arithmetic is needed. Do not invent policy details. Document:\n" + document}
    ]
    tools = [{"type": "function", "function": {"name": "calculator", "description": "Calculate basic arithmetic when needed; do not call for simple document lookup or memory recall.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"], "additionalProperties": False}}}]
    print("Document agent ready. Type 'exit' to quit.")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        turn_start = len(messages)
        messages.append({"role": "user", "content": question})
        try:
            for _ in range(3):
                print("Contacting Gemini (up to 25 seconds)...", flush=True)
                response = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto")
                answer = response.choices[0].message
                calls = answer.tool_calls or []
                # Keep Gemini-specific metadata such as thought_signature exactly as
                # returned. It is required when sending a function result back.
                messages.append(answer.model_dump(exclude_none=True))
                if not calls:
                    print("Agent:", answer.content or "No answer returned.")
                    break
                for call in calls:
                    if call.function.name == "calculator":
                        try:
                            output = str(calculate(json.loads(call.function.arguments)["expression"]))
                        except (ValueError, ZeroDivisionError, SyntaxError, KeyError) as exc:
                            output = f"Calculator error: {exc}"
                        print("[calculator called]")
                    else:
                        output = "Unknown tool"
                    messages.append({"role": "tool", "name": call.function.name, "tool_call_id": call.id, "content": output})
            else:
                print("Agent: Tool call limit reached.")
        except (APIConnectionError, APITimeoutError) as exc:
            del messages[turn_start:]
            print("Error: Gemini did not respond within 25 seconds or the network connection failed. Check your internet connection and try again.")
        except Exception as exc:
            del messages[turn_start:]
            print(f"Error: {exc}")
    return 0


if __name__ == "__main__":
    main()
