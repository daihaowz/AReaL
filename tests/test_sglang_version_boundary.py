# SPDX-License-Identifier: Apache-2.0

"""A CPU controller builds server arguments; the server checks its own runtime."""

import pytest

from areal.api.cli_args import SGLangConfig
from areal.v2.inference_service.sglang import launch_server


def test_sglang_controller_does_not_need_local_server_package(monkeypatch):
    monkeypatch.setattr(
        "areal.api.cli_args.pkg_version.is_version_greater_or_equal",
        lambda *_args: False,
    )
    args = SGLangConfig.build_args(
        SGLangConfig(model_path="local-model"), tp_size=1, base_gpu_id=0
    )
    assert args["model_path"] == "local-model"


def test_sglang_server_rejects_incompatible_local_version(monkeypatch):
    monkeypatch.setattr(
        launch_server.pkg_version, "is_version_greater_or_equal", lambda *_: False
    )
    with pytest.raises(RuntimeError, match="sglang>=0.5.10.post1"):
        launch_server.areal_launch_server(object())
