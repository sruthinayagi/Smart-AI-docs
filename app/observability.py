import time
def log_event(event, data):
    print({
        "event": event,
        "timestamp": time.time(),
        "details": data
    })

# Usage in agent
# log_event("retrieval", {"query": state["question"]})
# log_event("tool_call", {"tool": state["tool_choice"]})
# log_event("final_score", {"score": state["score"]})