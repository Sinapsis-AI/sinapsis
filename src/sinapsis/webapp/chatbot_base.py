# -*- coding: utf-8 -*-
import os.path
import uuid
from typing import Any

import cv2
import gradio as gr
import numpy as np
from gradio.utils import get_upload_folder
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from sinapsis_core.agent.agent import Agent
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
    login_image: str = SINAPSIS_AVATAR
    # enable_memories: bool = True
    examples: list[str] | None = None


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


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class ChatInterfaceComponents:
    """Container for core UI components used in the chat interface.

    Attributes:
        chatbot (gr.Chatbot): The chatbot message display area.
        textbox (gr.MultimodalTextbox): Input field for user messages and file uploads.
        session_state (gr.State): State object to track the user's session.
        chat_interface (gr.ChatInterface): Main Gradio chat interface component.
    """

    chatbot: gr.Chatbot
    textbox: gr.MultimodalTextbox
    session_state: gr.State
    chat_interface: gr.ChatInterface


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
        self.chatbot_height = "70vh"
        self.agent = self.initialize_agent(self.config_file)
        self.examples = (
            [[{ChatKeys.text: example}, None] for example in self.config.examples] if self.config.examples else None
        )
        self._setup_working_directory()

    @staticmethod
    def initialize_agent(config_file: str) -> Agent:
        """Instantiate the chatbot agent from the configuration file."""
        return generic_agent_builder(config_file)

    def stop_agent(self) -> tuple[dict, dict, dict]:
        """Stops the chatbot agent and disables user input components in the UI.

        This method performs cleanup of the agent, releases GPU memory, logs the shutdown,
        and returns Gradio UI updates that:

            - Disable the input textbox and stop button.
            - Enable the restart button.

        Returns:
            tuple[dict, dict, dict]: Gradio UI updates for textbox, stop button and restart button.
        """
        self.agent.cancel_agent_execution()
        gr.Info("🛑 Chatbot stopped!")
        sinapsis_logger.info("Chatbot stopped")
        return (
            gr.update(interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=True),
        )

    def _setup_working_directory(self) -> None:
        """Create and ensure the existence of directories for uploads and cached chat histories."""
        self.gradio_temp_dir = get_upload_folder()
        self.chats_dir = os.path.join(SINAPSIS_CACHE_DIR, "chats")
        os.makedirs(self.gradio_temp_dir, exist_ok=True)
        os.makedirs(self.chats_dir, exist_ok=True)

    def restart_agent(self) -> tuple[dict, dict, dict]:
        """Reinitializes the chatbot agent and enables user input components in the UI.

        This method rebuilds the agent, logs the startup, and returns Gradio UI updates that:

            - Enable the input textbox and stop button.
            - Disable the restart button.

        Returns:
            tuple[dict, dict, dict]: Gradio UI updates for textbox, stop button and restart button.
        """
        self.agent = self.initialize_agent(self.config_file)
        gr.Success("✅ Chatbot ready!")
        sinapsis_logger.info("Chatbot initialized")
        return (
            gr.update(interactive=True),
            gr.update(interactive=True),
            gr.update(interactive=False),
        )

    @staticmethod
    def generate_packet(message: dict[str, Any], user_id: str, session_id: str | None = None) -> DataContainer:
        """Constructs a DataContainer from user input including text, files, and optional session info.

        Args:
                message (dict[str, Any]): User input with keys: 'text', 'files'.
                user_id (str): Unique identifier for the user.
                session_id (str | None, optional): Identifier for the session. Defaults to None.

        Returns:
                DataContainer: Structured container with text, images, or audio ready for agent execution.
        """
        container = DataContainer()
        container.texts.append(TextPacket(content=message.get(ChatKeys.text), id=user_id, source=session_id))
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

    def generate_user_response(
        self, message: dict[str, Any], user_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Generates a response from the agent for a given user input.

        Args:
            message (dict[str, Any]): Dictionary with user inputs (text, files, etc.).
            user_id (str): Unique user identifier.
            session_id (str | None, optional): Optional unique session identifier. Defaults to None.

        Returns:
            dict[str, Any]: Response payload containing 'text' and/or 'files'.
        """
        container = self.generate_packet(message, user_id, session_id)
        return self.agent_execution(container)

    def handle_user_message(
        self, message: dict[str, Any], history: list[dict], session_state: str, user_id: gr.State | str
    ) -> dict[str, Any]:
        """Handles a user message from the UI and routes it through the agent.

        Args:
            message (dict[str, Any]): Input data from the user interface.
            history (list[dict]): Unused chat history.
            session_state (str): Session UUID state.
            user_id (gr.State | None): user ID state.

        Returns:
            dict[str, Any]: Chatbot response formatted for the UI.
        """
        _ = history
        return self.generate_user_response(message, user_id, session_state)

    def _build_chat_interface(self) -> ChatInterfaceComponents:
        """Constructs the main chat interface with all core components.

        This includes the chatbot display, multimodal input textbox,
        session state, and the overall `ChatInterface` wrapper.

        Returns:
            ChatInterfaceComponents: A container holding all relevant UI components.
        """
        chatbot = gr.Chatbot(
            type="messages",
            height=self.chatbot_height,
            show_label=False,
            avatar_images=(None, SINAPSIS_AVATAR),
            show_copy_button=True,
        )
        textbox = gr.MultimodalTextbox(
            file_count="multiple",
            file_types=[".png", ".jpg", ".wav"],
            sources=["upload", "microphone"],
            placeholder="Message Chatbot",
        )
        session_state = gr.State(str(uuid.uuid4()))
        user_id = gr.Textbox("Chatbot user", visible=False)
        chat_interface = gr.ChatInterface(
            fn=self.handle_user_message,
            additional_inputs=[session_state, user_id],
            title=None,
            multimodal=True,
            chatbot=chatbot,
            fill_height=True,
            type="messages",
            examples=self.examples,
            example_icons=[SINAPSIS_AVATAR] * len(self.examples) if self.examples else None,
            textbox=textbox,
            api_name=False,
        )
        chatbot.clear(self.handle_clear_history, inputs=[session_state, user_id])

        return ChatInterfaceComponents(chatbot, textbox, session_state, chat_interface)

    def clear_user_conversation(self, user_id: str, session_id: str | None = None) -> None:
        """Clears stored conversation data for the specified user/session.

        Can be overridden by subclasses to customize additional actions when clearing conversations.

        Args:
            user_id (str): Unique user identifier.
            session_id (str | None, optional): Optional session ID to scope clearing. Defaults to None.

        Returns:
            Any: Result of the clear operation (to be defined by subclasses).
        """

    def handle_clear_history(self, session_state: gr.State, user_id: str) -> None:
        """Triggers the clearing of a user's chat history from the UI button.

        Args:
            session_state (gr.State): Current session state object.
            user_id (str): Gradio request containing user/session info.
        """
        # user_id = request.username if request.username else request.session_hash
        self.clear_user_conversation(user_id, session_state)

    def _add_buttons(self, chat_components: ChatInterfaceComponents):
        """Adds 'Stop' and 'Start Chatbot' buttons to control agent lifecycle.

        Can be overriden by subclasses to add more control buttons in the footer.

        Args:
            chat_components (ChatInterfaceComponents): Container with components needed
                to enable/disable input based on chatbot state.
        """
        stop_btn = gr.Button("Stop chatbot")
        restart_btn = gr.Button("Start Chatbot", interactive=False)
        stop_btn.click(self.stop_agent, outputs=[chat_components.textbox, stop_btn, restart_btn])
        restart_btn.click(self.restart_agent, outputs=[chat_components.textbox, stop_btn, restart_btn])

    def _inject_header_components(self):
        """Adds visual elements at the top of the UI (e.g., logo, app title).

        Can be overridden by subclasses to customize header layout.
        """
        add_logo_and_title(self.config.app_title)

    def _inject_footer_components(self, chat_components: ChatInterfaceComponents):
        """Adds UI components below the chat interface, such as control buttons.

        Can be overriden by subclasses to add more elements in the footer.

        Args:
            chat_components (ChatInterfaceComponents): Group of UI elements built in the chat interface.
        """
        with gr.Row():
            self._add_buttons(chat_components)

    def app_interface(self) -> gr.Blocks:
        """Builds the full Gradio Blocks layout including chat interface, headers, footers, and extras.

        Returns:
            gr.Blocks: Composed Gradio interface ready to launch.
        """
        with gr.Blocks(css=css_header(), title=self.config.app_title) as interface:
            self._inject_header_components()
            chat_components = self._build_chat_interface()
            self._inject_footer_components(chat_components)

        return interface

    def launch(self, **kwargs: dict[str, Any]) -> None:
        """Launches the Gradio app, optionally with authentication and custom options."""
        interface = self.app_interface()
        interface.launch(
            **kwargs,
        )
