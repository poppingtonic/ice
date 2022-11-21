from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.paper import Paragraph, Paper
from ice.recipe import recipe
from ice.recipes.primer.qa import answer
from ice.utils import map_async

# document might be long and since we're walking through
# a paragraph at a time

def make_classification_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""
Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:""".strip()

def stringify(para: Paragraph) -> str:
    return para.__str__()

async def classify_paragraph(paragraph: Paragraph, question: str) -> str:
    choice_probs, _ = await recipe.agent().classify(
        prompt=make_classification_prompt(paragraph, question),
        choices=(" Yes", " No"),
    )
    return choice_probs.get(" Yes", 0.0)

async def get_relevant_paragraphs(paper: Paper, question: str, top_n: int = 3) -> list[Paragraph]:
    probs = await map_async(
        paper.paragraphs, lambda par: classify_paragraph(par, question)
    )
    sorted_pairs = sorted(
        zip(paper.paragraphs, probs), key=lambda x: x[1], reverse=True
    )
    return [par for par, prob in sorted_pairs[:top_n]]

async def answer_for_paper(paper: Paper, question: str):
    relevant_pars = await get_relevant_paragraphs(paper, question)
    relevant_str = "\n\n".join(str(p) for p in relevant_pars)
    if relevant_str.strip() == "":
        response = "There is no reference to your question in the document. Please ask another question"
    else:
        response = await answer(context=relevant_str, question=question)
    return response

recipe.main(answer_for_paper)