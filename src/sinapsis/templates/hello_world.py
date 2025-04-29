# -*- coding: utf-8 -*-
"""Example Hello World Sinapsis template."""

from sinapsis_core.data_containers.data_packet import DataContainer, TextPacket
from sinapsis_core.template_base import Template
from sinapsis_core.template_base.base_models import TemplateAttributes, TemplateAttributeType


class HelloWorld(Template):
    """
    This template simply adds a text packet to our data container. The data container
    is `sent` to any subsequent templates in our Agent.
    """

    class AttributesBaseModel(TemplateAttributes):  # type:ignore
        """
        AttributesBaseModel is used to allow users to set attributes for a given template.

        All attribute classes are pydantic BaseModels so they get validated upon
        initialization. All pydantic BaseModel features are supported.

        In this example we will use two attributes to illustrate how these work.
        """

        display_text: str = "Hello World"

    def __init__(self, attributes: TemplateAttributeType) -> None:
        """
        In this example we don't really need the init as we're not doing anything in it,
        but we will leave it here for illustration purposes

        Args:
            attributes (TemplateAttributeType): attributes to set as per the AttributesBaseModel
                                         BaseModel above.
        """
        super().__init__(attributes)

    def execute(self, container: DataContainer) -> DataContainer:
        """
        Append a text packet to the data container with some user defined text.

        Args:
            container (DataContainer): Input data container. If this is our first Template
                                        in the Agent then it's always empty.

        Returns:
            container (DataContainer): The modified data container. A text packet is appended to the 'texts' field.
        """
        text_packet = TextPacket(content=self.attributes.display_text)
        text_packet.source = self.instance_name
        container.texts.append(text_packet)

        return container
