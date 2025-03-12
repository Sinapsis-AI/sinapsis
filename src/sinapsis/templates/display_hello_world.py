# -*- coding: utf-8 -*-
"""Example Display Hello World Sinapsis template."""

from sinapsis_core.data_containers.data_packet import DataContainer
from sinapsis_core.template_base import Template


class DisplayHelloWorld(Template):
    """
    This template simply logs all the text packets received in a data container.
    It is meant to be used for illustration purposes and in combination with
    HelloWorld template.
    """

    def execute(self, container: DataContainer) -> DataContainer:
        for text_packet in container.texts:
            print(f"\n{text_packet.content}\n")  # noqa: T201

        return container
