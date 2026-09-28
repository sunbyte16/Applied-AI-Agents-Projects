import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.agent.agent import agent

sys.stdout.reconfigure(encoding="utf-8")

scenarios = [
    {
        "id": "Test 1 (Direct Answer)",
        "query": "What is machine learning in simple terms?",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 2 (Calculator)",
        "query": "Calculate 9876 * 543",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 3 (Weather)",
        "query": "What's the weather in Hyderabad?",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 4 (Database)",
        "query": "How many products are in the database?",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 5 (Search)",
        "query": "Search for the latest developments in retrieval augmented generation",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 6 (Custom Function)",
        "query": "Analyze my skills for a Machine Learning Engineer role: Python, SQL, TensorFlow",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 7 (Multi-Tool)",
        "query": "Calculate 45 * 72 and tell me the weather in Hyderabad",
        "enabled_tools": ["calculator", "search", "weather", "database", "custom"],
    },
    {
        "id": "Test 8 (Disabled Tool Failure)",
        "query": "What's the weather in Hyderabad?",
        "enabled_tools": ["calculator", "search", "database", "custom"],  # weather intentionally omitted
    },
]

print("======================================================================")
print("AGENTLAB AI — LIVE EVALUATION AUDIT OF ALL 8 DEMO TEST CASES")
print("======================================================================\n")

for sc in scenarios:
    print(f"--- Running {sc['id']} ---")
    print(f"Query: \"{sc['query']}\"")
    print(f"Enabled Tools: {sc['enabled_tools']}")
    try:
        res = agent.chat(
            message=sc["query"],
            enabled_tools=sc["enabled_tools"],
        )
        print(f"Status: {'SUCCESS' if res.success else 'FAILED'}")
        print(f"Tool Calls Executed: {res.tool_calls_executed}")
        tools_called = [t.tool for t in res.trace if t.type == "tool_call"]
        print(f"Tools Called: {tools_called}")
        print(f"Answer Preview: {res.answer[:180]}...")
    except Exception as e:
        print(f"Execution Error: {e}")
    print("\n")
