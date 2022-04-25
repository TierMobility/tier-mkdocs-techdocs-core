import unittest
import mkdocs.plugins as plugins
from .core import TechDocsCore
from jinja2 import Environment, PackageLoader, select_autoescape
import json
import os


class DummyTechDocsCorePlugin(plugins.BasePlugin):
    pass


class TestTechDocsCoreConfig(unittest.TestCase):
    def setUp(self):
        self.techdocscore = TechDocsCore()
        self.plugin_collection = plugins.PluginCollection()
        plugin = DummyTechDocsCorePlugin()
        self.plugin_collection["tier-techdocs-core"] = plugin
        self.mkdocs_yaml_config = {"plugins": self.plugin_collection}

    def test_removes_techdocs_core_plugin_from_config(self):
        final_config = self.techdocscore.on_config(self.mkdocs_yaml_config)
        self.assertTrue("techdocs-core" not in final_config["plugins"])

    def test_merge_default_config_and_user_config(self):
        self.mkdocs_yaml_config["markdown_extension"] = []
        self.mkdocs_yaml_config["mdx_configs"] = {}
        self.mkdocs_yaml_config["markdown_extension"].append(["toc"])
        self.mkdocs_yaml_config["mdx_configs"]["toc"] = {"toc_depth": 3}
        final_config = self.techdocscore.on_config(self.mkdocs_yaml_config)
        self.assertTrue("toc" in final_config["mdx_configs"])
        self.assertTrue("permalink" in final_config["mdx_configs"]["toc"])
        self.assertTrue("toc_depth" in final_config["mdx_configs"]["toc"])
        self.assertTrue("mdx_truly_sane_lists" in final_config["markdown_extensions"])

    def test_override_default_config_with_user_config(self):
        self.mkdocs_yaml_config["markdown_extension"] = []
        self.mkdocs_yaml_config["mdx_configs"] = {}
        self.mkdocs_yaml_config["markdown_extension"].append(["toc"])
        self.mkdocs_yaml_config["mdx_configs"]["toc"] = {"permalink": False}
        final_config = self.techdocscore.on_config(self.mkdocs_yaml_config)
        self.assertTrue("toc" in final_config["mdx_configs"])
        self.assertTrue("permalink" in final_config["mdx_configs"]["toc"])
        self.assertFalse(final_config["mdx_configs"]["toc"]["permalink"])
        self.assertTrue("mdx_truly_sane_lists" in final_config["markdown_extensions"])

    def test_template_renders__multiline_value_as_valid_json(self):
        self.techdocscore.on_config(self.mkdocs_yaml_config)
        env = Environment(
            loader=PackageLoader("test", self.techdocscore.tmp_dir_techdocs_theme.name),
            autoescape=select_autoescape(),
        )
        template = env.get_template("techdocs_metadata.json")
        config = {
            "site_name": "my site",
            "site_description": "my very\nlong\nsite\ndescription",
        }
        rendered = template.render(config=config)
        as_json = json.loads(rendered)
        self.assertEquals(config, as_json)

    def test_kroki_plugin_reads_from_env(self):
        orig_kroki_server_url = os.environ.get("KROKI_SERVER_URL")
        orig_kroki_download_images = os.environ.get("KROKI_DOWNLOAD_IMAGES")
        test_url = "https://test-kroki.com"
        os.environ["KROKI_SERVER_URL"] = test_url
        os.environ["KROKI_DOWNLOAD_IMAGES"] = "1"
        config = self.techdocscore.on_config(self.mkdocs_yaml_config)
        self.assertTrue("kroki" in config["plugins"])
        self.assertEqual(config["plugins"]["kroki"].config["ServerURL"], test_url)
        self.assertEqual(config["plugins"]["kroki"].config["DownloadImages"], True)

    def test_search_plugin_modified_defaults(self):
        config = self.techdocscore.on_config(self.mkdocs_yaml_config)
        self.assertTrue("search" in config["plugins"])
        self.assertEqual(config["plugins"]["search"].config["prebuild_index"], True)
        self.assertEqual(config["plugins"]["search"].config["indexing"], "full")