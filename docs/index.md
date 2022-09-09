<h1>Language model composition with ICE: A tutorial</h1>

In this tutorial we'll learn how to get language models to do complex tasks by composing together multiple calls.

We'll call programs that describe such compositions _recipes_.

<h2>Contents</h2>

* TOC
{:toc}

## Before we start

This tutorial requires that you've set up ICE as described in [the ICE README](https://github.com/oughtinc/ice9#interactive-composition-explorer-).

## The simplest recipe: Hello world!

Let's first get used to the infrastructure for writing, running, and debugging recipes:

Create a file `hello_world.py`:

```py
from ice.recipe import Recipe

class HelloWorld(Recipe):
    async def execute(self):
        return "Hello world!"
```

Run the recipe:

```sh
scripts/run-recipe.sh -r hello_world.py -t
```

This will run the recipe, creating an execution trace (`-t`).

On the terminal, after a few lines about Docker and the trace link, you should see this:

```
Hello world!
```

If you follow the link, in your browser you should see a function node that you can click on, expand, and inspect inputs/outputs and source code.

Some things to note about the recipe:

- We're inhering from the `Recipe` class because that will give us automatic tracing of all async methods for debugging. (Synchronous methods are currently assumed to be simple and fast, and not worth tracing.)
- `execute` is the name of the method that is called when a recipe is run
- Most recipe methods, including `execute`, will be async so that language model calls are parallelized as much as possible.
- Different recipes take different arguments, which will be provided as keyword-only arguments. This recipe doesn't use any arguments.

### Exercises

1. Add another method to `HelloWorld` and call it from `execute`. Does it show up in the trace? What if you make it async and call it as `result = await self.my_function()`?

## Calling an agent: Question-answering

Now let's make our first recipe `qa.py` that calls out to an agent.

### Context-free question-answering

```py
from ice.recipe import Recipe


def make_qa_prompt(question: str) -> str:
    return f"""Answer the following question:

Question: "{question}"
Answer: "
""".strip()


class QA(Recipe):
    async def execute(self, *, question: str = "What is happening on 9/9/2022?"):
        prompt = make_qa_prompt(question)
        answer = (await self.agent().answer(question=prompt)).strip('" ')
        return answer
```

We can run recipes in different modes, which controls what type of agent is used. Some examples:

- `machine`: Use an automated agent (usually GPT-3 if no hint is provided in the agent call). This is the default mode.
- `human`: Elicit answers from you using a command-line interface.
- `augmented`: Elicit answers from you, but providing the machine-generated answer as a default.

You specify the mode like this:

```sh
scripts/run-recipe.sh -r qa.py -t -m human
```

Try running your recipe in different modes.

Things to note:

- Because the agent's `answer` method is async, we have to use `await`

### Answering questions about short texts

It's only a small change from the above to support answering questions about short texts (e.g. individual paragraphs):

```py
from ice.recipe import Recipe


DEFAULT_CONTEXT = "We're running a hackathon on 9/9/2022 to decompose complex reasoning tasks into subtasks that are easier to automate & evaluate with language models. Our team is currently breaking down reasoning about the quality of evidence in randomized controlled trials into smaller tasks e.g. placebo, intervention adherence rate, blinding procedure, etc."

DEFAULT_QUESTION = "What is happening on 9/9/2022?"


def make_qa_prompt(context: str, question: str) -> str:
    return f"""
Background text: "{context}"

Answer the following question about the background text above:

Question: "{question}"
Answer: "
""".strip()


class QA(Recipe):
    async def execute(
        self, context: str = DEFAULT_CONTEXT, question: str = DEFAULT_QUESTION
    ) -> str:
        prompt = make_qa_prompt(context, question)
        answer = (await self.agent().answer(question=prompt)).strip('" ')
        return answer
```

You should see a response like this:

```
A hackathon is happening on 9/9/2022.
```

### Exercises

1. Instead of answering directly, add "Let's think step by step" as a prefix to the answer part of the prompt. This is often referred to as chain-of-thought prompting.
2. After getting the answer, add another step that shows the question and answer to the agent and asks it to improve the answer.
3. Now iterate the improvement step until the answer stops changing or some # of steps is exceeded. Does this work? This is similar to diffusion models which take a noisy image and iteratively refine it until it's clear and detailed.

## Composing calls to agents: Debate

Let's implement debate to see how recipes can compose together multiple calls to agents. We'll investigate a question by having two agents take different sides on the same question.

### Representing debates

We'll represent debates as lists of turns. Each turn has the name of an agent and a message from that agent. For example:

