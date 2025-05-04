import os
import asyncio
import base64
import settings

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")


async def check_moderation():
    """Checks filenames in the examples directory using OpenAI Moderation API."""
    client = settings.openai_client

    print(f"Checking filenames in: {EXAMPLES_DIR}\n")

    if not os.path.exists(EXAMPLES_DIR) or not os.path.isdir(EXAMPLES_DIR):
        print(f"Error: Directory not found: {EXAMPLES_DIR}")
        return

    filenames = [f for f in os.listdir(EXAMPLES_DIR) if os.path.isfile(os.path.join(EXAMPLES_DIR, f))]

    if not filenames:
        print("No files found in the examples directory.")
        return

    moderation_tasks = []
    for filename in filenames:
        with open(os.path.join(EXAMPLES_DIR, filename), "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")

        print(f"Checking: {filename}")
        # Create a task for each moderation call
        task = client.moderations.create(
            model="omni-moderation-latest",
            input=[{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64_image}}],
        )
        moderation_tasks.append(task)

    # Run all moderation checks concurrently
    results = await asyncio.gather(*moderation_tasks)

    print("\n--- Moderation Results ---")
    for filename, result in zip(filenames, results):
        print(f"\nInput Image: '{filename}'")
        if result.results:
            mod_result = result.results[0]
            print(f"  Flagged: {mod_result.flagged}")
            if mod_result.flagged:
                flagged_categories = {k: v for k, v in mod_result.categories.__dict__.items() if v}
                print(f"  Flagged Categories: {flagged_categories}")
        else:
            print("  No moderation result returned.")


if __name__ == "__main__":
    try:
        asyncio.run(check_moderation())
    except Exception as e:
        print(f"An error occurred: {e}")
