"""
 * Copyright 2020 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

import tempfile
import logging
import os
from mkdocs.plugins import BasePlugin
from mkdocs.theme import Theme
from mkdocs.utils import warning_filter
from mkdocs.contrib.search import SearchPlugin
from mkdocs_monorepo_plugin.plugin import MonorepoPlugin
from kroki.plugin import KrokiPlugin
from pymdownx.emoji import to_svg

log = logging.getLogger(__name__)
log.addFilter(warning_filter)

TECHDOCS_DEFAULT_THEME = "material"


class TechDocsCore(BasePlugin):
    def __init__(self):
        # This directory will be removed automatically once the docs are built
        # MkDocs needs a directory for the theme with the `techdocs_metadata.json` file
        self.tmp_dir_techdocs_theme = tempfile.TemporaryDirectory()

    def on_config(self, config):
        with open(
            os.path.join(self.tmp_dir_techdocs_theme.name, "techdocs_metadata.json"),
            "w+",
        ) as fp:
            fp.write(
                '{{ {"site_name": (config.site_name | string), '
                '"site_description": (config.site_description | string)} | tojson }}'
            )

        mdx_configs_override = {}
        if "mdx_configs" in config:
            mdx_configs_override = config["mdx_configs"].copy()

        # Theme
        if config["theme"].name != TECHDOCS_DEFAULT_THEME:
            config["theme"] = Theme(name=TECHDOCS_DEFAULT_THEME)
        elif config["theme"].name == TECHDOCS_DEFAULT_THEME:
            log.info(
                "[mkdocs-techdocs-core] Overridden '%s' theme settings in use",
                TECHDOCS_DEFAULT_THEME,
            )

        config["theme"].static_templates.update({"techdocs_metadata.json"})
        config["theme"].dirs.append(self.tmp_dir_techdocs_theme.name)

        # Plugins
        del config["plugins"]["tier-techdocs-core"]

        search_plugin = SearchPlugin()
        search_plugin.load_config({"prebuild_index": True, "indexing": "full"})
        monorepo_plugin = MonorepoPlugin()
        monorepo_plugin.load_config({})

        kroki_server_url = os.environ.get("KROKI_SERVER_URL", "https://kroki.io")
        kroki_download_images = os.environ.get(
            "KROKI_DOWNLOAD_IMAGES", "0"
        ).lower() in ("true", "1")
        kroki_plugin = KrokiPlugin()
        kroki_plugin.load_config(
            {"ServerURL": kroki_server_url, "DownloadImages": kroki_download_images}
        )

        config["plugins"]["search"] = search_plugin
        config["plugins"]["monorepo"] = monorepo_plugin
        config["plugins"]["kroki"] = kroki_plugin

        # Markdown Extensions
        if "markdown_extensions" not in config:
            config["markdown_extensions"] = []

        if "mdx_configs" not in config:
            config["mdx_configs"] = {}

        config["markdown_extensions"].append("admonition")
        config["markdown_extensions"].append("toc")
        config["mdx_configs"]["toc"] = {
            "permalink": True,
        }

        config["markdown_extensions"].append("pymdownx.caret")
        config["markdown_extensions"].append("pymdownx.critic")
        config["markdown_extensions"].append("pymdownx.details")
        config["markdown_extensions"].append("pymdownx.emoji")
        config["mdx_configs"]["pymdownx.emoji"] = {"emoji_generator": to_svg}
        config["markdown_extensions"].append("pymdownx.inlinehilite")
        config["markdown_extensions"].append("pymdownx.magiclink")
        config["markdown_extensions"].append("pymdownx.mark")
        config["markdown_extensions"].append("pymdownx.smartsymbols")
        config["markdown_extensions"].append("pymdownx.superfences")
        config["markdown_extensions"].append("pymdownx.highlight")
        config["mdx_configs"]["pymdownx.highlight"] = {
            "linenums": True,
            "pygments_lang_class": True,
        }
        config["markdown_extensions"].append("pymdownx.extra")
        config["mdx_configs"]["pymdownx.betterem"] = {
            "smart_enable": "all",
        }
        config["markdown_extensions"].append("pymdownx.tabbed")
        config["mdx_configs"]["pymdownx.tabbed"] = {
            "alternate_style": True,
        }
        config["markdown_extensions"].append("pymdownx.tasklist")
        config["mdx_configs"]["pymdownx.tasklist"] = {
            "custom_checkbox": True,
        }
        config["markdown_extensions"].append("pymdownx.tilde")

        config["markdown_extensions"].append("markdown_inline_graphviz")
        config["markdown_extensions"].append("plantuml_markdown")
        config["markdown_extensions"].append("mdx_truly_sane_lists")

        # merge config supplied by user in the mkdocs.yml
        for key in mdx_configs_override:
            if key in config["mdx_configs"]:
                default_config = config["mdx_configs"][key]
                override_config = mdx_configs_override[key]
                default_config.update(override_config)

        return config
