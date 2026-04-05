def evaluate_answer(answer: str):
    score = 1.0
    if "I don't know" in answer:
            score -= 0.3
    if len(answer) < 50:
        score -= 0.2
    return round(max(score, 0), 2)