##
# @file   Params.py
# @author Yibo Lin
# @date   Apr 2018
# @brief  User parameters
#

import hashlib
import json
import os
from ast import literal_eval
from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Union

import yaml
from multimethod import multimethod


class Config(dict):
    def __getattr__(self, key: str) -> Any:
        if key not in self:
            d = self
            ## try hierarchical access
            keys = key.split(".")
            for k in keys:
                if k not in d:
                    raise AttributeError(key)
                d = d[k]
            return d
        else:
            return self[key]

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]

    def load(self, fpath: str, *, recursive: bool = False) -> None:
        if not os.path.exists(fpath):
            raise FileNotFoundError(fpath)
        fpaths = [fpath]
        if recursive:
            while fpath:
                fpath = os.path.dirname(fpath)
                for fname in ["default.yaml", "default.yml"]:
                    fpaths.append(os.path.join(fpath, fname))
        for fpath in reversed(fpaths):
            if os.path.exists(fpath):
                with open(fpath, "r") as f:
                    cfg_dict = yaml.safe_load(f)
                self.update(cfg_dict)

    def reload(self, fpath: str, *, recursive: bool = False) -> None:
        self.clear()
        self.load(fpath, recursive=recursive)

    @multimethod
    def update(self, other: Dict) -> None:
        for key, value in other.items():
            if isinstance(value, dict):
                if key not in self or not isinstance(self[key], Config):
                    self[key] = Config()
                self[key].update(value)
            else:
                self[key] = value

    @multimethod
    def update(self, opts: Union[List, Tuple]) -> None:
        index = 0
        while index < len(opts):
            opt = opts[index]
            if opt.startswith("--"):
                opt = opt[2:]
            if "=" in opt:
                key, value = opt.split("=", 1)
                index += 1
            else:
                key, value = opt, opts[index + 1]
                index += 2
            current = self
            subkeys = key.split(".")
            try:
                value = literal_eval(value)
            except:
                pass
            for subkey in subkeys[:-1]:
                current = current.setdefault(subkey, Config())
            current[subkeys[-1]] = value

    def dict(self) -> Dict[str, Any]:
        configs = dict()
        for key, value in self.items():
            if isinstance(value, Config):
                value = value.dict()
            configs[key] = value
        return configs

    def flat_dict(self) -> Dict[str, Any]:
        def _flatten_dict(dd, separator: str = "_", prefix: str = ""):
            return (
                {
                    prefix + separator + k if prefix else k: v
                    for kk, vv in dd.items()
                    for k, v in _flatten_dict(vv, separator, kk).items()
                }
                if isinstance(dd, dict)
                else {prefix: dd}
            )

        return _flatten_dict(self.dict(), separator=".")

    def hash(self) -> str:
        buffer = json.dumps(self.dict(), sort_keys=True)
        return hashlib.sha256(buffer.encode()).hexdigest()

    def dump_to_yml(self, path: str) -> None:
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f)

    def __str__(self) -> str:
        texts = []
        for key, value in self.items():
            if isinstance(value, Config):
                seperator = "\n"
            else:
                seperator = " "

            text = str(key) + ":" + seperator + str(value)
            lines = text.split("\n")
            for k, line in enumerate(lines[1:]):
                lines[k + 1] = (" " * 2) + line
            texts.extend(lines)
        return "\n".join(texts)


