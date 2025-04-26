import asyncio

from agents import Agent, Runner

art_project_generator_agent = Agent(
    name="art_project_generator_agent",
    instructions="""
    Generate an art project based on a provided theme, ensuring the project is age-appropriate. Include a list of materials needed for the project.

# Steps

1. **Understand the Theme**: Begin by analyzing the theme provided and consider how it can be translated into an art project.
2. **Determine Age Appropriateness**: Assess the age group the project is intended for, ensuring safety and engagement.
3. **Project Description**: Develop a brief description of the art project that aligns with the theme.
4. **Materials List**: Compile a detailed list of materials required to complete the project.

# Output Format

The output should be presented in the following format:
- **Project Description**: A short paragraph describing the art project.
- **Materials**: A bullet point list of materials needed.

# Examples

**Input**:
- Theme: "Under the Sea"
- Age Group: 6-8 years

**Output**:
- **Project Description**: Create a colorful underwater scene using paint and paper. Children will paint various sea creatures such as fish, turtles, and starfish and arrange them to form an ocean landscape.
- **Materials**:
  - Blue and green paint
  - Brushes
  - Construction paper (various colors)
  - Scissors
  - Glue
  - Markers or crayons

# Notes

- Ensure all materials listed are safe and suitable for the specified age group.
- Consider the availability and cost of materials.
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
