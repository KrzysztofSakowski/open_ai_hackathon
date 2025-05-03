"""
Interactive story generator.

This module implements an interactive story generator using the OpenAI API.
It allows users to engage in an interactive storytelling experience where they can choose different paths to continue the story.
"""

from typing import AsyncGenerator

from agents import Agent, Runner
from openai.types.responses import ResponseInputTextParam
from openai.types.responses.response_input_item_param import Message

from interactive_storytelling.guardrails import (
    prompt_hijack_guardrail,
    violent_story_input_guardrail,
    violent_story_output_guardrail,
    obscene_language_input_guardrail,
    obscene_language_output_guardrail,
    age_appropriateness_guardrail,
    input_length_guardrail,
)
from interactive_storytelling.models import (
    InteractiveTurnOutput,
    StorytellerContext,
)

# --- Agent Definition ---
interactive_story_agent = Agent(
    name="interactive_story_agent",
    instructions="""
        You are an interactive storyteller for children.
        Given the story so far and the user's chosen path (or an initial story context),
        generate the next short scene (3-5 paragraphs) of the story.
        This scene should be vivid, imaginative, and suitable for the age group specified in the context.
        Next, provide two distinct and engaging options for how the story could continue,
        ensuring they are intriguing and developmentally appropriate for the reader's age.

        # Steps
        1. **Understand the Story Context**: Review the story so far or initial context to maintain continuity and enhance narrative coherence.
        2. **Create the Next Scene**: Write a descriptive and immersive scene that captivates young readers, using language and themes that are engaging and suitable for the specified age group.
        3. **Develop Choices for Continuation**: Craft two clearly defined paths that the story could take, sparking curiosity and providing meaningful choices.

        # Output Format
        - **Next Scene**: 3-5 paragraphs, maintaining a consistent narrative tone suitable for children.
        - **Story Continuation Options**: Two bullet points, each presenting a potential path or decision point for the story to take.

        # Examples
        **Example 1**
        *Story Context*: In the magical forest, Lily the fairy found a strange talking mushroom that needed her help.
        *Next Scene*: Lily fluttered around the mushroom, her tiny wings shimmering in the dappled sunlight filtering through the leaves. "What sort of help do you need, dear mushroom?" she asked, her voice as gentle as the rustling leaves. The mushroom wobbled slightly, its eyes appearing earnest. "A pesky squirrel stole my cap, and now I can't grow any taller. Could you help me get it back?" "Of course!" exclaimed Lily. She loved helping her forest friends, and this sounded like quite the adventure. As they planned, bright sunlight glinted across the nearby stream, and Lily spotted some feathery leaves that might make a great new cap. But the forest was thick and full of curiosities, and she couldn't help wondering what else lay in store.
        **Options**:
        - Should Lily fly across the sparkling stream to follow the footprints she suspects might lead to the playful squirrel?
        - Or would it be better for her to explore an ancient tree hollow where she heard fascinating stories are whispered?

        **Example 2**
        *Story Context*: Toby the turtle discovered a hidden cave while playing on the beach.
        *Next Scene*: [...] (Should be longer in an actual story scene for coherence and depth)
        **Options**:
        - Should Toby venture deeper into the cave where he hears a curious echo?
        - Or should he return to the beach and share the finding with his friends, inviting them to explore together?

        # Notes
        - Be mindful of age-appropriate themes and language.
        - Ensure that each choice offers a unique storyline trajectory.
        - Maintain an element of fun, magic, or learning in both the scene and options.
    """,
    output_type=InteractiveTurnOutput,
    input_guardrails=[
        prompt_hijack_guardrail,
        violent_story_input_guardrail,
        obscene_language_input_guardrail,
        input_length_guardrail,
    ],
    output_guardrails=[
        age_appropriateness_guardrail,
        violent_story_output_guardrail,
        obscene_language_output_guardrail,
    ],
)


async def run_interactive_story(
    story_context: StorytellerContext,
) -> AsyncGenerator[InteractiveTurnOutput, str]:
    """Runs the interactive story agent, yielding each turn's output and accepting the user's choice."""
    story_input_so_far = [
        Message(
            role="system",
            content=[ResponseInputTextParam(text=story_context.get_prompt_content(), type="input_text")],
        ),
    ]

    while True:
        story_decision = await Runner.run(
            interactive_story_agent,
            story_input_so_far,
            context=story_context,
        )
        final_output: InteractiveTurnOutput = story_decision.final_output

        if final_output.decisions is None:
            yield final_output  # Yield the final scene without decisions
            break  # Story ends

        # Yield the current scene and decisions, wait for user choice
        user_choice = yield final_output

        # Prepare input (context) for the next turn
        story_input_so_far = story_decision.to_input_list() + [
            Message(role="user", content=[ResponseInputTextParam(text=user_choice, type="input_text")])
        ]
