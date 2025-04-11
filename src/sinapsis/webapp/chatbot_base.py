# -*- coding: utf-8 -*-
import json
import os.path
import uuid

import gradio as gr
import numpy as np
from PIL import Image
from pydantic.dataclasses import dataclass
from sinapsis_core.cli.run_agent_from_config import generic_agent_builder
from sinapsis_core.data_containers.data_packet import DataContainer, TextPacket
from sinapsis_core.utils.env_var_keys import SINAPSIS_CACHE_DIR
from sinapsis_core.utils.logging_utils import sinapsis_logger

from sinapsis.webapp.agent_gradio_helper import add_logo_and_title, css_header

SINAPSIS_AVATAR = "https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/fav_icon.png?raw=true"


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

    def __init__(self, config_file: str, app_title: str = "Sinapsis LLaMA Chatbot") -> None:
        """
        Initialize the chatbot with given configuration, framework, and task.

        Args:
            config_file (str): Path to the configuration file.
            app_title (str): Title of the app
        """
        self.config_file = config_file
        self.file_name = f"{SINAPSIS_CACHE_DIR}/chatbot/chat.txt"
        os.makedirs(os.path.dirname(self.file_name), exist_ok=True)
        self.app_title = app_title
        self.chat_history: list = self.load_chat()
        self.agent = generic_agent_builder(self.config_file)

    def load_chat(self) -> list:
        """If the file self.file_name exists, it loads
        previous chat history. Otherwise, it creates a new file and
        sets the chat history as an empty list

        Returns:
            the list of messages or empty list for messages
        """
        if os.path.exists(self.file_name):
            with open(self.file_name, "r", encoding="utf-8") as chat:
                try:
                    history = json.load(chat)
                except json.JSONDecodeError:
                    history = []
        else:
            history = []
            with open(self.file_name, "w") as file:
                json.dump(history, file)
        return history

    def generate_packet(self, message, conv_id: str) -> DataContainer:
        """
        Args:
        message (str): The user's input message, either as a audio file or text
        conv_id (str): The conversation ID to associate with the message.
        """
        container = DataContainer()
        if isinstance(message, dict):
            text_msg = message.get(ChatKeys.text, False)
            image_msg = message.get(ChatKeys.files, False)
            if text_msg:
                text_msg = TextPacket(content=message, id=conv_id)
                container.texts.append(text_msg)
            if image_msg:
                full_image_path = image_msg[0].split("/gradio/")
                data_dir = f"{full_image_path[0]}/gradio/"
                image_name = full_image_path[1]

                self.agent.update_template_attribute("ImageReader", "data_dir", data_dir)
                self.agent.update_template_attribute("ImageReader", "pattern", image_name)
                self.agent.reset_state("ImageReader")

        if isinstance(message, str):
            if not message.endswith("wav"):
                text_msg = TextPacket(content=message, id=conv_id)
                container.texts.append(text_msg)
            elif message.endswith("wav"):
                container.generic_data[ChatKeys.audio_path] = message
        return container

    def agent_execution(self, container: DataContainer) -> dict:
        """
        Makes a call to the agent to retrieve a response from the templates in the agent.

        Args:
            container (DataContainer): container with the packets to be processed by the
            templates in the agent.

        Returns:
            dict : The response to be added to the chatbot window

        """
        response = self.agent(container)
        response_dict = {
            ChatKeys.text: "Could not process request, please try again",
            ChatKeys.files: [],
        }
        if response.texts:
            response_dict = response.texts[-1].content

        if container.generic_data.get(ChatKeys.audio_path):
            container.generic_data[ChatKeys.audio_path] = False
        if response.images:
            image_as_packet = response.images[-1]
            image = Image.fromarray(np.uint8(image_as_packet.content))
            image_path = f"{SINAPSIS_CACHE_DIR}{image_as_packet.source}"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            image.save(image_path)
            response_dict = {ChatKeys.files: [image_path]}

        return response_dict

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

    def add_message(
        self, message: dict | str, role: str
    ) -> tuple[gr.components.MultimodalTextbox, gr.components.Audio]:
        """
        The method adds a user or assistant message to the chat history.

        Args:
            message (dict | str): The input message, either as text or a dictionary.
            role (str): The role of the message sender, e.g., "user" or "assistant".

        Returns:
            tuple: A tuple with updated chat history, a Textbox, and an Audio component.
        """
        if isinstance(message, dict):
            for x in message[ChatKeys.files]:
                self.chat_history.append({ChatKeys.role: role, ChatKeys.content: {ChatKeys.file_path: x}})
            if message.get(ChatKeys.text, False):
                self.chat_history.append({ChatKeys.role: role, ChatKeys.content: message[ChatKeys.text]})
        elif isinstance(message, str) and not message.endswith("wav"):
            self.chat_history.append({ChatKeys.role: role, ChatKeys.content: message})
        else:
            self.chat_history.append({ChatKeys.role: role, ChatKeys.content: {ChatKeys.file_path: message}})
        return (
            gr.MultimodalTextbox(),
            gr.Audio(),
        )

    def stop_agent(self) -> tuple[dict, dict]:
        """
        Stop the chatbot's agent and save the chat history to a file.


        Returns:
            tuple: A tuple with None and Gradio updates for interactivity.
        """
        with open(self.file_name, "w+", encoding="utf-8") as chat:
            json.dump(self.chat_history, chat, indent=4)
        chat.close()
        self.agent = None
        return gr.update(interactive=False), gr.update(interactive=False)

    def _clear_history(self) -> None:
        """
        Clears the chat history and saves it to a file named "chat.txt".

        This method writes the current chat history to a file in JSON format,
            then clears the history.
        """
        self.chat_history = []
        try:
            os.remove(self.file_name)
        except FileNotFoundError:
            sinapsis_logger.warning("Chat history file does not exist")

    def process_msg(self, message: str, conv_id: str) -> tuple[list, gr.MultimodalTextbox, gr.Audio, str] | list:
        """
        Process a user message and generate a chatbot response.

        Args:
            message (str): The user's input message.
            conv_id (str): The conversation ID for the current session.

        Returns:
            tuple: The updated chat history and UI components for the chatbot interface.
        """

        conv_id = self._set_conversation_id(conv_id)
        _ = self.add_message(message, ChatKeys.user)
        container = self.generate_packet(message, conv_id)
        response = self.agent_execution(container)
        retrieved_chat = self.add_message(response, ChatKeys.assistant)
        return self.chat_history, retrieved_chat[0], retrieved_chat[1], conv_id

    def add_app_components(self) -> tuple[gr.Chatbot, gr.MultimodalTextbox, gr.Audio]:
        """
        Add interactive components (buttons, inputs, and chatbot UI) to the interface.

        Returns:
            tuple: A tuple containing the components for the chatbot interface.
        """
        chatbot = gr.Chatbot(
            self.chat_history,
            type="messages",
            height=800,
            show_label=False,
            avatar_images=(None, SINAPSIS_AVATAR),
            show_copy_all_button=True,
        )
        chat_input = gr.MultimodalTextbox(
            interactive=True, placeholder="Enter a message", show_label=False, file_types=[".png", ".jpg"]
        )

        audio_input = gr.Audio(
            sources=["microphone"],
            type="filepath",
            label="Record Audio",
            interactive=True,
        )

        return chatbot, chat_input, audio_input

    def app_interface(self) -> None:
        """
        Define the core functionality of the chatbot, including initialization,
        message handling, and user interaction.
        """

        conversation_id = gr.State()
        (
            chatbot,
            chat_input,
            audio_input,
        ) = self.add_app_components()

        clear_btn = gr.ClearButton([audio_input, chat_input, chatbot, conversation_id])
        clear_btn.click(self._clear_history, inputs=[], outputs=[])

        audio_input.stop_recording(
            self.process_msg,
            inputs=[audio_input, conversation_id],
            outputs=[chatbot, chat_input, audio_input, conversation_id],
        )
        chat_input.submit(
            self.process_msg,
            inputs=[chat_input, conversation_id],
            outputs=[chatbot, chat_input, audio_input, conversation_id],
        )

        finish_chatbot = gr.Button(value="Finish chatbot", elem_id="finish-button", variant="primary")
        finish_chatbot.click(
            self.stop_agent,
            inputs=[],
            outputs=[chat_input, audio_input],
        )

    def __call__(self) -> gr.Blocks:
        with gr.Blocks(css=css_header()) as chatbot_interface:
            add_logo_and_title(self.app_title)
            self.app_interface()
        return chatbot_interface
