# -*- coding: utf-8 -*-
import os.path
import uuid
from typing import Any

import cv2
import gradio as gr
import numpy as np
from gradio.utils import get_upload_folder
from pydantic.dataclasses import dataclass
from sinapsis_core.cli.run_agent_from_config import generic_agent_builder
from sinapsis_core.data_containers.data_packet import DataContainer, ImagePacket, TextPacket
from sinapsis_core.utils.env_var_keys import SINAPSIS_CACHE_DIR
from sinapsis_core.utils.logging_utils import sinapsis_logger

from sinapsis.webapp.agent_gradio_helper import add_logo_and_title, css_header

LOGIN_TEMPLATE = """
<div style="text-align: center;">
  <img src="{image}" width="64" style="display: block; margin: 0 auto 10px auto;" />
  <p style="font-size: 16px; font-weight: bold;">{title}</p>
  <p>{message}</p>
</div>
"""
SINAPSIS_AVATAR = "https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/fav_icon.png?raw=true"


@dataclass
class ChatbotConfig:
    """Configuration class for the chatbot application.

    Attributes:
        app_title (str): The title displayed on the chatbot interface.
        login_message (str): The message shown on the login screen.
        login_image (str): URL of the image displayed on the login screen.
        enable_memories (bool): Flag to enable memory features.
        examples (list[str] | None): Optional list of example inputs to show in the UI.
        users_db_config (dict[str, str] | None): Database configuration for user authentication.
    """

    app_title: str = "Sinapsis Chatbot"
    # login_message: str = "Please log in with your credentials to continue."
    login_image: str = SINAPSIS_AVATAR
    enable_memories: bool = True
    examples: list[str] | None = None
    # users_db_config: dict[str, str] | None = None


@dataclass
class ChatKeys:
    """
    Defines key names used for referencing various chat-related data types.

    This class serves as a centralized place to manage key names for different types of data
    that may be used in chat interactions. These keys are typically used to map data in structured formats.
    """

    text: str = "text"
    image: str = "image"
    files: str = "files"
    file_path: str = "path"
    audio_path: str = "audio_path"
    role: str = "role"
    content: str = "content"
    user: str = "user"
    assistant: str = "assistant"


