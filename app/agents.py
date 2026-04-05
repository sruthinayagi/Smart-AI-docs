from langgraph.graph import StateGraph
from app.tools import TOOLS
from app.rag_pipeline import query_docs
from app.evaluator import evaluate_answer
from app.config import call_llm

class State(dict):
    question: str
    context: str
    tool_output: str
    final_answer: str
    tool_choice: str
    score: float

graph = StateGraph(State)

async def retrieve(state):
    docs = await query_docs(state["question"])
    state["context"] = "\n".join([d.page_content for d in docs])
    return state

async def decide_tool(state):
    q = state["question"].lower()
    print(q)
    if "rfc" in q:
        state["tool_choice"] = "summarize_rfc"
        print("Tool chosen: summarize_rfc")
    elif "architecture" in q:
        state["tool_choice"] = "validate_architecture"
    elif "topic" in q:
        state["tool_choice"] = "summarize_topic"
    else:
        state["tool_choice"] = None

    return state

async def call_tool(state):
    tool_choice = state.get("tool_choice")
    if not tool_choice:
        return state
    tool_fn = TOOLS[tool_choice]
    state["tool_output"] = tool_fn(state["context"], state["question"])
    return state

async def generate_answer(state):
    prompt = f"""
    Question: {state['question']}
    Context: {state['context']}
    Tool Output: {state.get('tool_output', '')}
    Answer concisely with citations.
    """
    state["final_answer"] = call_llm(prompt)
    return state

async def evaluate(state):
    state["score"] = evaluate_answer(state["final_answer"])
    return state

graph.add_node("retrieve", retrieve)
graph.add_node("decide_tool", decide_tool)
graph.add_node("call_tool", call_tool)
graph.add_node("generate_answer", generate_answer)
graph.add_node("evaluate", evaluate)

graph.add_edge("retrieve", "decide_tool")
graph.add_edge("decide_tool", "call_tool")
graph.add_edge("call_tool", "generate_answer")
graph.add_edge("generate_answer", "evaluate")

graph.set_entry_point("retrieve")
graph.set_finish_point("evaluate")

smartdocs_agent = graph.compile()
