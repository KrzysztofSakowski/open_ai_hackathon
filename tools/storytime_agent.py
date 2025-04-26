import asyncio
import json
from pathlib import Path

from pydantic import BaseModel

from agents import (
    Agent,
    Runner,
    function_tool,
    input_guardrail,
    RunContextWrapper,
    TResponseInputItem,
    GuardrailFunctionOutput,
)
from tools.onboarding_agent import Knowledge, PersonEntry, Address
from models import StoryContinuationOutput, InteractiveTurnOutput
from api import post_message
from models import ConvoInfo
from tools.storyboard_agent import _get_storyboard
from images import _generate_image_from_storyboard
from audio import generate_audio_from_storyboard
from video import generate_videos


class ViolentStoryOutput(BaseModel):
    reasoning: str
    is_violent_story: bool


guardrail_agent = Agent(
    name="Guardrail check",
    instructions="""
    Determine if the user's request involves generating a violent story.

# Steps

1. **Identify Story Elements**: Break down the user's request to understand the core elements of the story they are asking for.
2. **Keyword Analysis**: Look for keywords or phrases commonly associated with violence (e.g., fight, war, murder, attack).
3. **Context Evaluation**: Assess the context to verify if the violence is a primary theme or merely referenced.
4. **Intent Recognition**: Determine whether the user's intention is to create a narrative focusing on violent acts or scenes.

# Output Format

- Respond with "Yes" if the request involves generating a violent story.
- Respond with "No" if the request does not involve generating a violent story.

# Examples

**Example 1**
*Input*: "Write a story about an epic battle where the hero fights to save their kingdom."
*Analysis*: Contains keywords like "battle," "fights," and suggests violence is a major component.
*Output*: "Yes"

**Example 2**
*Input*: "Tell a story about a peaceful village life and the bonds between the residents."
*Analysis*: No significant violent elements present.
*Output*: "No"

# Notes

- Consider the overall theme and not just isolated words that might suggest violence.
- Handle ambiguous cases with contextual judgment based on common narrative themes.
    """,
    output_type=ViolentStoryOutput,
)


@input_guardrail
async def violent_story_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """This is an input guardrail function, which happens to call an agent to check if the input
    is a violent story request.
    """
    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(ViolentStoryOutput)

    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=final_output.is_violent_story,
    )


story_agent = Agent(
    name="story_agent",
    instructions="""
    Write a captivating short story based on the given outline. Ensure that the narrative follows the structure outlined, incorporating the characters, setting, and key events provided.

# Steps

1. **Understand the Outline**: Carefully read the given outline, identifying the main plot points, characters, setting, and any specific themes or tones required.
2. **Develop Characters**: Flesh out the characters, giving them distinct voices and traits that contribute to the plot development.
3. **Establish Setting**: Clearly describe the setting, utilizing sensory details to create an immersive environment.
4. **Build the Narrative**: Follow the outline to construct the story, weaving together the characters, setting, and events in a coherent and engaging way.
5. **Resolve the Plot**: Ensure the story reaches a satisfying conclusion that aligns with the initial outline.

# Output Format

Write a short story of approximately 500-1000 words. The story should be in prose form, with paragraphs structured to reflect logical breaks in action or narrative development.

# Examples

Example Outline:
- **Characters**: Alex (a young scientist), Mia (Alex's best friend)
- **Setting**: A futuristic cityscape
- **Plot Points**: Alex discovers a method for time travel but needs Mia's help. They test the method and find themselves in a past era, learning key lessons before returning.
- **Themes**: Friendship, curiosity, and the consequence of actions

**Short Story Example Start**:

In the dazzling glow of the neon-lit metropolis, Alex wandered through the labyrinthine alleys of the city. A young scientist with an insatiable thirst for discovery, Alex rarely ventured beyond their lab except to see Mia. Today was different. Today, Alex had stumbled upon something extraordinary—a formula scribbled hastily on the whiteboard held the secret to traversing time itself.

(Continue the story based on the outline, ensuring it meets the required word count and contains a coherent narrative with character development, setting description, plot progression, and conclusion.)

# Notes

- Pay special attention to how the theme is integrated into the narrative.
- Ensure consistency in tone and style as indicated by the outline.
- Be creative while adhering to the given structure and elements.
    """,
    output_type=str,
    input_guardrails=[violent_story_guardrail],
)


