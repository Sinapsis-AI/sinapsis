<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/logo.png?raw=true"
    alt="" width="300">
</a>
<br>
Sinapsis
<br>
</h1>

<h4 align="center">Build and manage AI workflows through modular and scalable Agents based on composite and reusable Templates.  </h4>

<p align="center">
<a href="#installation">⚙️ Installation</a> •
<a href="#quickstart">⚡ Quickstart</a> •
<a href="#features">🎯 Features</a> •
<a href="#examples">👀 Examples</a> •
<a href="#documentation">📙 Documentation</a> •
<a href="#packages">📚 Available sinapsis packages</a>
<a href="#packages">🔍 License</a>
</p>

<h4 align="center">
  <b>Welcome to Sinapsis!</b>
  The all-in-one AI-native platform that unifies the most powerful and innovative AI tools, from computer vision
  and NLP to GenAI, speech processing, time-series analysis, and beyond.  Whether you're building, experimenting, or
  deploying, Sinapsis empowers you to create seamless end-to-end workflows, unlocking new possibilities and
  accelerating AI-driven innovation like never before. Join us in shaping the future of AI!
</h4>

<h2 id="installation">⚙️ Installation</h2>
1. Clone the repository.

```bash
  git clone git@github.com:Sinapsis-ai/sinapsis.git
  cd sinapsis
```
> [!IMPORTANT]
> Sinapsis requires Python 3.10 or higher.
>

We strongly encourage the use of <code>uv</code>, although any other package manager should work too.
If you need to install <code>uv</code> please see the [official documentation](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).

<details>
<summary><strong><span style="font-size: 1.4em;">🐍 Install from PyPi </span></strong></summary>

2. Install using your favourite package manager.

Example with <code>uv</code>:
```bash
  uv pip install sinapsis
```
 or with raw <code>pip</code>:
```bash
  pip install sinapsis
```
</details>


<details>
<summary><strong><span style="font-size: 1.4em;">💻 Build from source with UV</span></strong></summary>

2. Create virtual environment and install dependencies:
```bash
  uv sync --frozen --all-extras
```
3. Activate the virtual environment:
```bash
  source .venv/bin/activate
```
4. Build and install the package:
```bash
  uv build && uv pip install dist/sinapsis-0.1.0-py3-none-any.whl
```
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">🐳 Build with Docker</span></strong></summary>


Sinapsis provides Docker images with all dependencies pre-configured. To build images:

2. run the following command
```bash
docker compose -f docker/compose.yaml build
```

This will create two docker images:
- **sinapsis:base**: Contains UV package manager, git with SSH support, and Python 3.10 environment.
- **sinapsis-nvidia:base**: Same as base plus CUDA 12.4.0 support for GPU acceleration.
</details>


<h2 id="quickstart">⚡ Quickstart</h2>

<details>
<summary><strong><span style="font-size: 1.4em;">CLI usage</span></strong></summary>

The Sinapsis CLI provides an easy way to run agents and get information about templates:

```bash
# Run an agent with a config file
sinapsis run config.yml

# Run an agent with profiler enabled
sinapsis run config.yml --enable-profiler

# List all available templates
sinapsis info --all-template-names

# Get detailed info about a specific template
sinapsis info --template TemplateName

# Get example config for a template
sinapsis info --example-template-config TemplateName

# Display info for all templates
sinapsis info --all
```
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">📖 Hello World Sinapsis</span></strong></summary>

**Create a config file my_test_agent.yml:**

You can also use the ones defined under the ```src/configs/``` folder
```yaml
agent:
  name: my_test_agent

templates:
- template_name: InputTemplate-1
  class_name: InputTemplate
  attributes: {}

- template_name: HelloWorld-1
  class_name: HelloWorld
  template_input: InputTemplate-1
  attributes:
    display_text: "Hello, this is my first template!"
```

**Run the agent:**
```bash
sinapsis run my_test_agent.yml
```

**Output**

