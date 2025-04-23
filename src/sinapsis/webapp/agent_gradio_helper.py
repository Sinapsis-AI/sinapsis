# -*- coding: utf-8 -*-
import os
from typing import Any

import gradio as gr
from sinapsis_core.cli.run_agent_from_config import generic_agent_builder
from sinapsis_core.utils.env_var_keys import AGENT_CONFIG_PATH

from sinapsis.webapp.agent_webapp_utils import infer_image

SINAPSIS_WEBAPP_ROOT_FOLDER = os.getenv("SINAPSIS_WEBAPP_ROOT_FOLDER", "")
SINAPSIS_WEBAPP_PATH = os.path.dirname(os.path.abspath(__file__))


def lambda_init_agent(infer_func: Any, config_file: str) -> Any:
    """
    Method to start the agent and run the agent on a single image
    Args:
        infer_func (Any): method to run inference
        config_file (str): Configuration of the agent
    Returns:
        the final data container after running the agent
    """
    config_path = AGENT_CONFIG_PATH or os.path.join(
        SINAPSIS_WEBAPP_ROOT_FOLDER,
        config_file,
    )
    agent = generic_agent_builder(config_path)
    return lambda image: infer_func(agent, image)


def init_image_inference(
    config_path: str,
    title: str | None = None,
    stream: bool = False,
    image_input: gr.Image | None = gr.Image,
    app_message: str | None = None,
    examples: list[str] | None = None,
):
    """
    Method to perform inference on the input from gradio
    Args:
        config_path (str): path to config file for the agent
        title (str) : title of the gradio app
        stream (bool) : Whether to consume a single image (False) or a video (True)
        image_input (gr.Image | None): Whether the app takes an input image or not
        app_message (str | None): The message that shows up in the interface when starting it.
        examples (list | None): Adds example images to the gradio app
    """
    input_sources = ["webcam"]
    if not stream:
        input_sources.append("upload")
    fn = lambda_init_agent(infer_image, config_path)
    if image_input:
        image_input = [gr.Image(sources=input_sources, streaming=stream)]

    live_interface = gr.Interface(
        fn,
        inputs=image_input,
        outputs=gr.Image(type="pil"),
        live=True,
        title=title,
        flagging_mode="never",
        article=app_message,
        examples=examples,
    )
    return live_interface


def css_header() -> str:
    """Adds a css header for sinapsis logo and title of the app"""
    return """#sinapsis-logo {
            background-color: transparent;
            border: none;
            border-color: transparent;
        }
        #title {
            font-size: 100px;
            font-weight: bold;
            color: #333333;
            text-align: center;
            margin-bottom: 10px;
        }
       .primary {
        background-color: #004aad !important;
        opacity: 0.8 !important;
        color: white !important;
        border: 2px solid #004aad !important;
        }
        .secondary {
        background-color: #38b6ff !important;
        opacity: 0.8 !important;
        color: white !important;
        border: 2px solid #38b6ff !important;
        }
    #finish-chatbot-btn {
        background-color: blue !important;
        color: white !important;
        border: 2px solid black !important;
    }
    .color-primary.svelte-s8feoe.svelte-s8feoe {
  fill: #004aad;
  stroke: #004aad;
  color: #004aad;
}
    """


css = css_header()


def add_logo_and_title(page_title: str | None = None) -> None:
    """Method to create the header for the gradio apps
    Args:
        page_title (str): title of the page in gradio
    """
    logo_path = "https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/logo.png?raw=true"
    with gr.Row():
        gr.Image(
            logo_path,
            elem_id="sinapsis-logo",
            height=50,
            show_label=False,
            show_download_button=False,
            show_fullscreen_button=False,
            scale=1,
        )

        gr.Markdown(f"# {page_title}", elem_id="title")
        gr.Markdown("")
