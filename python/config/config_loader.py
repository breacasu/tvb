#!/usr/bin/env python3
import configparser
import logging
import os
import sys

CONFIG_FILENAME = 'tvb-config.ini'
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".m4v", ".mpg", ".mpeg", ".wmv"}


class TVBConfig:
    def __init__(self, config_path=None):
        # Existing user configs may contain an older preset followed by the
        # active replacement. ConfigParser's last-value behavior preserves
        # that established editing workflow.
        self.config = configparser.ConfigParser(strict=False)
        self._loaded_path = None
        self._load(config_path)

    def _load(self, config_path=None):
        search_paths = []
        if config_path:
            search_paths.append(config_path)

        env_path = os.environ.get('TVB_CONFIG_PATH')
        if env_path:
            search_paths.append(env_path)

        try:
            alt_path = os.path.join(os.path.dirname(__file__), '..', CONFIG_FILENAME)
            search_paths.append(os.path.abspath(alt_path))
        except NameError:
            pass
        search_paths.append(CONFIG_FILENAME)

        for path in search_paths:
            if path and os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                cleaned = self._strip_inline_comments(content)
                self.config.read_string(cleaned)
                self._loaded_path = path
                logging.info(f"Loaded config from: {path}")
                return

        logging.warning(f"No config file found, using defaults")

    def _strip_inline_comments(self, content):
        import re as _re
        result = []
        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith(';'):
                result.append(line)
                continue
            if '=' in stripped:
                stripped_no_comment = _re.sub(r'\s+#.*$|\s+;.*$', '', stripped)
                if stripped_no_comment != stripped:
                    indent = line[:len(line) - len(line.lstrip())]
                    result.append(indent + stripped_no_comment.rstrip())
                else:
                    result.append(line)
            else:
                result.append(line)
        return '\n'.join(result)

    @property
    def loaded_path(self):
        return self._loaded_path

    def get_format_params(self, format_type):
        if format_type in {'movie', 'tvshow', 'custom'}:
            return self.config.get(format_type, 'parameter', fallback='')
        return self.config.get('default', 'parameter', fallback='')

    def get_preview_params(self):
        return self.config.get('preview', 'parameter', fallback='--stop-at duration:30')

    def get_output_dir(self):
        val = self.config.get('default', 'outputdir', fallback='')
        val = val.strip("'\"")
        if not val or '/path/to/' in val:
            return './output'
        return val

    def get_bool(self, key, fallback=False):
        return self.config.getboolean('default', key, fallback=fallback)

    def get_int(self, key, fallback=100):
        return self.config.getint('default', key, fallback=fallback)

    def get_str(self, key, fallback=''):
        return self.config.get('default', key, fallback=fallback)

    def get_localization(self):
        return self.config.get('default', 'localization', fallback='en_US')

    def get_tool_path(self, section, platform_key=None):
        if section in self.config:
            if platform_key and platform_key in self.config[section]:
                return self.config[section][platform_key]
        return None

    @property
    def preserve_atmos_audio(self):
        return self.get_bool('preserve_atmos_audio', fallback=False)

    @property
    def preserve_file_date(self):
        return self.get_bool('preserve_file_date', fallback=True)