storytime_agent = Agent(
    name="storytime_agent",
    instructions="""
    Create a children’s story based on the user's input, focusing on imaginative scenarios and engaging characters suitable for young readers.

# Criteria for a Successful Children's Story
- Engaging storyline with a clear beginning, middle, and end.
- Simple language appropriate for the age group (e.g., ages 4-8).
- Positive moral or lesson, unless specified otherwise by the user.
- Characters that children can relate to or learn from.
- Creative and descriptive illustrations or scenes.

# Steps
1. Understand the user input and identify key elements to include in the story such as themes, characters, or settings.
2. Develop a simple plot with a problem or challenge for the main character(s) to overcome.
3. Introduce imaginative elements to capture a child's interest.
4. Conclude with a resolution that includes a positive lesson or happy ending.
5. Ensure the language is engaging and age-appropriate throughout.

# Output Format
The completed story should be one to two paragraphs long and suited for children's comprehension and interest levels.

# Examples

**Example 1:**
**Input:** A story about a brave little mouse in a big city.
**Output:**
Once upon a time, in the heart of a bustling city, there lived a brave little mouse named Max. Despite his small size, Max was known for his mighty courage. One day, Max decided to explore the world beyond his cozy home under the old clock tower. As he scurried through the city streets, he encountered towering buildings, busy people, and noisy cars. Max found himself in an adventure when he stumbled upon an alley where a group of mice were trying to find shelter from a sudden rainstorm. Thinking quickly, Max led the mice to the safety of a nearby bakery, where they all shared crumbs and stories. Max realized that being brave isn’t about being fearless, but about helping friends in need. And from that day forward, Max was known as the hero of the city mice.

# Notes
- Consider incorporating whimsical elements such as talking animals or magical places if fitting for the input.
- Feel free to use repetition, rhymes, or rhythm to enhance storytelling and engagement.
    """,
)


class StoryOutput(BaseModel):
    story: str
    theme: str


@function_tool
async def get_story(wrapper: RunContextWrapper[ConvoInfo], knowledge: Knowledge, theme: str) -> StoryOutput:
    return await _get_story(wrapper, knowledge, theme)


async def _get_story(wrapper: RunContextWrapper[ConvoInfo], knowledge: Knowledge, theme: str) -> StoryOutput:
    input_prompt = f"""
    Here is some helpful data: {knowledge.model_dump_json()}.
    You can name characters like parent and child, and use the theme as a base for the story.
    You can locate the story in the address provided.

    But DO NOT use make humans the main characters of the story.
    The story should be a short children's story, with a clear beginning, middle, and end.
    The story should be engaging and suitable for children, with a positive message or moral.
    The story should be no more than 500 words long.
    The story should be written in a simple and clear language, with short sentences and paragraphs.
    The story should be imaginative and creative, with interesting characters and settings.
    The story should be appropriate for the age group of the child.

    Remember: Generate a story with the theme: {theme}.
"""

    print("Generating story outline...")
    # Ensure the entire workflow is a single trace
    # 1. Generate an outline
    outline_result = await Runner.run(
        story_outline_agent,
        input_prompt,
    )
    print("Outline generated")
    # 4. Write the story
    story_result = await Runner.run(
        story_agent,
        outline_result.final_output,
    )
    print(f"Story: {story_result.final_output}")

    storyboard_output = await _get_storyboard(wrapper, story_result.final_output)
    print("Storyboard generated: " + storyboard_output.model_dump_json())

    print("Generating audio...")
    audio_output = await generate_audio_from_storyboard(storyboard_output)

    print("Generating images...")
    images_output = await _generate_image_from_storyboard(
        storyboard_output,
    )

    print("Generating video...")
    video_output = []
    try:
        video_output = await generate_videos([Path(p) for p in images_output.image_paths])
    except Exception as e:
        print(f"Error generating video: {e}")
    print(images_output)
    print(audio_output)
    print(video_output)

    from api import add_to_output

    add_to_output(
        wrapper.context.convo_id,
        "story_images",
        images_output.model_dump(),
    )
    add_to_output(
        wrapper.context.convo_id,
        "story_audio",
        audio_output,
    )
    add_to_output(
        wrapper.context.convo_id,
        "story_video",
        video_output,
    )

    return StoryOutput(
        story=story_result.final_output,
        theme=theme,
    )


story_outline_agent = Agent(
    name="story_outline_agent",
    instructions="""
    Create a short outline for a children's story based on the user's input. The outline should capture the main idea, characters, setting, and key plot points, ensuring it is tailored to the themes or elements specified by the user.

# Steps

1. **Understand the User Input**: Identify key elements such as theme, characters, setting, or any specific prompts provided by the user.
2. **Develop Characters**: Create engaging and relatable characters suitable for a children’s story.
3. **Establish Setting**: Define a vivid and appealing setting that will captivate young readers.
4. **Outline Plot**: Develop a simple yet intriguing plot with a clear beginning, middle, and end. Include a lesson or moral if relevant.
5. **Ensure Suitability**: Ensure the outline is age-appropriate and engaging for children.

# Output Format

- **Title**: A catchy and suitable title for a children's story.
- **Main Idea**: A one-sentence summary of the story.
- **Characters**: List of main characters with brief descriptions.
- **Setting**: Description of where and when the story takes place.
- **Plot Points**: Key events in the story, such as the beginning, middle, and end, in bullet points.

# Examples

**User Input**: A story about a brave little rabbit in a magical forest.

**Output**:

- **Title**: "Brave Bunny in the Enchanted Woods"
- **Main Idea**: A curious little rabbit discovers courage in the magical forest when faced with a challenge.
- **Characters**:
  - Benny the Rabbit: A curious and brave little bunny.
  - Willow the Wise Owl: A helpful guide in the forest.
- **Setting**: A lush, whimsical forest filled with magical creatures.
- **Plot Points**:
  - Benny ventures into the magical forest despite being scared.
  - He encounters various friendly and magical creatures along the way.
  - With the encouragement of Willow the Wise Owl, Benny overcomes a challenge and returns home braver than before.

(Real examples should fully integrate the specific theme and elements provided by the user.)
    """,
)