```py
my_debate = [
  ("Alice", "I think we should legalize all drugs."),
  ("Bob", "I'm against."),
  ("Alice", "The war on drugs has been a failure. It's time to try something new.")
]
```

Here's how we'll represent and render debates:

```py
Name = str
Message = str
Turn = tuple[Name, Message]
Debate = list[Turn]


def initialize_debate(question: Message) -> Debate:
    return [
        ("Question", question),
        ("Alice", "I'm in favor."),
        ("Bob", "I'm against."),
    ]


def render_debate(debate: Debate, self_name: Name | None = None) -> str:
    debate_text = ""
    for speaker, text in debate:
        if speaker == self_name:
            speaker = "You"
        debate_text += f'{speaker}: "{text}"\n'
    return debate_text.strip()
```

When we render debates, we also provide the option to replace an agent name with "You", like this:

```py
>>> print(render_debate(my_debate, self_name="Alice"))
```

```
You: "I think we should legalize all drugs."
Bob: "I'm against."
You: "The war on drugs has been a failure. It's time to try something new."
```

This will help us with prompts!

### From debates to prompts

A prompt is a debate with some instructions and a prefix for a new response. We create it like this:

```py
def render_debate_prompt(agent_name: str, debate: Debate, turns_left: int) -> str:
    prompt = f"""
You are {agent_name}. There are {turns_left} turns left in the debate. You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.

{render_debate(debate, agent_name)}
You: "
""".strip()
    return prompt
```

When we apply it to the debate above, we get:

```py
>>> print(render_debate_prompt("Bob", my_debate, 5))
```

```
You are Bob. There are 5 turns left in the debate. You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.

Alice: "I think we should legalize all drugs."
You: "I'm against."
Alice: "The war on drugs has been a failure. It's time to try something new."
You: "
```

### The recipe

If you want to challenge yourself, pause and see if you can use the pieces above to write a recipe that has agents take turns at a debate about a question.

Once you're ready, or if you just want to see the result, take a look at this recipe:

```py
from ice.agents.base import Agent
from ice.recipe import Recipe

class DebateRecipe(Recipe):

    async def execute(self, *, question: str = "Should we legalize all drugs?"):
        agents = [self.agent(), self.agent()]
        agent_names = ["Alice", "Bob"]
        debate = initialize_debate(question)
        turns_left = 8
        while turns_left > 0:
            for agent, agent_name in zip(agents, agent_names):
                turn = await self.turn(debate, agent, agent_name, turns_left)
                debate.append(turn)
                turns_left -= 1
        return render_debate(debate)

    async def turn(
        self, debate: Debate, agent: Agent, agent_name: Name, turns_left: int
    ):
        prompt = render_debate_prompt(agent_name, debate, turns_left)
        answer = await agent.answer(
            question=prompt, multiline=False, max_tokens=100
        )
        return (agent_name, answer.strip('" '))
```

Once you've saved the recipe in `debate.py` you can run it as usual:

```sh
scripts/run-recipe.sh -r debate.py -t
```

You should see a debate like this:

```
Question: "Should we legalize all drugs?"
Alice: "I'm in favor."
Bob: "I'm against."
Alice: "The war on drugs has been a failure. It's time to try something new."
Bob: "Legalizing drugs would lead to more drug use and more addiction. It's not the answer."
Alice: "There is evidence that drug use would go down when drugs are legalized. In Portugal, where all drugs have been legal since 2001, drug use has declined among young people."
Bob: "Even if drug use declines, the number of addicts will increase. And more addicts means more crime."
Alice: "Addiction rates would not necessarily increase. In fact, they could go down, because people would have better access to treatment."
Bob: "Treatment is expensive, and most addicts can't afford it. Legalizing drugs would just make the problem worse."
Alice: "The government could fund treatment programs. And people would be less likely to need treatment if they could get drugs legally."
Bob: "It's not that simple. Legalizing drugs would create a lot of new problems."
```

Some things to note:

- In `agents = [self.agent(), self.agent()]` we're creating two agents. This doesn't actually matter since all the agents we're using in ICE right now don't have implicit state (except for humans), so we could just have created agents on the fly in the `turn` function.

### Exercises

1. Add a judge agent at the end that decides which agent won the debate. In the original debate proposal, these judgments would be used to RL-finetune the parameters of the debate agents.
2. Generate model judgments directly (only given the question) and after debate. Are there systematic differences between these judgments? You could also use models to generate the questions if you need a larger input set.