class BaseChatbot:
    """
    A base chatbot class designed to work with various LLM frameworks, such as LLaMA.
    This class provides the functionality to interact with users through text, audio,
    and file inputs, maintain chat history, and integrate with Gradio for a web
    interface. The class is intended to serve as a foundation
    that can be adapted to different LLM frameworks by modifying the agent
    initialization and response handling methods.
    """

    def __init__(self, config_file: str, config: ChatbotConfig | dict[str, Any] = ChatbotConfig()) -> None:
        self.config_file = config_file
        self.config = ChatbotConfig(**config) if isinstance(config, dict) else config
        self.agent = generic_agent_builder(self.config_file)
        self.examples = [{ChatKeys.text: example} for example in self.config.examples] if self.config.examples else None
        self.file_name = f"{SINAPSIS_CACHE_DIR}/chatbot/chat.txt"
        os.makedirs(os.path.dirname(self.file_name), exist_ok=True)
        self._setup_working_directory()

    def _setup_working_directory(self) -> None:
        """Creates a temporary directory for storing uploaded media files."""
        self.gradio_temp_dir = get_upload_folder()
        os.makedirs(self.gradio_temp_dir, exist_ok=True)

    @staticmethod
    def _format_history(history: list[dict[str, Any]], max_turns: int = 5) -> dict[str, Any]:
        """Formats the chat history into a simplified dictionary with limited turns per role.

        Args:
                history (list[dict[str, Any]]): Full chat history with role and content.
                max_turns (int, optional): Number of recent messages to keep per role. Defaults to 5.

        Returns:
                dict[str, Any]: A dictionary in the form {"user": [...], "assistant": [...]}.
        """
        user_msgs = [entry[ChatKeys.content] for entry in history if entry[ChatKeys.role] == ChatKeys.user][-max_turns:]
        assistant_msgs = [entry[ChatKeys.content] for entry in history if entry[ChatKeys.role] == ChatKeys.assistant][
            -max_turns:
        ]
        return {
            ChatKeys.user: user_msgs,
            ChatKeys.assistant: assistant_msgs,
        }

    def generate_packet(
        self, container: DataContainer, message: dict[str, Any], history: list[dict[str, Any]], conv_id: str
    ) -> DataContainer:
        """Creates a `DataContainer` object from user message and chat history.

        Args:
                container (container): incoming container for the query
                message (dict[str, Any]): Dictionary with keys like 'text' and 'files'.
                history (list[dict[str, Any]]): List of previous chat messages.
                conv_id (str): Conversation id value

        Returns:
                DataContainer: A structured container of the parsed input.
        """
        formatted_history = self._format_history(history)
        container.texts.append(
            TextPacket(content=message.get(ChatKeys.text), source=conv_id, generic_data={"history": formatted_history})
        )
        for file_path in message.get(ChatKeys.files, []):
            if file_path.endswith(".wav"):
                container.generic_data[ChatKeys.audio_path] = file_path
            else:
                img_bgr = cv2.imread(file_path)
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                filename = os.path.basename(file_path)
                container.images.append(ImagePacket(content=img_rgb, color_space=1, source=filename))
        return container

    def agent_execution(self, container: DataContainer) -> dict[str, Any]:
        """Executes the Sinapsis agent and processes the result into chatbot output.

        Args:
            container (DataContainer): Structured input for the agent.

        Returns:
            dict[str, Any]: Dictionary with keys such as 'text' and 'files' to display in the UI.
        """
        default_response = {ChatKeys.text: "Could not process request, please try again", ChatKeys.files: []}
        result_container = self.agent(container)
        response = {}

        if result_container.texts:
            response[ChatKeys.text] = result_container.texts[-1].content

        if result_container.images:
            image_packet = container.images[-1]
            img_array = np.uint8(image_packet.content)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            image_path = os.path.join(self.gradio_temp_dir, image_packet.source)
            cv2.imwrite(image_path, img_array)
            response[ChatKeys.files] = [image_path]

        return response if response else default_response

    @staticmethod
    def _set_conversation_id(conv_id: str) -> str:
        """
        Ensure a valid conversation ID is set. If no ID is provided, a new one is
        generated.
        Args:
            conv_id (str): The provided conversation ID.
        Returns:
            str: The valid conversation ID (either provided or generated).
        """
        if not conv_id:
            conv_id = str(uuid.uuid4())
        return conv_id

    def stop_agent(self) -> dict:
        """
        Stop the chatbot's agent and save the chat history to a file.


        Returns:
            tuple: A tuple with None and Gradio updates for interactivity.
        """

        self.agent = None
        return gr.update(interactive=False)

    def _clear_history(self) -> None:
        """
        Clears the chat history and saves it to a file named "chat.txt".

        This method writes the current chat history to a file in JSON format,
            then clears the history.
        """

        try:
            os.remove(self.file_name)
        except FileNotFoundError:
            sinapsis_logger.warning("Chat history file does not exist")

    def process_msg(self, message: dict, history: list[dict], conv_id: str, container: DataContainer) -> dict:
        """
        Process a user message and generate a chatbot response.

        Args:
            message (str): The user's input message.
            history: list[dict]: list of messages sent through chatbot
            conv_id (str): The conversation ID for the current session.
            container (DataContainer): Incoming data container for the query

        Returns:
            tuple: The updated chat history and UI components for the chatbot interface.
        """
        container = container or DataContainer()
        conv_id = self._set_conversation_id(conv_id)
        container = self.generate_packet(container, message, history, conv_id)
        response = self.agent_execution(container)
        return response

    def add_app_components(self, conv_id) -> gr.ChatInterface:
        """Builds and returns the main Gradio chat interface.

        Returns:
            gr.ChatInterface: Configured chat interface with multimodal input.
        """
        chatbot = gr.Chatbot(
            type="messages",
            height=600,
            show_label=False,
            avatar_images=(None, SINAPSIS_AVATAR),
            show_copy_all_button=True,
        )
        textbox = gr.MultimodalTextbox(
            file_count="multiple",
            file_types=[".png", ".jpg", ".wav"],
            sources=["upload", "microphone"],
            placeholder="Message Chatbot",
        )
        container = gr.State(value=DataContainer())
        interface = gr.ChatInterface(
            fn=self.process_msg,
            title=None,
            multimodal=True,
            chatbot=chatbot,
            fill_height=True,
            css=css_header,
            type="messages",
            examples=self.examples,
            example_icons=[SINAPSIS_AVATAR] * len(self.examples) if self.examples else None,
            textbox=textbox,
            save_history=True,
            additional_inputs=[conv_id, container],
        )

        stop_agent = gr.Button("Stop chatbot")
        stop_agent.click(self.stop_agent, outputs=[textbox])

        return interface

    def app_interface(self) -> gr.Blocks:
        """Builds the full Gradio UI layout for the chatbot application.

        Returns:
            gr.Blocks: Gradio Blocks layout for the complete application.
        """
        with gr.Blocks(css=css_header(), title=self.config.app_title) as chatbot_interface:
            add_logo_and_title(self.config.app_title)
            conv_id = gr.State(value=str(uuid.uuid4()))
            self.add_app_components(conv_id)

        return chatbot_interface

    def launch(self, **kwargs: dict[str, Any]) -> None:
        """Launches the Gradio app, optionally with authentication and custom options."""
        interface = self.app_interface()
        interface.launch(
            **kwargs,
        )
