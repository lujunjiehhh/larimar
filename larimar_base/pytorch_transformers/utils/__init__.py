#!/usr/bin/env python
# coding=utf-8

# Copyright 2021 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from huggingface_hub import get_full_repo_name  # for backward compatibility
from packaging import version
from transformers.utils.import_utils import _is_package_available

from .. import __version__
from .constants import IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD, IMAGENET_STANDARD_MEAN, IMAGENET_STANDARD_STD
from .doc import (
    add_code_sample_docstrings,
    add_end_docstrings,
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    copy_func,
    replace_return_docstrings,
)
from .generic import (
    ContextManagers,
    ExplicitEnum,
    ModelOutput,
    PaddingStrategy,
    TensorType,
    add_model_info_to_auto_map,
    cached_property,
    can_return_loss,
    expand_dims,
    find_labels,
    flatten_dict,
    infer_framework,
    is_jax_tensor,
    is_numpy_array,
    is_tensor,
    is_tf_symbolic_tensor,
    is_tf_tensor,
    is_torch_device,
    is_torch_dtype,
    is_torch_tensor,
    reshape,
    squeeze,
    strtobool,
    tensor_size,
    to_numpy,
    to_py_obj,
    transpose,
    working_or_temp_dir,
)
import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import warnings
from collections import OrderedDict
from functools import lru_cache
from itertools import chain
from types import ModuleType
from typing import Any, Tuple, Union

from .hub import (
    CLOUDFRONT_DISTRIB_PREFIX,
    DISABLE_TELEMETRY,
    HF_MODULES_CACHE,
    HUGGINGFACE_CO_PREFIX,
    HUGGINGFACE_CO_RESOLVE_ENDPOINT,
    PYTORCH_PRETRAINED_BERT_CACHE,
    PYTORCH_TRANSFORMERS_CACHE,
    S3_BUCKET_PREFIX,
    TRANSFORMERS_CACHE,
    TRANSFORMERS_DYNAMIC_MODULE_NAME,
    EntryNotFoundError,
    PushInProgress,
    PushToHubMixin,
    RepositoryNotFoundError,
    RevisionNotFoundError,
    cached_file,
    default_cache_path,
    define_sagemaker_information,
    download_url,
    extract_commit_hash,
    get_cached_models,
    get_file_from_repo,
    has_file,
    http_user_agent,
    is_offline_mode,
    is_remote_url,
    move_cache,
    send_example_telemetry,
    try_to_load_from_cache,
)
from .import_utils import (
    ENV_VARS_TRUE_AND_AUTO_VALUES,
    ENV_VARS_TRUE_VALUES,
    TORCH_FX_REQUIRED_VERSION,
    USE_JAX,
    USE_TF,
    USE_TORCH,
    DummyObject,
    OptionalDependencyNotAvailable,
    _LazyModule,
    ccl_version,
    direct_transformers_import,
    get_torch_version,
    is_accelerate_available,
    is_apex_available,
    is_auto_gptq_available,
    is_bitsandbytes_available,
    is_bs4_available,
    is_coloredlogs_available,
    is_cv2_available,
    is_cython_available,
    is_datasets_available,
    is_decord_available,
    is_detectron2_available,
    is_essentia_available,
    is_faiss_available,
    is_flash_attn_available,
    is_flax_available,
    is_fsdp_available,
    is_ftfy_available,
    is_in_notebook,
    is_ipex_available,
    is_jieba_available,
    is_jinja_available,
    is_jumanpp_available,
    is_kenlm_available,
    is_keras_nlp_available,
    is_levenshtein_available,
    is_librosa_available,
    is_natten_available,
    is_ninja_available,
    is_nltk_available,
    is_onnx_available,
    is_openai_available,
    is_optimum_available,
    is_pandas_available,
    is_peft_available,
    is_phonemizer_available,
    is_pretty_midi_available,
    is_protobuf_available,
    is_psutil_available,
    is_py3nvml_available,
    is_pyctcdecode_available,
    is_pytesseract_available,
    is_pytest_available,
    is_pytorch_quantization_available,
    is_rjieba_available,
    is_sacremoses_available,
    is_safetensors_available,
    is_sagemaker_dp_enabled,
    is_sagemaker_mp_enabled,
    is_scipy_available,
    is_sentencepiece_available,
    is_seqio_available,
    is_sklearn_available,
    is_soundfile_availble,
    is_spacy_available,
    is_speech_available,
    is_sudachi_available,
    is_tensorflow_probability_available,
    is_tensorflow_text_available,
    is_tf2onnx_available,
    is_tf_available,
    is_timm_available,
    is_tokenizers_available,
    is_torch_available,
    is_torch_bf16_available,
    is_torch_bf16_cpu_available,
    is_torch_bf16_gpu_available,
    is_torch_compile_available,
    is_torch_cuda_available,
    is_torch_fx_available,
    is_torch_fx_proxy,
    is_torch_mps_available,
    is_torch_neuroncore_available,
    is_torch_npu_available,
    is_torch_tensorrt_fx_available,
    is_torch_tf32_available,
    is_torch_tpu_available,
    is_torch_xpu_available,
    is_torchaudio_available,
    is_torchdistx_available,
    is_torchdynamo_available,
    is_torchvision_available,
    is_training_run_on_sagemaker,
    is_vision_available,
    requires_backends,
    torch_only_method, logger,
)
from .peft_utils import (
    ADAPTER_CONFIG_NAME,
    ADAPTER_SAFE_WEIGHTS_NAME,
    ADAPTER_WEIGHTS_NAME,
    check_peft_version,
    find_adapter_config_file,
)


