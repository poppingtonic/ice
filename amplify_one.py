"""Recursive Amplification"""
from ice.recipe import recipe
from subquestions import ask_subquestions
from ice.utils import map_async

Question = str
Answer = str
Subs = list[tuple[Question, Answer]]

def render_background(subs: Subs) -> str:
    if not subs:
        return ""
    subs_text = "\n\n".join(f"Q: {q}\nA: {a}" for (q, a) in subs)
    return f"Here is relevant background information:\n\n{subs_text}\n\n"

def make_qa_prompt(question: str, subs: Subs) -> str:
    background_text = render_background(subs)
    return f"""{background_text}Answer the following question, using the background information provided above, wherever helpful:

Question: "{question}"
Answer: "
"""

async def get_subs(question: str) -> Subs:
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(subquestions, answer)
    return list(zip(subquestions, subanswers))

async def answer(question: str, subs: Subs = []) -> str:
    prompt = make_qa_prompt(question=question, subs=subs)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer

async def answer_by_amplification(question: str = "What is the effect of rapamycin on aging?"):
    """Answer a question by asking subquestions, answering them and using the resulting background information as context."""
    subs = await get_subs(question)
    response = await answer(question=question, subs=subs)
    return response

recipe.main(answer_by_amplification)