## Reasoning about external content: Paper Q&A

Ultimately we'd like for language models to help us make sense of more information than we can read and understand ourselves. As a small step in that direction, let's make a recipe that answers questions about a paper.

### Loading papers in recipes

ICE has built-in functionality for parsing and loading papers, and includes some example papers in its `papers` folder. Here's a minimal recipe that loads a paper and prints out the first paragraph (often the abstract):

```py
from ice.recipe import Recipe

class PaperQA(Recipe):
    async def execute(self, **kw):
        paper = kw['paper']
        return paper.paragraphs[0]
```

If you have this recipe as `paperqa.py`, you can run it as follows, providing a paper as input (`-i`):

```sh
scripts/run-recipe.sh -r paperqa.py -t -i papers/keenan-2018.pdf
```

You'll see a result like this:

```py
Paragraph(sentences=['We hypothesized that mass distribution of a broad-spectrum antibiotic agent to preschool children would reduce mortality in areas of sub-Saharan Africa that are currently far from meeting the Sustainable Development Goals of the United Nations.'], sections=[Section(title='Abstract', number=None)], section_type='abstract')
```

Note that:

- Papers are represented as lists of paragraphs
- Paragraphs are represented as lists of sentences
- Each paragraph has information about which section it's from

Feel free to try it with your own papers!

### Finding the most relevant paragraphs

In this recipe we'll take a simple approach:

1. Classify for each paragraph whether it answers the question or not
2. Take the paragraphs with the highest probability of answering the question and ask a model to answer the question given those paragraphs. For this step we can use the QA recipe from above.

#### Classifying individual paragraphs using `prompted_classify`

Let's start by just classifying whether the first paragraph answers a question. To do this, we'll use a new agent method, `prompted_classify`. It takes a context, a question, and a list of choices, and returns a choice, a choice probability, and for some agent implementations an explanation.

Our single-paragraph classifier looks like this:

```py
from ice.recipe import Recipe
from ice.paper import Paragraph

def make_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""
Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:""".strip()

class PaperQA(Recipe):

    async def classify_paragraph(self, paragraph: Paragraph, question: str) -> float:
        choice, choice_prob, _ = await self.agent().prompted_classify(
            question=make_prompt(paragraph, question),
            choices=(" Yes", " No"),
        )
        return choice_prob if choice == " Yes" else 1 - choice_prob

    async def execute(self, **kw):
        paper = kw['paper']
        paragraph = paper.paragraphs[0]
        question = kw.get("question", "What was the study population?")
        return await self.classify_paragraph(paragraph, question)
```

Save it to `paperqa.py` and run it on a paper:

```
./scripts/run-recipe.sh -r paperqa.py -t -i papers/keenan-2018.pdf
```

You should see a result like this:

```py
0.024985359096987403
```

According to the model, the first paragraph is unlikely to answer the question.

#### Classifying all paragraphs in parallel with `map_async`

To find the most relevant paragraphs, we map the paragraph classifier over all paragraphs and get the most likely ones.

For mapping, we use the utility `map_async` which runs the language model calls in parallel:

```py
from ice.recipe import Recipe
from ice.paper import Paragraph
from ice.utils import map_async

def make_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""

class PaperQA(Recipe):

    async def classify_paragraph(self, paragraph: Paragraph, question: str) -> float:
        choice, choice_prob, _ = await self.agent().prompted_classify(
            question=make_prompt(paragraph, question),
            choices=(" Yes", " No"),
        )
        return choice_prob if choice == " Yes" else 1 - choice_prob

    async def execute(self, **kw):
        paper = kw['paper']
        paragraph = paper.paragraphs[0]
        question = kw.get("question", "What was the study population?")
        probs = await map_async(paper.paragraphs, lambda par: self.classify_paragraph(par, question))
        return probs
```

If you run the same command as above, you will now see a list of probabilities, one for each paragraph:

```
[
    0.024381454349145293,
    0.24823367447526778,
    0.21119208211186247,
    0.07488850139282821,
    0.16529937276656714,
    0.46596912974665494,
    0.09871877171479271,
    ...
    0.06523843237521842,
    0.041946178310281246,
    0.03264635093381785,
    0.023112249840077093,
    0.0018325902029144858,
    0.15962813987814772
]
```

Now all we need to do is add a utility function for looking up the paragraphs with the highest probabilities:

