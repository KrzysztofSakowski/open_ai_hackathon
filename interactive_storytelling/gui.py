import asyncio
import queue
import threading
from queue import Queue
from typing import AsyncGenerator

import customtkinter
from PIL import Image  # Import PIL
from dotenv import load_dotenv

from interactive_storytelling.agent import run_interactive_story
from interactive_storytelling.models import StorytellerContext, StoryMoral, InteractiveTurnOutput

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
        self.result_queue: Queue[InteractiveTurnOutput | Exception] = queue.Queue()
        self.story_context = StorytellerContext(  # Default context, can be made configurable
            main_topic="A curious squirrel discovering a hidden world in a park.",
            main_moral=StoryMoral(
                name="Curiosity",
                description="Curiosity leads to discovery.",
            ),
            main_character="Squeaky, the squirrel",
            language="English",
            age=8,
        )

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
        self.main_frame.grid_rowconfigure(1, weight=1)  # Allow textbox to expand
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
        self.story_textbox.insert("0.0", "Welcome! Click 'Start Story' to begin.")
        self.story_textbox.configure(state="disabled")  # Make read-only

        # --- Create button frame ---
        self.button_frame = customtkinter.CTkFrame(self.main_frame)
        self.button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)  # Make buttons expand

        self.button_option_1 = customtkinter.CTkButton(self.button_frame, text="Start Story", command=self.start_story)
        self.button_option_1.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.button_option_2 = customtkinter.CTkButton(
            self.button_frame, text="", command=lambda: self.make_choice("B"), state="disabled"
        )
        self.button_option_2.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def start_story(self):
        print("Starting story...")
        self.story_generator = run_interactive_story(self.story_context)
        self.button_option_1.configure(text="Option A", command=lambda: self.make_choice("A"), state="disabled")
        self.button_option_2.configure(state="disabled")
        self._advance_story(None)  # Start the story with no initial choice

    def make_choice(self, choice: str):
        print(f"Choice made: {choice}")
        self._advance_story(choice)

    def _run_async_story_step(self, choice: str | None):
        """Runs the async story generator step in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result: InteractiveTurnOutput = loop.run_until_complete(self.story_generator.asend(choice))
            self.result_queue.put(result)
        except Exception as e:
            # Put exception in queue to handle it in the main thread
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

        # Run the async part in a separate thread
        thread = threading.Thread(target=self._run_async_story_step, args=(choice,))
        thread.start()

        # Start polling the queue for the result
        self._check_queue()

    def _check_queue(self):
        """Checks the queue for results from the async thread."""
        try:
            result = self.result_queue.get_nowait()
            if isinstance(result, Exception):
                # Handle exceptions from the async thread
                print(f"Error in story generation: {result}")
                self.story_textbox.configure(state="normal")
                self.story_textbox.delete("0.0", "end")
                self.story_textbox.insert("0.0", f"An error occurred: {result}")
                self.story_textbox.configure(state="disabled")
                # Maybe reset or offer to restart?
                self.button_option_1.configure(text="Start New Story?", command=self.start_story, state="normal")
                self.button_option_2.configure(text="", state="disabled")
            else:
                print(type(result))
                self._update_ui(result)
        except queue.Empty:
            # If queue is empty, schedule to check again later
            self.after(100, func=self._check_queue)

    def _update_ui(self, story_turn: InteractiveTurnOutput):
        """Updates the GUI elements with the new story content."""
        print(f"Updating UI with {story_turn}...")
        self.story_textbox.configure(state="normal")  # Enable editing
        self.story_textbox.delete("1.0", "end")
        self.story_textbox.insert("1.0", story_turn.scene_text)
        self.story_textbox.configure(state="disabled")  # Disable editing

        # TODO: Update image_label with the actual generated image
        # self.image_label.configure(image=...) # Load and set the image

        if story_turn.decisions:
            self.button_option_1.configure(text=story_turn.decisions.option1, state="normal")
            self.button_option_2.configure(text=story_turn.decisions.option2, state="normal")
        else:
            # Story ended
            self.button_option_1.configure(text="The End", state="disabled")
            self.button_option_2.configure(text="Start Over?", state="normal", command=self.start_story)


if __name__ == "__main__":
    app = StoryApp()
    app.mainloop()
