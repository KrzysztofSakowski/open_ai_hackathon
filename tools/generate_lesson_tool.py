import asyncio

from agents import Agent, Runner, WebSearchTool

lesson_generator_agent = Agent(
    name="lesson_agent",
    instructions="""
    This agent is responsible for generating a lesson plan based on the user's input.
    It takes into account the age of the child and the subject matter.
    It also ensures that the lesson is engaging and age-appropriate.
    It also includes interactive elements to enhance learning.
    Search the web for the latest information on the topic.
    """,
    output_type=str,
    input_guardrails=[],
    tools=[WebSearchTool()],
)


if __name__ == "__main__":

    async def test_lesson_generator_agent():
        lesson = await Runner.run(
            lesson_generator_agent,
            "Child is 5 years old, and the lesson is about the solar system.",
            context=None,
        )
        print(lesson)

    asyncio.run(test_lesson_generator_agent())