```py
from ice.recipe import Recipe
from ice.paper import Paper, Paragraph
from ice.utils import map_async


def make_classification_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""


class PaperQA(Recipe):
    async def classify_paragraph(self, paragraph: Paragraph, question: str) -> float:
        choice, choice_prob, _ = await self.agent().prompted_classify(
            question=make_classification_prompt(paragraph, question),
            choices=(" Yes", " No"),
        )
        return choice_prob if choice == " Yes" else 1 - choice_prob

    async def execute(
        self, paper: Paper, question: str, top_n: int = 3
    ) -> list[Paragraph]:
        probs = await map_async(
            paper.paragraphs, lambda par: self.classify_paragraph(par, question)
        )
        sorted_pairs = sorted(
            zip(paper.paragraphs, probs), key=lambda x: x[1], reverse=True
        )
        return [par for par, prob in sorted_pairs[:top_n]]
```

Running the same command again...

```
./scripts/run-recipe.sh -r paperqa.py -t -i papers/keenan-2018.pdf
```

...we indeed get paragraphs that answer the question who the study population was!

```py
[
    Paragraph(sentences=['A total of 1624 communities were eligible for inclusion in the trial on the basis of the most recent census (Fig. 1 ).', 'A random selection of 1533 communities were included in the current trial, and the remaining 91 were enrolled in smaller parallel trials at each site, in which additional microbiologic, anthropometric, and adverse-event data were collected.', 'In Niger, 1 community declined to participate and 20 were excluded because of census inaccuracies.', 'No randomization units were lost to follow-up after the initial census.'], sections=[Section(title='Participating Communities', number=None)], section_type='main'),
    ...
]
```


### Answering the question given the top paragraphs with subrecipes

Now all we have to do is combine the paragraph finder with the question-answering recipe we built earlier on.

We could just paste in the code from the other recipe. However, we can also *directly* reuse it as a subrecipe. If you have the code in `qa.py`, we can directly import and use it:

```py
from ice.recipe import Recipe
from ice.paper import Paper, Paragraph
from ice.utils import map_async
from qa import QA


def make_classification_prompt(paragraph: Paragraph, question: str) -> str:
    return f"""Here is a paragraph from a research paper: "{paragraph}"

Question: Does this paragraph answer the question '{question}'? Say Yes or No.
Answer:"""


class PaperQA(Recipe):
    async def classify_paragraph(self, paragraph: Paragraph, question: str) -> float:
        choice, choice_prob, _ = await self.agent().prompted_classify(
            question=make_classification_prompt(paragraph, question),
            choices=(" Yes", " No"),
        )
        return choice_prob if choice == " Yes" else 1 - choice_prob

    async def get_relevant_paragraphs(
        self, paper: Paper, question: str, top_n: int = 3
    ) -> list[Paragraph]:
        probs = await map_async(
            paper.paragraphs, lambda par: self.classify_paragraph(par, question)
        )
        sorted_pairs = sorted(
            zip(paper.paragraphs, probs), key=lambda x: x[1], reverse=True
        )
        return [par for par, prob in sorted_pairs[:top_n]]

    async def execute(
        self, paper: Paper, question: str = "What was the study population?"
    ):
        relevant_paragraphs = await self.get_relevant_paragraphs(paper, question)
        relevant_str = "\n\n".join(str(p) for p in relevant_paragraphs)
        answer = await QA().execute(context=relevant_str, question=question)
        return answer
```

If you run it with the same command as above, you should get an answer like this:

```
The study population was children 1 to 59 months of age who weighed at least 38
```

Take a look at the trace to see how it all fits together.


### Exercises

1. We're taking a fixed number of paragraphs (3) and sticking them into the prompt. This will sometimes result in prompt space not being used well, and sometimes it will overflow. Modify the recipe to use as many paragraphs as can fit into the prompt. (Hint: A prompt for current models has space for 2048 tokens. A token is about 3.5 characters.)
2. We're classifying paragraphs individually, but it could be better to do ranking by showing the model pairs of paragraphs and ask it which better answers the question. Implement this as an alternative.
3. (Advanced) Implement debate with agents that have access to the same paper, and let agents provide quotes from the paper that can't be faked. Does being able to refer to ground truth quotes favor truth in debate?


## Future tutorial topics

- Other recipe components we've written, e.g. paragraph ranking
- Amplification
- Agent methods: Relevance etc
- Agent combinators
  - Machine agent with human spot checking
- Better agents: OpenAIReasoning
  - Chain-of-thought + plurality voting
- Special-purpose models & model hints
- Filters & verifiers
- Selection-Inference
- Other structures from Cascades, Prompt Chainer, and Maeutic prompting paper
- Unfold/fold structure
