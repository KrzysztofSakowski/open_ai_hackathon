import asyncio
import queue
import threading
from queue import Queue
from typing import AsyncGenerator
import os
import io
import tempfile
from playsound3 import playsound

import customtkinter
from PIL import Image
from dotenv import load_dotenv
from audio import generate_audio

from interactive_storytelling.agent import run_interactive_story
from interactive_storytelling.models import StorytellerContext, StoryMoral, InteractiveTurnOutput
from image_generation.agent import generate_images
from image_generation.models import ImageGeneratorContext, ImageGenerationPrompt

import settings

# --- Basic Setup ---
customtkinter.set_appearance_mode("system")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class StoryApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # --- Configure window ---
        self.title("Interactive Storyteller")
        self.geometry(f"{800}x{600}")

        # --- Load environment variables ---
        load_dotenv()

        # --- Story State ---
        self.story_generator: AsyncGenerator[InteractiveTurnOutput, str] | None = None
        self.result_queue: Queue[tuple[InteractiveTurnOutput | None, bytes | None, str | None] | Exception] = (
            queue.Queue()
        )
        self.story_context = StorytellerContext(  # Default context, can be made configurable
            main_topic="A curious squirrel discovering a hidden world in a park.",
            main_moral=StoryMoral(
                name="Curiosity",
                description="Curiosity leads to discovery.",
            ),
            main_character="Squeaky, the squirrel",
            language="Polish",
            age=8,
        )

        # Initialize OpenAI client
        self.openai_client = settings.openai_client
        # Audio playback state
        self.current_sound_playback = None
        self.current_audio_path = None

        # --- Configure grid layout (1x2) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Create sidebar frame with widgets ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Story Options", font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # Add any sidebar controls here if needed later

        # --- Create main content frame ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        # Configure row weights for resizing: Give image (row 0) more weight than textbox (row 1)
        self.main_frame.grid_rowconfigure(0, weight=3)  # Image row
        self.main_frame.grid_rowconfigure(1, weight=2)  # Textbox row
        self.main_frame.grid_columnconfigure(0, weight=1)  # Allow widgets to expand horizontally

        # --- Create image display (Placeholder) ---
        # Placeholder for now, replace with actual image loading later
        # You might need to adjust the size based on your image generation
        placeholder_image = Image.new("RGB", (400, 300), color="grey")
        self.story_image_ctk = customtkinter.CTkImage(
            light_image=placeholder_image, dark_image=placeholder_image, size=(400, 300)
        )
        self.image_label = customtkinter.CTkLabel(self.main_frame, text="", image=self.story_image_ctk)
        self.image_label.grid(row=0, column=0, padx=20, pady=10)

        # --- Create textbox for story scene ---
        self.story_textbox = customtkinter.CTkTextbox(self.main_frame, wrap="word")  # Changed to CTkTextbox
        self.story_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.story_textbox.insert("1.0", "Welcome! Click 'Start Story' to begin.")
        self.story_textbox.configure(state="disabled")  # Make read-only

        # --- Create button frame ---
        self.button_frame = customtkinter.CTkFrame(self.main_frame)
        self.button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)  # Make buttons expand

        self.button_option_1 = customtkinter.CTkButton(self.button_frame, text="Start Story", command=self.start_story)
        self.button_option_1.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.button_option_2 = customtkinter.CTkButton(
            self.button_frame, text="-", command=lambda: self.make_choice("B"), state="disabled"
        )
        self.button_option_2.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Register the closing protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_story(self):
        print("Starting story...")
        self.story_generator = run_interactive_story(self.story_context)
        self.button_option_1.configure(text="Option A", command=lambda: self.make_choice("A"), state="disabled")
        self.button_option_2.configure(state="disabled")
        self._advance_story(None)  # Start the story with no initial choice
        # Keep track of the last played audio path to delete it
        self.last_played_audio_path: str | None = None

    def make_choice(self, choice: str):
        print(f"Choice made: {choice}")
        self._advance_story(choice)

    async def _async_get_story_and_generate_media(
        self, choice: str | None
    ) -> tuple[InteractiveTurnOutput | None, bytes | None, str | None]:
        """Helper async function to run story and media generation tasks."""
        story_turn_result: InteractiveTurnOutput | None = None
        image_bytes_result: bytes | None = None
        audio_path_result: str | None = None

        # 1. Get the next story turn
        story_turn_result = await self.story_generator.asend(choice)

        if story_turn_result:
            # --- Set up concurrent Image and Audio Generation Tasks ---
            img_gen_task = None
            if story_turn_result.description_of_the_scene_for_image_generation:
                print(
                    f"Setting up image generation for: {story_turn_result.description_of_the_scene_for_image_generation[:50]}..."
                )
                img_context = ImageGeneratorContext(
                    images_to_generate=[
                        ImageGenerationPrompt(
                            base_images=[],
                            prompt=story_turn_result.description_of_the_scene_for_image_generation,
                            quality="low",
                        )
                    ],
                    child_age=self.story_context.age,
                    child_preferred_style="cartoonish",
                )
                img_gen_task = asyncio.create_task(generate_images(img_context))

            audio_gen_task = None
            temp_audio_path = None
            if story_turn_result.scene_text:
                print(f"Setting up audio generation for: {story_turn_result.scene_text[:50]}...")
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_f:
                        temp_audio_path = tmp_f.name
                    print(f"Generated temp path for audio: {temp_audio_path}")
                    audio_gen_task = asyncio.create_task(
                        generate_audio(self.openai_client, story_turn_result.scene_text, temp_audio_path)
                    )
                except Exception as path_exc:
                    print(f"Error creating temp audio file path: {path_exc}")
                    temp_audio_path = None

            # --- Await concurrent tasks using asyncio.gather ---
            tasks_to_await = [task for task in [img_gen_task, audio_gen_task] if task is not None]
            if tasks_to_await:
                print("Awaiting image/audio generation...")
                try:
                    results = await asyncio.gather(*tasks_to_await, return_exceptions=True)
                    # Process results safely
                    res_idx = 0
                    if img_gen_task:
                        img_res = results[res_idx]
                        if isinstance(img_res, list) and img_res:
                            image_bytes_result = img_res[0]
                            print("Image generated successfully.")
                        elif isinstance(img_res, Exception):
                            print(f"Error during image generation: {img_res}")
                        else:
                            print("Image generation returned no/unexpected results.")
                        res_idx += 1
                    if audio_gen_task:
                        audio_res = results[res_idx]
                        if isinstance(audio_res, Exception):
                            print(f"Error during audio generation: {audio_res}")
                            if temp_audio_path and os.path.exists(temp_audio_path):
                                try:
                                    os.remove(temp_audio_path)
                                except OSError:
                                    pass
                            temp_audio_path = None
                        elif temp_audio_path:
                            audio_path_result = temp_audio_path
                            print("Audio generated successfully.")
                        else:
                            print("Audio generation task finished but temp path missing?")

                except Exception as gather_exc:
                    print(f"Error awaiting generation tasks: {gather_exc}")
                    if temp_audio_path and os.path.exists(temp_audio_path):
                        try:
                            os.remove(temp_audio_path)
                        except OSError:
                            pass
                    temp_audio_path = None

        return story_turn_result, image_bytes_result, audio_path_result

    def _run_async_story_step(self, choice: str | None):
        """Runs the async helper function in a separate thread's event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            story_turn, image_bytes, audio_path = loop.run_until_complete(
                self._async_get_story_and_generate_media(choice)
            )

            self.result_queue.put((story_turn, image_bytes, audio_path))

        except Exception as e:
            print(f"Error in async step execution: {e}")
            self.result_queue.put(e)
        finally:
            loop.close()

    def _advance_story(self, choice: str | None):
        """Initiates the async story step in a background thread."""
        self.button_option_1.configure(state="disabled")
        self.button_option_2.configure(state="disabled")
        self.story_textbox.configure(state="normal")
        self.story_textbox.delete("0.0", "end")
        self.story_textbox.insert("0.0", "Thinking...")
        self.story_textbox.configure(state="disabled")

        thread = threading.Thread(target=self._run_async_story_step, args=(choice,))
        thread.start()

        self._check_queue()

    def _check_queue(self):
        """Checks the queue for results from the async thread."""
        try:
            result = self.result_queue.get_nowait()
            if isinstance(result, Exception):
                print(f"Error in story/image/audio generation: {result}")
                self.story_textbox.configure(state="normal")
                self.story_textbox.delete("0.0", "end")
                self.story_textbox.insert("0.0", f"An error occurred: {result}")
                self.story_textbox.configure(state="disabled")
                self._display_image_bytes(None)
                self.button_option_1.configure(text="Start New Story?", command=self.start_story, state="normal")
                self.button_option_2.configure(text="", state="disabled")
            elif isinstance(result, tuple) and len(result) == 3:
                story_turn, image_bytes, audio_path = result
                if story_turn is not None:
                    self._update_ui(story_turn, image_bytes, audio_path)
                else:
                    print("Error: Received None for story_turn in result tuple.")
                    self._display_image_bytes(None)

        except queue.Empty:
            self.after(100, func=self._check_queue)

    def _play_audio(self, audio_path: str | None):
        """Plays audio using playsound3, stopping the previous one first."""
        # Stop and clean up previous sound playback if it exists
        if self.current_sound_playback and self.current_sound_playback.is_alive():
            print("Stopping previous audio playback...")
            self.current_sound_playback.stop()
            self.current_sound_playback = None  # Clear the reference

        # Clean up the previous temporary audio file
        if self.current_audio_path:
            print(f"Attempting to remove previous audio file: {self.current_audio_path}")
            try:
                os.remove(self.current_audio_path)
                print(f"Successfully removed: {self.current_audio_path}")
            except OSError as e:
                print(f"Error removing previous audio file {self.current_audio_path}: {e}")
            self.current_audio_path = None  # Clear the path reference

        # Play the new audio file if a path is provided
        if audio_path:
            try:
                print(f"Playing audio from: {audio_path}")
                self.current_sound_playback = playsound(audio_path, block=False)
                self.current_audio_path = audio_path  # Store the new path
            except Exception as e:
                print(f"Error playing sound {audio_path}: {e}")
                self.current_sound_playback = None
                self.current_audio_path = None
                # Attempt cleanup even if playback failed to start
                try:
                    os.remove(audio_path)
                    print(f"Cleaned up failed playback file: {audio_path}")
                except OSError as remove_e:
                    print(f"Error removing failed playback file {audio_path}: {remove_e}")
        else:
            # Ensure references are clear if no new audio is played
            self.current_sound_playback = None
            self.current_audio_path = None

    def _display_image_bytes(self, image_bytes: bytes | None):
        """Displays an image from bytes data."""
        if image_bytes:
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=(400, 300))
                self.image_label.configure(image=ctk_image, text="")
                self.image_label.image = ctk_image
                print("Image displayed.")
            except Exception as e:
                print(f"Error loading image from bytes: {e}")
                self.image_label.configure(image=self.story_image_ctk, text="Error loading image")
                self.image_label.image = self.story_image_ctk
        else:
            print("No image bytes provided, displaying placeholder.")
            self.image_label.configure(image=self.story_image_ctk, text="")
            self.image_label.image = self.story_image_ctk

    def _update_ui(self, story_turn: InteractiveTurnOutput, image_bytes: bytes | None, audio_path: str | None):
        """Updates the GUI elements with text, image, and plays audio."""
        print(f"Updating UI for scene...")
        self.story_textbox.configure(state="normal")
        self.story_textbox.delete("1.0", "end")
        self.story_textbox.insert("1.0", story_turn.scene_text)
        self.story_textbox.configure(state="disabled")

        self._display_image_bytes(image_bytes)

        self._play_audio(audio_path)

        if story_turn.decisions:
            self.button_option_1.configure(text=story_turn.decisions.option1, state="normal")
            self.button_option_2.configure(text=story_turn.decisions.option2, state="normal")
        else:
            self.button_option_1.configure(text="The End", state="disabled")
            self.button_option_2.configure(text="Start Over?", state="normal", command=self.start_story)

    def on_closing(self):
        """Handles window close event."""
        print("Window closing...")
        # Stop any active sound playback
        if self.current_sound_playback and self.current_sound_playback.is_alive():
            print("Stopping audio on close...")
            self.current_sound_playback.stop()
            self.current_sound_playback = None

        # Clean up the last temporary audio file
        if self.current_audio_path:
            print(f"Removing last audio file on close: {self.current_audio_path}")
            try:
                os.remove(self.current_audio_path)
            except OSError as e:
                print(f"Error removing last audio file {self.current_audio_path} on close: {e}")
            self.current_audio_path = None

        print("Destroying window.")
        self.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    app = StoryApp()
    app.mainloop()
