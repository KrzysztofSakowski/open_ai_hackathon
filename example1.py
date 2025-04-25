
import asyncio
import os

from agents import (
    Agent,
    FileSearchTool,
    Runner,
    WebSearchTool,
    function_tool,
    set_default_openai_key,
    trace,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from openai import OpenAI

set_default_openai_key(os.getenv("OPENAI_API_KEY"))


#define web search agent that uses the WebSearchTool provided by the Responses API to find real-time information on the user's query


# --- Agent: Search Agent ---
def define_search_agent():
    search_agent = Agent(
        name="SearchAgent",
        instructions=(
            "You immediately provide an input to the WebSearchTool to find up-to-date information on the user's query."
        ),
        tools=[WebSearchTool()],
    )
    return search_agent

# --------------------------------------------------------------------------------------
#The second agent needs to be able to answer questions on our product portfolio. To do this, we'll use the FileSearchTool to retrieve information from a vector store managed by OpenAI containing our company specific product information.



def upload_file(file_path: str, vector_store_id: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    file_name = os.path.basename(file_path)
    try:
        file_response = client.files.create(file=open(file_path, 'rb'), purpose="assistants")
        attach_response = client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_response.id
        )
        return {"file": file_name, "status": "success"}
    except Exception as e:
        print(f"Error with {file_name}: {str(e)}")
        return {"file": file_name, "status": "failed", "error": str(e)}

def create_vector_store(store_name: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        vector_store = client.vector_stores.create(name=store_name)
        details = {
            "id": vector_store.id,
            "name": vector_store.name,
            "created_at": vector_store.created_at,
            "file_count": vector_store.file_counts.completed
        }
        print("Vector store created:", details)
        return details
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return {}

def upload_file_to_vector_store():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    vector_store_id = create_vector_store("ACME Shop Product Knowledge Base")
    upload_file("voice_agents_knowledge/acme_product_catalogue.pdf", vector_store_id["id"])
    


# --------------------------------------------------------------------------------------

# --- Agent: Knowledge Agent ---
def define_knowledge_agent():
    knowledge_agent = Agent(
        name="KnowledgeAgent",
        instructions=(
            "You answer user questions on our product portfolio with concise, helpful responses using the FileSearchTool."
        ),
        tools=[FileSearchTool(
                max_num_results=3,
                vector_store_ids=["vs_68062b4dddd88191af60cb32448a2ce7"], # Replace with your vector store ID
            ),],
    )
    return knowledge_agent


# --- Tool 1: Fetch account information (dummy) ---
@function_tool
def get_account_info(user_id: str) -> dict:
    """Return dummy account info for a given user."""
    return {
        "user_id": user_id,
        "name": "Bugs Bunny",
        "account_balance": "£72.50",
        "membership_status": "Gold Executive"
    }


# --- Agent: Account Agent ---
def define_account_agent():
    account_agent = Agent(
        name="AccountAgent",
        instructions=(
            "You provide account information based on a user ID using the get_account_info tool."
        ),
        tools=[get_account_info],
    )
    return account_agent



# --------------------------------------------------------------------------------------
# The triage agent that will route the user's query to the appropriate agent based on their intent. Here we're using the prompt_with_handoff_instructions function, which provides additional guidance

# --- Agent: Triage Agent ---
def define_triage_agent(account_agent, knowledge_agent, search_agent):
    triage_agent = Agent(
        name="Assistant",
        instructions=prompt_with_handoff_instructions("""
    You are the virtual assistant for Acme Shop. Welcome the user and ask how you can help.
    Based on the user's intent, route to:
    - AccountAgent for account-related queries
    - KnowledgeAgent for product FAQs
    - SearchAgent for anything requiring real-time web search
    """),
        handoffs=[account_agent, knowledge_agent, search_agent],
    )
    return triage_agent


# --------------------------------------------------------------------------------------
# Run agent orchestration
async def main():
    #upload_file_to_vector_store()

    examples = [
        "What's my ACME account balance doc? My user ID is 1234567890", # Account Agent test
        "Ooh i've got money to spend! How big is the input and how fast is the output of the dynamite dispenser?", # Knowledge Agent test
        "Hmmm, what about duck hunting gear - what's trending right now?", # Search Agent test

    ]
    with trace("ACME App Assistant"):
        for query in examples:
            result = await Runner.run(define_triage_agent(define_account_agent(), define_knowledge_agent(), define_search_agent()), query)
            print(f"User: {query}")
            print(result.final_output)
            print("---")


if __name__ == "__main__":
    asyncio.run(main())
