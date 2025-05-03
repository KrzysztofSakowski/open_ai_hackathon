from unittest.mock import MagicMock, patch

import pytest

from interactive_storytelling.agent import run_interactive_story
from interactive_storytelling.models import (
    InteractiveTurnOutput,
    InteractiveTurnDecisions,
    StorytellerContext,
    StoryMoral,
)


@patch("interactive_storytelling.agent.Runner.run")
@pytest.mark.asyncio
async def test_happy_path_full_e2e(mocked_agent_run: MagicMock) -> None:
    """
    Runs "happy path" e2e test with mocked user input and llm answers.
    """
    # Define mock responses
    mock_response_1 = MagicMock(
        final_output=InteractiveTurnOutput(
            scene_text="Scene 1", decisions=InteractiveTurnDecisions(option1="Option A", option2="Option B")
        )
    )
    mock_response_2 = MagicMock(
        final_output=InteractiveTurnOutput(
            scene_text="Scene 2 based on Option A",
            decisions=InteractiveTurnDecisions(option1="Option C", option2="Option D"),
        )
    )
    mock_response_3 = MagicMock(
        final_output=InteractiveTurnOutput(scene_text="Final scene based on Option C", decisions=None)  # End of story
    )

    # Configure the mock to return responses in sequence
    mocked_agent_run.side_effect = [
        mock_response_1,
        mock_response_2,
        mock_response_3,
    ]

    # Start the story
    topic = "a brave knight"
    story_generator = run_interactive_story(
        StorytellerContext(
            main_topic=topic,
            main_moral=StoryMoral(
                name="Friendship",
                description="Friendship and loyalty are priceless.",
            ),
            main_character="Nana, the Shiba dog",
            language="Polish",
            age=5,
        )
    )

    # First interaction
    output_1 = await story_generator.asend(None)
    assert output_1 == mock_response_1.final_output

    # Second interaction (simulate user choosing Option A, which is index 0)
    output_2 = await story_generator.asend("0")
    assert output_2 == mock_response_2.final_output

    # Third interaction (simulate user choosing Option C, which is index 0)
    output_3 = await story_generator.asend("0")
    assert output_3 == mock_response_3.final_output

    # Fourth interaction (simulate user choosing Option D, which is index 1)
    # This should lead to the final scene with decisions=None
    with pytest.raises(StopAsyncIteration):
        await story_generator.asend("1")

    assert mocked_agent_run.call_count == 3
