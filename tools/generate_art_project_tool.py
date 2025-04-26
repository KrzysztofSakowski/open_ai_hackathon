import asyncio

from agents import Agent, Runner

art_project_generator_agent = Agent(
    name="art_project_generator_agent",
    instructions="""
    You are responsible for generating an art project based on a provided user provided theme.
    It also ensures the project is age-appropriate.
    Provide a list of materials needed for the project.
    """,
    output_type=str,
    input_guardrails=[],
)


async def get_art_project(context: dict, theme: str):
    story_result = await Runner.run(
        art_project_generator_agent,
        input=f"Generate an art project for a child with age={context['age']} on a following theme={theme}",
    )
    return story_result.final_output


if __name__ == "__main__":

    async def test_get_art_project():
        theme = "space"
        context = {"age": 5}
        art_project = await get_art_project(context, theme)
        print(art_project)

    asyncio.run(test_get_art_project())