# --- Interactive Story Components ---
story_continuation_agent = Agent(
    name="story_continuation_agent",
    instructions="""
You are an interactive storyteller for children.
Given the story so far and the user's chosen path (or an initial topic), generate the next short scene (1-2 paragraphs) of the story.
Then, provide two distinct and engaging options for how the story could continue next.

Input will be structured as:
- Topic: [Initial topic if starting]
- Story History: [The story generated so far]
- Chosen Path: [The option chosen by the user in the previous step, or 'Start' if beginning]

Output should be the next scene and two new options.
Keep the tone light, engaging, and appropriate for children.
""",
    output_type=StoryContinuationOutput,
    input_guardrails=[violent_story_guardrail],  # Reuse the violence check
)

# --- New Interactive Story + Illustrator Agent ---

from tools.storyboard_agent import get_storyboard
from images import generate_image_from_storyboard

interactive_story_illustrator_agent = Agent(
    name="interactive_story_illustrator_agent",
    instructions="""
You are an interactive storyteller and illustrator for children, tasked with performing one turn of an interactive story.

Your task involves:
1. **Generating the Next Story Scene and Continuation Options:** Use the provided story history and the user's chosen path or initial topic to create the next scene and two continuation options. Employ the 'story_continuation_agent' tool for this.
2. **Creating a Storyboard:** Develop a storyboard based on the newly generated scene text. Use the 'get_storyboard' tool.
3. **Generating Images:** Produce images derived from the storyboard using the 'generate_image_from_storyboard' tool.
4. **Delivering Results:** Present the newly generated scene text, paths to the generated images, and continuation options.

Input format expected:
- **Story History:** [Text of the story generated so far]
- **Chosen Path:** [The option chosen by the user in the previous step, or the initial 'Topic: <topic>' if starting]

# Steps

1. **Generate Scene and Options:**
   - Use the 'story_continuation_agent' tool with supplied inputs.
   - Ensure the scene is creative and suitable for children, keeping the tone light and engaging.
2. **Create a Storyboard:**
   - Base this entirely on the new scene text.
   - Utilize the 'get_storyboard' tool to complete this step.
3. **Generate Images:**
   - Use the 'generate_image_from_storyboard' tool based on the storyboard.
4. **Compile and Return Output:**
   - Format the response with scene text, image paths, and continuation options.

# Output Format

Show results in the InteractiveTurnOutput format:
- **Scene Text:** Provide the text of the newly generated scene.
- **Image Paths:** Include the paths to the generated images.
- **Continuation Options:** Present two options for continuing the story, allowing users to choose the next path.

# Examples

**Example Input:**
- Story History: "Once upon a time, a little dragon named Oliver visited the magical forest."
- Chosen Path: "Oliver decides to explore the shimmering river."

**Example Output:**
- Scene Text: "Oliver tiptoed to the river's edge, mesmerized by the sparkling water that danced in the sunlight. Suddenly, a friendly fish poked its head out, eager to chat."
- Image Paths: ["/images/scene_dragon_river.jpg", "/images/scene_fish.jpg"]
- Continuation Options: ["Oliver asks the fish about the river's secret.", "A butterfly invites Oliver to follow it into the enchanted woods."]

# Notes

- Ensure scenes are suitable for young audiences.
- Maintain a consistent, engaging tone.
- Each turn should offer potential paths for narrative development.
- Consider visual interest in storyboard development to enhance the storytelling experience.
""",
    output_type=InteractiveTurnOutput,
    tools=[
        story_continuation_agent.as_tool(
            tool_name="story_continuation_agent",
            tool_description="Generates the next story scene and two options based on history and choice.",
        ),
        get_storyboard,
        generate_image_from_storyboard,
    ],
    input_guardrails=[violent_story_guardrail],
)


# --- End Interactive Story Components ---


class Context(BaseModel):
    context: ConvoInfo


if __name__ == "__main__":
    from api import CONVO_DB, Conversation, Knowledge, Address, PersonEntry

    CONVO_ID = "test_convo_id"
    CONVO_DB[CONVO_ID] = Conversation(
        messages_to_user=[],
        messages_to_agent=[],
        outputs=[],
        knowledge=Knowledge(
            address=Address(city="Warsaw", country="Poland"),
            parent=PersonEntry(
                name="John Doe",
                age=34,
                likes=["cheese", "running"],
                dislikes=["cats", "loud noises"],
            ),
            child=PersonEntry(
                name="Little Timmy",
                age=5,
                likes=["playing", "adventures"],
                dislikes=["bedtime", "vegetables"],
            ),
            theme="A brave little mouse",
        ),
        final_output={},
    )
    asyncio.run(
        _get_story(
            Context(context=ConvoInfo(convo_id="test_convo_id")),
            CONVO_DB[CONVO_ID].knowledge,
            "A brave little mouse",
        ),
    )
