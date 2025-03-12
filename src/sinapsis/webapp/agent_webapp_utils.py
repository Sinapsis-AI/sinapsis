# -*- coding: utf-8 -*-
from typing import Any

from sinapsis_core.agent import Agent
from sinapsis_core.data_containers.data_packet import DataContainer, ImagePacket


def infer_image(agent: Agent, image: Any) -> Any:
    """Method used in apps that require an image input
    Args:
        agent (Agent): Agent instance
        image (Any): input from the gradio/streamlit app
    Returns:
        the final image content after agent execution
    """

    container = DataContainer()
    container.images = [
        ImagePacket(
            content=image,
            source="live_stream",
        )
    ]
    result_container = agent(container)
    return result_container.images[-1].content
