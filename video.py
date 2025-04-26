# Fairytale agent using OpenAI's GPT-4o model
import base64
import os
import time
from pathlib import Path

from runwayml import RunwayML


def get_client_runway() -> RunwayML:
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        raise EnvironmentError("RUNWAY_API_KEY environment variable is not set.")
    return RunwayML(api_key=api_key)


def generate_video(input_image_path: Path, client):
    """Encodes an image and submits a request to generate video."""
    try:
        with open(input_image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        prompt_image = f"data:image/webp;base64,{encoded_image}"

        task = client.image_to_video.create(
            model="gen4_turbo",
            prompt_image=prompt_image,
            prompt_text="Follow a main character in a fairytale world.",
            ratio="1280:720",
        )

        print(f"Task created with ID: {task.id}")
        return task.id

    except Exception as e:
        print(f"Error generating video: {e}")
        return None


def check_task_status(task_id, client, timeout=60):
    """Polls task status with a timeout mechanism and returns output URLs."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            task = client.tasks.retrieve(id=task_id)

            if task.status == "SUCCEEDED":
                print("Task completed!")
                return [output for output in task.output]

            elif task.status == "FAILED":
                print("Task failed.")
                return None

            else:
                print(f"Task status: {task.status}. Retrying in 10 seconds...")
                time.sleep(10)

        except Exception as e:
            print(f"Error checking task status: {e}")
            return None

    print("Task polling timeout reached.")
    return None


def generate_videos(images: list[Path]):
    print("Starting video generation...")
    client = get_client_runway()

    list_of_videos = []

    for img in images:
        assert img.exists(), f"Image {img} does not exist."

        task_id = generate_video(img, client)  # Get task ID
        print(f"Task ID: {task_id}")

        if task_id:
            video_output = check_task_status(task_id, client)  # Get output URLs

            if video_output:
                list_of_videos.extend(video_output)  # Append URLs

    print("Generated videos:", list_of_videos)
    return list_of_videos


if __name__ == "__main__":
    generate_videos(
        images=[
            Path("sample_images/1fe76004-b7dd-438d-a82b-26687f79eba1/img_0.png"),
            Path("sample_images/1fe76004-b7dd-438d-a82b-26687f79eba1/img_1.png"),
        ]
    )