```console
... | DEBUG |  my_test_agent:__instantiate_templates:105 - Initialized template: InputTemplate-1
... | DEBUG |  my_test_agent:__instantiate_templates:105 - Initialized template: HelloWorld-1
... | DEBUG |  my_test_agent:_log_agent_execution_order:119 - Execution Order
... | DEBUG |  my_test_agent:_log_agent_execution_order:122 - Order: <<0>>, template name: <<InputTemplate-1>>
... | DEBUG |  my_test_agent:_log_agent_execution_order:122 - Order: <<1>>, template name: <<HelloWorld-1>>
... | INFO |  my_test_agent:_lazy_init:63 - Agent and templates initialized
... | INFO |  my_test_agent:signal_block_if_needed:156 - Signaling block mode for HelloWorld-1 no: 2/2
... | INFO |  my_test_agent:all_templates_finished:192 - All templates returned finished, stopping execution...
... | DEBUG | .../run_agent_from_config.py:run_agent_from_config:41 - result: DataContainer(container_id=abc..., images=[], audios=[], texts=[TextPacket(content='Hello, this is my first template!', id='abc...', source='HelloWorld-1', modified_by_templates=['HelloWorld-1'], embedding=[], generic_data={}, annotations=None)], time_series=[], binary_data=[], generic_data={})

```
</details>

<h2 id="features">🎯 Key Features</h2>

<details>
<summary><strong><span style="font-size: 1.4em;">Agents</span></strong></summary>

- Declarative workflows
- Multiple execution modes:
  - Generator
  - Single execute
  - Continuous execution
- Sophisticated template orchestration:
  - Topological sorting of execution order
  - Parallel template execution
  - Execution blocking control
- Built-in profiling capabilities:
  - Execution time tracking
- State management:
  - Dynamic attribute updates
- Failure handling
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">Templates</span></strong></summary>

- Self-contained components
- Modular task-focused execution
- Eager or lazy evaluation
- Dynamic template definitions
- Composite templates
- SubAgents

</details>

<details>
<summary><strong><span style="font-size: 1.4em;">Data Containers</span></strong></summary>

- Universal data transport
- Domain agnostic design
- Native built-in support for images, audio, text, time series
- Multimodal data

</details>

<details>
<summary><strong><span style="font-size: 1.4em;">General</span></strong></summary>

- Data Validation and Type Safety through Pydantic
- YAML-based configuration files
</details>

<h2 id="examples">👀 Examples</h2>

You can find specific implementations of templates in:

* **Static Templates**
  * [Hello World Template](src/sinapsis/templates/hello_world.py)
  * [Sinapsis Video Readers](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_data_readers)

* **Dynamic Templates**
  * [Sinapsis LangChain](https://github.com/Sinapsis-ai/sinapsis-langchain)

<h2 id="documentation">📙 Documentation</h2>

Documentation is available on the [sinapsis website](https://docs.sinapsis.tech/docs)

Tutorials for different projects within sinapsis are available at [sinapsis tutorials page](https://docs.sinapsis.tech/tutorials)

<h2 id="packages">📚 Available sinapsis packages</h2>

The sinapsis framework contains a list of public packages with **Templates** covering a wide range of tasks,
including computer vision, time series, nlp, llm'. These packages include:
<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis data tools</span></strong></summary>


* [sinapsis-data-readers](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_data_readers): package with tools to handle the data reading, using different libraries to process images, videos, audios, etc.

* [sinapsis-data-writers](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_data_writers): package with tools to handle data writing, using different libraries to write in local environment images, audios, videos, etc.

* [sinapsis-data-visualization](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_data_visualization): package with data visualization and drawing tools.

* [sinapsis-generic-data-tools](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_generic_data_tools): package with generic tools for data handling; i.e., selection regions of interest, buffering of data, postprocessing of text, etc.

</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis langchain</span></strong></summary>

* [sinapsis-langchain-readers](https://github.com/Sinapsis-ai/sinapsis-langchain): package with document readers using the langchain library.
</details>
<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis image transforms</span></strong></summary>

* [sinapsis-image-transforms](https://github.com/Sinapsis-ai/sinapsis-image-transforms): package with templates using the Albumentations library to perform image transformations.
</details>


<h2 id="license">🔍 License</h2>

This project is licensed under the AGPLv3 license, which encourages open collaboration and sharing. For more details, please refer to the [LICENSE](LICENSE) file.

For commercial use, please refer to our [official Sinapsis website](https://sinapsis.tech) for information on obtaining a commercial license.



