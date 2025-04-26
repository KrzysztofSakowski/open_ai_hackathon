from __future__ import annotations

import asyncio
from pydantic import BaseModel
from api import AudioMessageToUser, CONVO_DB
from models import Address, PersonEntry, Knowledge, ConvoInfo

from settings import env_settings

from agents import (
    Agent,
    ItemHelpers,
    Runner,
    TResponseInputItem,
    function_tool,
    RunContextWrapper,
)


class FollowUpQuestion(BaseModel):
    follow_up: str | None


follow_up_question_generator = Agent(
    name="question_generator",
    instructions=(
        """
        Gather detailed information about a parent and a child to generate personalized stories for a child, ensuring a complete data set without gaps.

Ask one question at a time to obtain information on likes, dislikes, age, and address for both the parent and child. Keep questions focused: separate personal details from interests. Single-child context.

# Steps

1. **Parent Information**: Request details such as likes, dislikes, age, city, and country. Avoid combining interests with personal data in a single question.
2. **Child Information**: Obtain similar details—likes, dislikes, age, city, and country—for the child.

# Output Format

Each question should address one specific data point. If no further questions are necessary, output an empty structure.

- **Example Question**: "What are the parent's likes?"
- **City and Country Question**: Specifically ask, "What is the city and country where the parent/child lives?" Avoid requesting the full street address.

# Examples

**Example Interaction:**

- Prompt: "What is the parent's age?"
- Follow-up: "What is the parent's city and country of residence?"

**Example Completion for Initial Data Gathering:**

- Question 1: "What are the child's likes?"
- Question 2: "What are the parent's dislikes?"

# Notes

- Ensure all relevant fields are eventually covered without redundancy.
- Do not include full addresses, only city and country.
- Tailor questions to maintain engagement and clarity for story generation purposes.
- Only ask for additional information if a data gap exists.
        """
    ),
    output_type=FollowUpQuestion,
)

initial_knowledge_builder = Agent(
    name="initial_knowledge_builder",
    instructions="""
    Create an initial knowledge base using the description provided, which may involve a parent and a child. Ensure that the knowledge base is structured in a way that effectively captures the relevant details about the individuals mentioned.

# Steps

1. **Identification**: Identify the key elements within the description that relate to the parent and child, such as names, ages, relationships, traits, and any important events or characteristics mentioned.
2. **Organization**: Structure the information systematically, categorizing details under headings like "Individual Details," "Relationships," "Characteristics," and "Events."
3. **Detailing**: Ensure each category contains concise and relevant information extracted from the description.

# Output Format

Provide the knowledge base in a structured, readable format. It should include sections with clear headings for each identified category, and the details should be listed in bullet points or short sentences.

# Examples

**Example Input:**

"A mother named Sarah who is a doctor and is 35 years old has a 5-year-old daughter named Lily who loves painting."

**Example Knowledge Base:**

- **Individual Details**
  - **Parent**: Name: Sarah, Profession: Doctor, Age: 35 years
  - **Child**: Name: Lily, Age: 5 years

- **Relationships**
  - Sarah is Lily's mother

- **Characteristics**
  - Lily enjoys painting

# Notes

- Ensure all relevant information is captured and no important details from the description are overlooked.
- Maintain clarity and readability in the presentation of the knowledge base.
    """,
    output_type=Knowledge,
)

knowledge_updater = Agent(
    name="knowledge_updater",
    instructions="""
    Update the state based on a given question, current state, and provided answer.

Take inputs on the current state and integrate the new information from the question and corresponding answer to modify and update the state appropriately.

# Steps

1. **Understand the Inputs**: Identify the components of the question, current state, and answer, ensuring you understand their context and relationship.
2. **Identify Changes**: Determine what aspects of the current state are affected by the new information contained in the question and answer.
3. **Update the State**: Adjust the current state accordingly. Use reasoning to determine how exactly the state should change based on the given information.
4. **Verify Consistency**: Ensure that the updated state remains coherent and consistent with all available information.

# Output Format

The output should be a clear and concise description of the updated state, formatted as a paragraph.

# Examples

**Example 1**
- **Current State**: "The project deadline is set for September 30th."
- **Question**: "Has the project deadline been moved?"
- **Answer**: "Yes, it has been extended to October 15th."

**New State**: "The project deadline is now set for October 15th."

**Example 2**
- **Current State**: "The temperature is currently 25 degrees Celsius."
- **Question**: "Will the temperature increase today?"
- **Answer**: "Yes, it is expected to rise by 5 degrees."

**New State**: "The temperature today is expected to increase to 30 degrees Celsius."

# Notes

- Ensure the updated state reflects all relevant and recent information provided.
- Consider implications of changes and confirm that they align logically with the existing state and new data.
    """,
    output_type=Knowledge,
)


@function_tool
async def onboard_user(wrapper: RunContextWrapper[ConvoInfo]) -> Knowledge:
    if env_settings.preset_knowledge:
        return Knowledge(
            address=Address(
                country="Poland",
                city="Warsaw",
            ),
            parent=PersonEntry(
                name="Helena",
                age=40,
                likes=["Kopernik", "physics", "museums"],
                dislikes=["spiders", "ants", "bats"],
            ),
            child=PersonEntry(
                name="Mark",
                age=10,
                likes=["Kopernik", "physics", "museums"],
                dislikes=["sports"],
            ),
            theme="Mark wants to visit Kopernik center in Warsaw with his trusty turtle.",
        )

    # Add imports locally
    from api import wait_for_user_message, post_message

    # if wrapper.context.existing_convo:
    #     return CONVO_DB[wrapper.context.convo_id].knowledge

    if not env_settings.run_in_cli:
        post_message(
            wrapper.context.convo_id,
            AudioMessageToUser(audio_message="Tell me something about yourselves."),
        )
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

        post_message(
            wrapper.context.convo_id,
            AudioMessageToUser(audio_message=structured.follow_up),
        )
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

    CONVO_DB[wrapper.context.convo_id].knowledge = current_knowledge
    from api import add_to_output

    add_to_output(
        wrapper.context.convo_id,
        "knowledge",
        current_knowledge.model_dump_json(),
    )
    return current_knowledge


if __name__ == "__main__":
    asyncio.run(onboard_user())
