from ice.recipe import recipe

def make_subquestion_prompt(question: str) -> str:
    return f"""Decompose the following question in to 2-5 subquestions that would help you answer the question. Make each question stand alone, so they can be answered without the context of the original question.
Question: "{question}"
Subquestions:
""".strip()

async def ask_subquestions(question: str = "What is the effect of rapamycin on aging?"):
    prompt = make_subquestion_prompt(question)
    subquestions_text = await recipe.agent().complete(prompt=prompt)
    subquestions = [line.strip("- ") for line in subquestions_text.split("\n")]
    return subquestions

recipe.main(ask_subquestions)