# -*- coding: utf-8 -*-

import gradio as gr
from sinapsis_core.agent import Agent
from sinapsis_core.cli.run_agent_from_config import generic_agent_builder
from sinapsis_core.data_containers.data_packet import DataContainer, TextPacket

from sinapsis.webapp.agent_gradio_helper import add_logo_and_title, css_header


class BaseTTSApp:
    """
    A base class for building text-to-speech (TTS) applications using various configurations.
    """

    def __init__(
        self,
        config_file: str,
        generic_key_or_base_path: str | None = None,
        framework: str = "Elevenlabs",
        task: str = "Text-to-Speech",
    ) -> None:
        """
        Initializes the TTS (Text-to-Speech) application with a given configuration file, framework, and task settings.

        Args:
            config_file (str): Path to the configuration file for the TTS application, which contains
                                necessary settings and parameters.
            generic_key_or_base_path (str | None): Optional key to access the container's generic data or the base_path
                where audios are located
            framework (str, optional): The name of the framework to be used in the user interface title.
                                       Defaults to Elevenlabs.
            task (str, optional): The task to be performed by the application (default is "Text-to-Speech").

        """
        self.config_file = config_file
        self.framework = framework
        self.task = task
        self.generic_key_or_base_path = generic_key_or_base_path
        self.agent, self.initialized_state = self.init_agent()

    def init_agent(self) -> tuple[Agent, bool]:
        """
        Initializes the agent using the configuration file.

        Returns:
            tuple: Updates agent_state and initialized_state.
        """
        return generic_agent_builder(self.config_file), True

    def _postprocess_output(self, container: DataContainer, generic_key: str | None) -> str | None:
        """
        Abstract method for postprocessing the agent's output to extract the audio path.

        Args:
            container (DataContainer): The container object returned by the agent after processing.
            generic_key (str): An optional key used for accessing specific data or configurations
                                related to the TTS agent. If not provided, the key defaults to None.

        Returns:
            str | None: The path to the generated audio file, or None if the output is invalid.
        """

    def text_to_speech(self, text_to_convert: str) -> tuple[gr.Audio | None, str | None]:
        """
        Converts text to speech by passing the text through the agent and postprocessing steps.
        If models has not been initialized, only a text hint is returned.

        Args:
            text_to_convert (str): The text to be converted to speech.

        Returns:
            tuple: Updates for audio_generated and status_msg.

        Raises:
            gr.Error: If the speech generation fails.
        """
        if self.initialized_state:
            container = DataContainer(texts=[TextPacket(content=text_to_convert)])
            output_container = self.agent(container)
            audio_path = self._postprocess_output(output_container, self.generic_key_or_base_path)
            if audio_path:
                return gr.Audio(audio_path, visible=True), None
            raise gr.Error("Unable to generate speech")
        return None, "#### Model not ready! Please wait..."

    @staticmethod
    def update_status_msg() -> str:
        """Updates status_text to indicate that the model is ready."""
        return gr.Markdown(
            "#### Model ready. Click on the box the text you wish to convert to speech and submit to generate!"
        )

    def inner_tts_functionality(self) -> None:
        """
        Defines the inner functionality of the TTS app interface using Gradio components.
        """

        text_to_convert = gr.Textbox(
            submit_btn=True,
            label="Text to convert:",
            value="The Sinapsis platform aims to democratize artificial intelligence by offering "
            + "a flexible template system that ensures modularity and compatibility between models and tools widely "
            + "used by the community.",
        )
        status_msg = self.update_status_msg()

        audio_generated = gr.Audio(label="Audio generated:", visible=False)

        text_to_convert.submit(
            self.text_to_speech,
            inputs=[text_to_convert],
            outputs=[audio_generated, status_msg],
        )

    def app_interface(self):
        with gr.Blocks(css=css_header()) as tts_interface:
            add_logo_and_title(f"Sinapsis {self.framework} {self.task} demo")
            self.inner_tts_functionality()
        return tts_interface

    def launch(self, **kwargs) -> None:
        """Launches the Gradio app, optionally with authentication and custom options."""
        interface = self.app_interface()
        interface.launch(
            **kwargs,
        )


class TTSAppAudioFromPacket(BaseTTSApp):
    """
    A subclass of BaseTTSApp for implementing text-to-speech functionality extracting the audio path
    from the generic_data field of Containers.
    """

    def _postprocess_output(self, container: DataContainer, generic_key: str | None) -> str | None:
        """
        Postprocesses the output of the TTS agent to extract the audio file path.
        """
        _ = generic_key

        audio = container.audios[-1]
        audio_path = f"{audio.source}-{audio.id.split('-')[0]}"
        audio_path = f"{self.generic_key_or_base_path}/{audio_path}.wav"
        return audio_path


class TTSAppAudioFromGeneric(BaseTTSApp):
    """
    A subclass of BaseTTSApp for implementing text-to-speech functionality using ElevenLabs.

    This class overrides the abstract methods from BaseTTSApp to provide specific preprocessing
    and postprocessing steps for the ElevenLabs TTS application.
    """

    def _postprocess_output(self, container: DataContainer, generic_key: str | None) -> str | None:
        """
        Post-processes the output of the ElevenLabs TTS agent to extract the audio file path.

        This method checks the `generic_data` of the provided container to find the audio file path
        associated with the given `generic_key`. If the key is found and the audio path exists,
        it is returned. Otherwise, `None` is returned.

        Args:
            container (DataContainer): The container returned by the TTS agent containing the output
                                       data, including the audio file path stored under the `generic_key`.
            generic_key (str | None): An optional key used to retrieve the audio path from the `generic_data`
                                      of the container.

        Returns:
            str | None: The path to the generated audio file if the key exists and contains the audio path;
                        otherwise, None if no valid path is found.
        """
        _ = self
        audio_path = container.generic_data.get(generic_key, None)
        return audio_path[0] if audio_path else audio_path
