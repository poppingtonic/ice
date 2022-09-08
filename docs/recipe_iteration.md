# Iterating on the Placebo recipe

## Tweaking the recipe

1. Start a new branch for work on your recipe iteration:

   ```
   $ git checkout -b andreas/placebo-iteration-v3
   ```

2. Run the recipe manually (with machine defaults) on the gold standard paragraphs until you disagree with a machine judgment in a way that seems fixable:

   ```
   $ ./scripts/eval-gold-paragraphs.sh -q placebo --recipe-name placebotree --random-seed 0 --method-name classify_paragraph_placebo
   ```

   Tips:

   1. When the recipe asks for user input, you can interrupt with Ctrl+C and the recipe will print out the current prompt and then stop. It's often useful to copy this prompt to the [OpenAI playground](https://beta.openai.com/playground?model=text-davinci-002) and iterate on it there.
   2. By controlling the random seed you can change the order in which the paragraphs are shown to you.

   3. This only works for methods such as `classify_paragraph_placebo` that have a signature `(self, paragraph: Paragraph, experiment: Experiment) -> Any`

3. Tweak the recipe `ice/recipes/placebo_tree.py` to make the machine judgment agree with your judgment.

4. Rerun the gold standard evaluation in step 1 to check if the recipe is now consistent with your judgment, and isn't worse on other gold standard paragraphs.

5. Repeat steps 1-3 a few times until you've substantially improved the recipe on the gold standard paragraphs.

6. Test the recipe on papers with iteration gold standards:

   ```
   $ ./scripts/run-recipe.sh -m machine -r placebotree -q placebo -g iterate -o log.txt
   ```

7. If the overall metrics are worse than the previous scores, continue iteration on 1-5. If the metrics are better, or if you want to record your state of work even though they're not, you can now submit your new recipe and evaluation.

## Submitting recipes

1. Commit all changes to the recipe and tag the commit with a new version number:

   ```
   $ git add ice/recipes/placebo_tree.py
   $ git commit -m "Added placebo iteration v3"
   $ git tag placebo-iteration-v3
   ```

2. Push the tag to the repository:

   ```
   $ git push
   $ git push origin placebo-iteration-v3
   ```

3. Create [a release](https://github.com/oughtinc/ice/releases) for this tag, pasting in the summary stats from the log file created in step 5 above. Append the log file as a binary.
