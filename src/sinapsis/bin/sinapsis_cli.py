# -*- coding: utf-8 -*-
from sinapsis_core.cli.arg_parser import args_parser
from sinapsis_core.cli.display_template_info import display_template_info
from sinapsis_core.cli.run_agent_from_config import run_agent_from_config

import sinapsis.templates as templates


def welcome_msg():
    print("Welcome to Sinapsis CLI. Please run 'sinapsis -h' to obtain information about available commands.")  # noqa: T201


def main():
    args = args_parser()
    match args.action:
        case "run":
            run_agent_from_config(args.agent_config, args.enable_profiler)
        case "info":
            display_template_info(args, templates)
        case _:
            welcome_msg()


if __name__ == "__main__":
    main()
