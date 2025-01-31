"""Utility functions for Let"s Encrypt plugin tests."""
import argparse
import copy
import contextlib
import os
import re
import shutil
import socket
import tarfile

from acme import jose
from acme import test_util
from letsencrypt import constants

from letsencrypt_compatibility_test import errors


_KEY_BASE = "rsa1024_key.pem"
KEY_PATH = test_util.vector_path(_KEY_BASE)
KEY = test_util.load_pyopenssl_private_key(_KEY_BASE)
JWK = jose.JWKRSA(key=test_util.load_rsa_private_key(_KEY_BASE))
IP_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def create_le_config(parent_dir):
    """Sets up LE dirs in parent_dir and returns the config dict"""
    config = copy.deepcopy(constants.CLI_DEFAULTS)

    le_dir = os.path.join(parent_dir, "letsencrypt")
    config["config_dir"] = os.path.join(le_dir, "config")
    config["work_dir"] = os.path.join(le_dir, "work")
    config["logs_dir"] = os.path.join(le_dir, "logs_dir")
    os.makedirs(config["config_dir"])
    os.mkdir(config["work_dir"])
    os.mkdir(config["logs_dir"])

    config["domains"] = None

    return argparse.Namespace(**config)  # pylint: disable=star-args


def extract_configs(configs, parent_dir):
    """Extracts configs to a new dir under parent_dir and returns it"""
    config_dir = os.path.join(parent_dir, "configs")

    if os.path.isdir(configs):
        shutil.copytree(configs, config_dir, symlinks=True)
    elif tarfile.is_tarfile(configs):
        with tarfile.open(configs, "r") as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, config_dir)
    else:
        raise errors.Error("Unknown configurations file type")

    return config_dir


def get_two_free_ports():
    """Returns two free ports to use for the tests"""
    with contextlib.closing(socket.socket()) as sock1:
        with contextlib.closing(socket.socket()) as sock2:
            sock1.bind(("", 0))
            sock2.bind(("", 0))

            return sock1.getsockname()[1], sock2.getsockname()[1]