WEIGHTS_NAME = "pytorch_model.bin"
WEIGHTS_INDEX_NAME = "pytorch_model.bin.index.json"
TF2_WEIGHTS_NAME = "tf_model.h5"
TF2_WEIGHTS_INDEX_NAME = "tf_model.h5.index.json"
TF_WEIGHTS_NAME = "model.ckpt"
FLAX_WEIGHTS_NAME = "flax_model.msgpack"
FLAX_WEIGHTS_INDEX_NAME = "flax_model.msgpack.index.json"
SAFE_WEIGHTS_NAME = "model.safetensors"
SAFE_WEIGHTS_INDEX_NAME = "model.safetensors.index.json"
CONFIG_NAME = "config.json"
FEATURE_EXTRACTOR_NAME = "preprocessor_config.json"
IMAGE_PROCESSOR_NAME = FEATURE_EXTRACTOR_NAME
GENERATION_CONFIG_NAME = "generation_config.json"
MODEL_CARD_NAME = "modelcard.json"

SENTENCEPIECE_UNDERLINE = "▁"
SPIECE_UNDERLINE = SENTENCEPIECE_UNDERLINE  # Kept for backward compatibility

MULTIPLE_CHOICE_DUMMY_INPUTS = [
    [[0, 1, 0, 1], [1, 0, 0, 1]]
] * 2  # Needs to have 0s and 1s only since XLM uses it for langs too.
DUMMY_INPUTS = [[7, 6, 0, 0, 1], [1, 2, 3, 0, 0], [0, 0, 0, 4, 5]]
DUMMY_MASK = [[1, 1, 1, 1, 1], [1, 1, 1, 0, 0], [0, 0, 0, 1, 1]]


def check_min_version(min_version):
    if version.parse(__version__) < version.parse(min_version):
        if "dev" in min_version:
            error_message = (
                "This example requires a source install from HuggingFace Transformers (see "
                "`https://huggingface.co/docs/transformers/installation#install-from-source`),"
            )
        else:
            error_message = f"This example requires a minimum version of {min_version},"
        error_message += f" but the version found is {__version__}.\n"
        raise ImportError(
            error_message
            + "Check out https://github.com/huggingface/transformers/tree/main/examples#important-note for the examples corresponding to other "
            "versions of HuggingFace Transformers."
        )
def is_flash_attn_2_available():
    if not is_torch_available():
        return False

    if not _is_package_available("flash_attn"):
        return False

    # Let's add an extra check to see if cuda is available
    import torch

    if not torch.cuda.is_available():
        return False

    if torch.version.cuda:
        return version.parse(importlib.metadata.version("flash_attn")) >= version.parse("2.1.0")
    elif torch.version.hip:
        # TODO: Bump the requirement to 2.1.0 once released in https://github.com/ROCmSoftwarePlatform/flash-attention
        return version.parse(importlib.metadata.version("flash_attn")) >= version.parse("2.0.4")
    else:
        return False


def is_flash_attn_greater_or_equal_2_10():
    if not _is_package_available("flash_attn"):
        return False

    return version.parse(importlib.metadata.version("flash_attn")) >= version.parse("2.1.0")


def is_flash_attn_available():
    logger.warning(
        "Using `is_flash_attn_available` is deprecated and will be removed in v4.38. "
        "Please use `is_flash_attn_2_available` instead."
    )
    return is_flash_attn_2_available()