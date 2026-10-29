# Part 3: Practical Evaluation

## 1. Overview

This implementation provides a simple command-line agent that answers questions using one supplied document, maintains conversation context during the current session, and decides when to call a calculator tool. It uses Gemini API calls through Google's OpenAI-compatible endpoint.

## 2. Sample Document

The agent loads `docs/sample-product-faq.md` when it starts. The document contains plan prices, storage limits, support hours, and password-reset instructions. It deliberately states that no refund policy is provided, allowing unsupported-answer behavior to be demonstrated.

The system instruction requires the agent to use only the document and conversation context for factual answers. When the document does not contain the requested information, the agent must say so instead of inventing an answer.

## 3. Conversation Memory

Every user message, model response, function call, and function result is appended to an in-memory message history. This history is included in later requests, allowing the agent to remember information such as the user's name and previous questions. Memory lasts for the current terminal session and is cleared when the program exits.

## 4. Calculator Tool

The calculator is supplied to the model as a function tool using automatic tool selection. The model can answer document lookups and memory questions directly. It calls the calculator only when arithmetic is required.

The calculator parses a restricted arithmetic expression and supports addition, subtraction, multiplication, and division. It rejects arbitrary Python execution, overly long expressions, and excessively large results. A three-call limit prevents an uncontrolled tool loop.

## 5. Verification

The following live Gemini conversation was completed successfully:

1. `My name is Alex.` — the agent acknowledged the name.
2. `What is the price of the Pro plan?` — it answered `$12 per month`, based on the document.
3. `What is my name?` — it remembered Alex.
4. `How much do 3 months of the Pro plan cost?` — it called the calculator and answered `$36`.
5. `What is the refund policy?` — it stated that the document does not specify one.

The calculator did not run for document lookup or memory recall. The automated test suite also contains calculator correctness and code-execution rejection tests; all 18 project tests pass.

## 6. Limitations

- Memory is session-based and is not stored after exit.
- The entire sample document is included in the prompt because it is small. Larger document collections would require retrieval and chunking.
- Gemini Free Tier availability and rate limits depend on the selected model and Google AI Studio project.
- Model behavior is probabilistic, so production use would require a larger evaluation set and monitoring.
