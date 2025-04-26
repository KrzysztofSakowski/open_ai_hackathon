import base64
import os
import time
from pathlib import Path
from typing import cast

from runwayml import RunwayML


def get_client_runway() -> RunwayML:
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        raise EnvironmentError("RUNWAY_API_KEY environment variable is not set.")
    return RunwayML(api_key=api_key)


def generate_video(input_image_path: Path, client: RunwayML):
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


def check_task_status(task_id, client: RunwayML):
    """Polls task status with a timeout mechanism and returns output URLs."""
    try:
        task = client.tasks.retrieve(id=task_id)
        if task is None or task.status is None:
            print(f"Task {task_id} not found or status is None.")
            return None
        elif task.status == "SUCCEEDED":
            assert task.output, "Task output is None"
            print("Task completed!")
            return [output for output in task.output]

        elif task.status == "FAILED":
            print("Task failed.")
            return None

        else:
            assert False, f"Unexpected task status: {task.status}"

    except Exception as e:
        print(f"Error checking task status: {e}")
        return None


def generate_videos(images: list[Path]) -> list[str]:
    print("Starting video generation...")
    client = get_client_runway()
    task_ids: dict[str, str | None] = {}

    for img in images:
        assert img.exists(), f"Image {img} does not exist."

        task_id = generate_video(img, client)  # Get task ID
        assert task_id, f"Failed to create task for {img}"
        print(f"Task ID: {task_id}")
        task_ids[task_id] = None  # Mark tsk as not ready

    while not all(task_ids.values()):
        print("Waiting for tasks to complete...")
        time.sleep(10)

        for task_id, url in task_ids.items():
            if url is not None:
                continue

            url_candidate = check_task_status(task_id, client)
            if url_candidate:
                task_ids[task_id] = url_candidate
                print(f"Task {task_id} is ready.")
            else:
                print(f"Task {task_id} is not ready yet.")

    list_of_videos = list(task_ids.values())
    for idx, video in enumerate(list_of_videos, start=1):
        print(f"Video {idx}: {video}")

    return cast(list[str], list_of_videos)


if __name__ == "__main__":
    generate_videos(
        images=[
            Path("sample_images/1fe76004-b7dd-438d-a82b-26687f79eba1/img_0.png"),
            Path("sample_images/1fe76004-b7dd-438d-a82b-26687f79eba1/img_1.png"),
        ]
    )
