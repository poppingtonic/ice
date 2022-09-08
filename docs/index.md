# Language model composition with ICE: A tutorial

In this tutorial we'll learn how to get language models to do complex tasks by composing together multiple calls.

We'll call programs that describe such compositions _recipes_.

## Contents

{:toc}

## Before we start

This tutorial requires that you've set up ICE as described in [the ICE README](https://github.com/oughtinc/ice9#interactive-composition-explorer-).

## The simplest recipe: Hello world!

Let's first get used to the infrastructure for writing, running, and debugging recipes:

Make a file `hello_world.py` in `ice/recipes/`:

```py
from ice.recipe import Recipe

class HelloWorld(Recipe):
    async def execute(self, **kw):
        return "Hello world!"
```

Run the recipe:

```sh
scripts/run-recipe.sh -r helloworld -t -b
```

This will run the recipe, creating an execution trace (`-t`) and showing it in a browser window (`-b`).

On the terminal, you should see this:

```
Hello world!
```

In your browser you should see a function node that you can click on, expand, and inspect inputs/outputs and source code.

Some things to note about the recipe:

- We're inhering from the `Recipe` class because that will give us automatic tracing of all async methods for debugging. (Synchronous methods are currently assumed to be simple and fast, and not worth tracing.)
- `execute` is the name of the method that is called when a recipe is run
- Most recipe methods, including `execute`, will be async so that language model calls are parallelized as much as possible.
- Different recipes take different arguments, which will be provided as keyword arguments captured by `**kw`. This recipe doesn't use any arguments--we're just accepting `**kw` to make the function type consistent.

### Exercises

1. Add another method to `HelloWorld` and call it from `execute`. Does it show up in the trace? What if you make it async and call it as `result = await self.my_function()`?

## Calling an agent: Q&A

Now let's make our first recipe that calls out to an agent.

```py
from ice.recipe import Recipe

def make_qa_prompt(question: str) -> str:
    return f"""
Question: {question}
Answer:""".strip()

class QA(Recipe):
    async def execute(self, question: str):
        prompt = make_qa_prompt(question)
        answer = await self.agent().answer(context="", question=question)  # FIXME: Use prompt arg
        return answer
```

We can run recipes in different modes, which controls what type of agent is used. Some examples:

- `machine`: Use an automated agent (usually GPT-3 if no hint is provided in the agent call). This is the default mode.
- `human`: Elicit answers from you using a command-line interface.
- `augmented`: Elicit answers from you, but providing the machine-generated answer as a default.

You specify the mode like this:

```sh
scripts/run-recipe.sh -r qa -t -b -m human
```

Try running your recipe in different modes.

Things to note:

- Because the agent's `answer` method is async, we have to use `await`

### Exercises

1. Instead of answering directly, add "Let's think step by step" as a prefix to the answer part of the prompt.

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
You are Bob. There are 5 turns left in the debate. You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.

Alice: "I think we should legalize all drugs.
You: "I'm against.
Alice: "The war on drugs has been a failure. It's time to try something new.
You: "
```

### The recipe

If you want to challenge yourself, pause and see if you can use the pieces above to write a recipe that has agents take turns at a debate about a question.

Once you're ready, or if you just want to see the result, take a look at this recipe:

```py
class DebateRecipe(Recipe):

    async def execute(self, **kw):
        question = kw.get("question", "Should we legalize all drugs?")
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
            context="", question=prompt, multiline=False, max_tokens=100
        )
        return debate + [(agent_name, answer.strip())]
```

Once you've saved the recipe in `debate.py` you can run it as usual:

```sh
scripts/run-recipe.sh -r debate -t -b
```

Some things to note:

- In `agents = [self.agent(), self.agent()]` we're creating two agents. This doesn't actually matter since all the agents we're using in ICE right now don't have implicit state (except for humans), so we could just have created agents on the fly in the `turn` function.

### Exercises

1. Add a judge agent at the end that decides which agent won the debate. In the original debate proposal, these judgments would be used to RL-finetune the parameters of the debate agents.

## Future topics

- Reasoning about external content: Papers
- Parts of recipes we've written
- Subrecipes: Amplification
- Agent methods: relevance etc
- Better agents: OpenAIReasoning
  - chain-of-thought + plurality voting
- Special-purpose models & model hints
- Filters & verifiers
- Selection-Inference
- Other structures from Cascades paper
