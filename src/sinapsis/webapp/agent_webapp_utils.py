# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any

from sinapsis_core.agent import Agent
from sinapsis_core.cli.run_agent_from_config import AgentMode
from sinapsis_core.data_containers.data_packet import DataContainer, ImagePacket
from sinapsis_core.utils.logging_utils import sinapsis_logger


def infer_image(agent: Agent, image: Any) -> Any:
    """Method used in apps that require an image input
    Args:
        agent (Agent): Agent instance
        image (Any): input from the gradio/streamlit app
    Returns:
        the final image content after agent execution
    """
    if image is None:
        return None
    container = DataContainer()
    container.images = [
        ImagePacket(
            content=image,
            source="live_stream",
        )
    ]
    result_container = agent(container)
    return result_container.images[-1].content


def infer_video(agent: Agent, video: Any) -> Path:
    """Processes an input video using the CoTracker agent and returns the path to the output video.

    Args:
        agent (Agent): Agent instance
        video (Any): The input video file or path.

    Returns:
        Path: The file path to the processed video.
    """
    agent.update_template_attribute("VideoReaderCV2", "video_file_path", video)
    agent.reset_state()
    for _ in agent(None, AgentMode.GENERATOR):
        pass
    agent.topological_sort["VideoWriterCV2"].template_instance.video_writer_is_done()
    sinapsis_logger.debug("Finished processing video")
    path = agent.topological_sort["VideoWriterCV2"].metadata.attributes["destination_path"]

    return Path(path)
