from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pydantic import BaseModel
from api import post_message, wait_for_user_message

from agents import (
    Agent,
    ItemHelpers,
    Runner,
    TResponseInputItem,
    function_tool,
    RunContextWrapper,
)


class ConvoInfo(BaseModel):
    convo_id: str


class Address(BaseModel):
    country: str | None
    city: str | None


class PersonEntry(BaseModel):
    name: str | None
    age: int | None
    likes: list[str]
    dislikes: list[str]


class Knowledge(BaseModel):
    address: Address | None = None
    parent: PersonEntry | None = None
    child: PersonEntry | None = None
    theme: str | None = None


class FollowUpQuestion(BaseModel):
    follow_up: str | None


follow_up_question_generator = Agent(
    name="question_generator",
    instructions=(
        "You want to generate a good initial state for generating stories for a child. We need information about both parent and a child. "
        "For each person, we need some information about likes, dislikes, age. We do not want to have "
        "any holes in the structure, so make sure every field is there, including address, parent information and child information. Ask only one question at once. Do not mix personal details with interests - ask separate questions for them. "
        "There is single child. If you have no follow up question return nothing in the structure. When you ask for address, be specific that you are interested only in city and country, without specific address."
    ),
    output_type=FollowUpQuestion,
)

initial_knowledge_builder = Agent(
    name="initial_knowledge_builder",
    instructions=("Based on description, possibly of a parent and a child, create a initial knowledge base."),
    output_type=Knowledge,
)

knowledge_updater = Agent(
    name="knowledge_updater",
    instructions=("Based on a question, current state, question and answer update the state."),
    output_type=Knowledge,
)


@function_tool
async def onboard_user(wrapper: RunContextWrapper[ConvoInfo]) -> Knowledge:
    print("Tell me something about yourselves:")
    initial_description = await wait_for_user_message(wrapper.context.convo_id)
    # Ensure initial_description is not None
    if initial_description is None:
        print("Warning: Received None for initial_description. Defaulting to empty string.")
        initial_description = ""
    print("initial_description: ", initial_description)
    initial_result = await Runner.run(
        initial_knowledge_builder,
        [{"content": initial_description, "role": "system"}],
    )
    current_knowledge = Knowledge.model_validate_json(ItemHelpers.text_message_outputs(initial_result.new_items))
    print("initial: ", current_knowledge)

    while True:
        input_items: list[TResponseInputItem] = [
            {
                "content": "Current state is: " + current_knowledge.model_dump_json(),
                "role": "system",
            }
        ]

        story_outline_result = await Runner.run(
            follow_up_question_generator,
            input_items,
        )

        latest_outline = ItemHelpers.text_message_outputs(story_outline_result.new_items)

        structured = FollowUpQuestion.model_validate_json(latest_outline)
        print(structured)

        if structured.follow_up is None or structured.follow_up == "":
            break

        post_message(wrapper.context.convo_id, structured.follow_up)
        answer = await wait_for_user_message(wrapper.context.convo_id)
        # Ensure answer is not None
        if answer is None:
            print("Warning: Received None for answer. Defaulting to empty string.")
            answer = ""
        print("answer: ", answer)

        updater_input_items: list[TResponseInputItem] = [
            {
                "content": "Current state is: " + current_knowledge.model_dump_json(),
                "role": "system",
            },
            {"content": "Question is: " + structured.follow_up, "role": "system"},
            {"content": "Answer to a question is: " + answer, "role": "user"},
        ]

        updated_result = await Runner.run(
            knowledge_updater,
            updater_input_items,
        )

        current_knowledge = Knowledge.model_validate_json(ItemHelpers.text_message_outputs(updated_result.new_items))
        print(current_knowledge)

    return current_knowledge


if __name__ == "__main__":
    asyncio.run(onboard_user())