class Params:
    """
    @brief Parameter class
    """
    def __init__(self):
        """
        @brief initialization
        """
        filename = os.path.join(os.path.dirname(__file__), 'params.json')
        self.__dict__ = {}
        params_dict = {}
        with open(filename, "r") as f:
            params_dict = json.load(f, object_pairs_hook=OrderedDict)
        for key, value in params_dict.items():
            if 'default' in value: 
                self.__dict__[key] = value['default']
            else:
                self.__dict__[key] = None
        self.__dict__['params_dict'] = params_dict

    def printWelcome(self):
        """
        @brief print welcome message
        """
        content = """\
========================================================
                     PICPlace Apollo
            Hongjian Zhou (hzhou144@asu.edu)
         Jiaqi Gu (https://scopex-asu.github.io)
========================================================"""
        print(content, flush=True)

    def printHelp(self):
        """
        @brief print help message for JSON parameters
        """
        content = self.toMarkdownTable()
        print(content)

    def toMarkdownTable(self):
        """
        @brief convert to markdown table 
        """
        key_length = len('JSON Parameter')
        key_length_map = []
        default_length = len('Default')
        default_length_map = []
        description_length = len('Description')
        description_length_map = []

        def getDefaultColumn(key, value):
            flag = isinstance(value['default'], str)
            if flag and not value['default'] and 'required' in value: 
                return value['required']
            else:
                return value['default']

        for key, value in self.params_dict.items():
            key_length_map.append(len(key))
            default_length_map.append(len(str(getDefaultColumn(key, value))))
            description_length_map.append(len(value['descripton']))
            key_length = max(key_length, key_length_map[-1])
            default_length = max(default_length, default_length_map[-1])
            description_length = max(description_length, description_length_map[-1])

        content = "| %s %s| %s %s| %s %s|\n" % (
                'JSON Parameter', 
                " " * (key_length - len('JSON Parameter') + 1), 
                'Default', 
                " " * (default_length - len('Default') + 1), 
                'Description', 
                " " * (description_length - len('Description') + 1)
                )
        content += "| %s | %s | %s |\n" % (
                "-" * (key_length + 1), 
                "-" * (default_length + 1), 
                "-" * (description_length + 1)
                )
        count = 0
        for key, value in self.params_dict.items():
            content += "| %s %s| %s %s| %s %s|\n" % (
                    key, 
                    " " * (key_length - key_length_map[count] + 1), 
                    str(getDefaultColumn(key, value)), 
                    " " * (default_length - default_length_map[count] + 1), 
                    value['descripton'], 
                    " " * (description_length - description_length_map[count] + 1)
                    )
            count += 1
        return content 

    def toJson(self):
        """
        @brief convert to json
        """
        data = {}
        for key, value in self.__dict__.items():
            if key != 'params_dict': 
                data[key] = value
        return data

    def fromJson(self, data):
        """
        @brief load form json
        """
        for key, value in data.items(): 
            self.__dict__[key] = value

    def dump(self, filename):
        """
        @brief dump to json file
        """
        with open(filename, 'w') as f:
            json.dump(self.toJson(), f)

    def load(self, filename):
        """
        @brief load from json file
        """
        with open(filename, 'r') as f:
            self.fromJson(json.load(f))

    def __str__(self):
        """
        @brief string
        """
        return str(self.toJson())

    def __repr__(self):
        """
        @brief print
        """
        return self.__str__()

    def design_name(self):
        """
        @brief speculate the design name for dumping out intermediate solutions 
        """
        if self.aux_input: 
            design_name = os.path.basename(self.aux_input).replace(".aux", "").replace(".AUX", "")
        elif self.verilog_input:
            design_name = os.path.basename(self.verilog_input).replace(".v", "").replace(".V", "")
        elif self.def_input: 
            design_name = os.path.basename(self.def_input).replace(".def", "").replace(".DEF", "")
        elif self.yaml_input:
            design_name = os.path.basename(self.yaml_input[0]).replace(".yml", "").replace(".YML", "")
        else:
            raise NotImplementedError("Unsupported input format")
        return design_name 

    def solution_file_suffix(self): 
        """
        @brief speculate placement solution file suffix 
        """
        if self.def_input is not None and os.path.exists(self.def_input): # LEF/DEF 
            return "def"
        elif self.yaml_input is not None and os.path.exists(self.yaml_input[0]):
            return "yml"
        else: # Bookshelf
            return "pl"
