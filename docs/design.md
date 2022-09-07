# Glossary

## Agent

A worker solving the task at a given **Node**. Could use a human, a machine, a combination, or an ensemble.

## Environment

A interface through which to gather information from humans.

**Agents** are able to use the **Environment** if they need input from humans, but the **Environment** can also be used outside of **Agents**, e.g. when selecting papers and a recipe.

## Recipe

Responsible for building a **DAG** of **Nodes**. This graph represents the sequence of steps we will ask **Agents** to complete to solve the overall problem.

## Node

A single task in an overall **DAG**. We'd expect that **Nodes** are human-interpretable as a unit of work – although practically-speaking they may need to be split into a collection of simpler **Nodes** to be tractable.

## DAG

The graph consisting of **Nodes** (tasks) and edges (dependencies) between them. A **Recipe** creates a **DAG** to solve a specific problem.
