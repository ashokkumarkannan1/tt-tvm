from pybuda.tensor import to_tf_tensors
from pybuda.tvm_utils import flatten_inputs, flatten_structured_output
import torch

import numpy as np
import tvm
from tvm.ir.transform import Pass
import tvm.relay as relay
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import (
    convert_variables_to_constants_v2,
)
from tvm.contrib import graph_executor
from loguru import logger

from ctypes import c_void_p
import copy
import json

from collections import OrderedDict, MutableMapping
import pybuda

from json import JSONEncoder
import os
import subprocess
from os.path import exists as file_exists
import onnxruntime as ort
import onnx
import onnx.numpy_helper
import mxnet as mx
from tvm.relay.expr import Tuple
from tvm.relay.op.contrib.buda.buda import verify_tvm_compile

from jax.experimental import jax2tf
from jax.tools.jax_to_ir import tf_wrap_with_input_names
import collections
from transformers.utils.generic import ModelOutput
from tvm.contrib.pybuda_utils import (
    extract_framework_model_outputs, 
    extract_flatten_inputs, 
    construct_tvm_ir,
    extract_function_callnodes,
    trace_to_origin,
)
import hashlib

dev_json_graph = {"functions": {}, "graph" : "", "param_names": {}, "device" : "tt"}
cpu_json_graph = {"functions": {}, "graph" : "", "param_names": {}, "device" : "cpu"}

def retrieve_graph(json_graph, t):
    function_name = t[0]
    if function_name in json_graph["functions"]:
        return

    json_graph["functions"][function_name] = t[1]
    json_graph["param_names"][function_name] = t[2]

def join_graphs(json_graphs):
    json_graphs = [json.loads(graph) for graph in json_graphs]
    existing_graph = json_graphs[0]
    for graph in json_graphs[1:]:        
        num_new_nodes = len(existing_graph["nodes"])
        for node in graph["nodes"]:
            if "num_inputs" not in node["attrs"]:
                continue

            node["inputs"] = [[input_nid[0] + num_new_nodes, 0, 0] for input_nid in node["inputs"]]
            
        graph["heads"] = [[head[0] + num_new_nodes, 0, 0] for head in graph["heads"]]
        graph["arg_nodes"] = [arg_node + num_new_nodes for arg_node in graph["arg_nodes"]]
        num_node_rows = len(graph["node_row_ptr"])
        graph["node_row_ptr"] = [node_row_ptr + num_node_rows for node_row_ptr in graph["node_row_ptr"]]

        for key in graph.keys():
            existing_graph[key] = existing_graph[key] + graph[key]

    existing_graph = json.dumps(existing_graph)
    return existing_graph

@tvm.register_func
def retrieve_pybuda_json_graph(*args):
    t = tuple(args)
    global dev_json_graph
    retrieve_graph(dev_json_graph, t)

@tvm.register_func
def retrieve_pybuda_cpudevice_json_graph(*args):
    t = tuple(args)
    global cpu_json_graph
    retrieve_graph(cpu_json_graph, t)


def load_tvm_graph(inputs, module, compiler_cfg, graph_name, framework, output_names=None, path=None, verify_cfg=None):
    """
    Loads TVM graph ported to the PyBuda from other frameworks (TensorFlow, Pytorch). Can eather
    run whole compilation process from specific framework to the PyBuda graph representation, or
    skip this compilation process and load serialize TVM graph which is already ported to PyBuda
    by initial invocation.

    Parameters
    ----------
    inputs: Tuple[Tensor, ...]
        Input tensors

    module: Module(PyTorchModule or TFModule)
        Module that contains workload which can be assigned to a single device.

    compiler_cfg: CompilerConfig
        Compiler configurations

    output_names: List[str]
        Model output names to extract from Tensorflow -> TVM conversion. If None, the last node will be treated
        as model output node.

    path: str
        Path to onnx file on disk. This is used to verify TVM results vs. framework results.

    Returns
    -------
    Dictionary, OrderedDict, Tuple, Boolean
        TVM ported graph, Weights, Input tensors, Constant evaluation
    """
    if compiler_cfg.tvm_graph_store_path != "" and compiler_cfg.tvm_graph_load_path != "":
        logger.warning(f"TVM serialization logic will be skipped as both store and load paths are provided")

    json_graphs, flattened_inputs = compile_tvm_graph(inputs, module, compiler_cfg, graph_name=graph_name, output_names=output_names, path=path, verify_cfg=verify_cfg, framework=framework)
    
    flattened_pytorch_inputs, weights = format_tvm_graph_weights(flattened_inputs, module, compiler_cfg, framework=framework)

    serialize_and_store_tvm_graph(json_graphs, compiler_cfg)

    return json_graphs, flattened_pytorch_inputs, weights


def compile_tvm_graph(inputs, module, compiler_cfg, graph_name, output_names=None, path=None, verify_cfg=None, framework=None):
    """
    Compiles TVM graph ported to the PyBuda from other frameworks (TensorFlow, Pytorch). Can eather
    run whole compilation process or only load serilized TVM graph and thus increase test performance.

    Parameters
    ----------
    inputs: Tuple[Tensor, ...]
        Input tensors
    
    module: Module(PyTorchModule or TFModule)
        Module that contains workload which can be assigned to a single device

    compiler_cfg: CompilerConfig
        Compiler configurations

    output_names: List[str]
        Model output names to extract from Tensorflow -> TVM conversion. If None, the last node will be treated
        as model output node.

    path: str
        Path to onnx file on disk. This is used to verify TVM results vs. framework results.

    Returns
    -------
    Dictionary
        TVM ported graph
    """
    # clear out graphs before starting in case python session is ongoing
    global dev_json_graph
    global cpu_json_graph
    dev_json_graph = {"functions": {}, "graph" : "", "param_names": {}, "device" : "tt"}
    cpu_json_graph = {"functions": {}, "graph" : "", "param_names": {}, "device" : "cpu"}
  
    if framework == "pytorch":
        json_graphs, inputs = compile_pytorch_for_buda(module, *inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    elif framework == "tensorflow":
        # convert pytorch tensors to tf tensors
        tf_inputs = to_tf_tensors(inputs, force_float32=True)
        json_graphs, inputs = compile_tf_for_buda(module, *tf_inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    elif framework == "tf_graphdef":
        if len(inputs) > 0 and isinstance(inputs[0], torch.Tensor):
            tf_inputs = tuple(None if t is None else tf.convert_to_tensor(t.detach().numpy()) for t in inputs)
        else:
            tf_inputs = inputs
        json_graphs = compile_tf_graphdef_for_buda(module, *tf_inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, output_names=output_names)
    elif framework == "onnx":
        assert all([isinstance(x, torch.Tensor) for x in inputs])
        onnx_inputs = [x.detach().numpy() for x in inputs]
        json_graphs, _ = compile_onnx_for_buda(module, path, *onnx_inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    elif framework == "mxnet":
        assert all([isinstance(x, torch.Tensor) for x in inputs])
        mxnet_inputs = [mx.nd.array(x.detach().numpy()) for x in inputs]
        json_graphs = compile_mxnet_for_buda(module, *mxnet_inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    elif framework == "jax":
        tf_inputs = to_tf_tensors(inputs, force_float32=True)
        json_graphs, inputs = compile_jax_for_buda(module, *tf_inputs, graph_name=graph_name, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    else:
        raise RuntimeError(f"Unsupported module type {type(module)}")

    return json_graphs, inputs

def save_nid_to_input_idx(traced_model_inputs, json_graph):
    existing_graph = json.loads(json_graph["graph"])

    nid_to_input_idx = {}

    # reorder arg nodes to be inputs first, then parameters
    for i, arg_idx in enumerate(existing_graph["arg_nodes"]):
        name = existing_graph["nodes"][arg_idx]["name"]
        if name not in traced_model_inputs:
            continue

        nid_to_input_idx[arg_idx] = traced_model_inputs.index(name)

    json_graph["nid_to_input_idx"] = nid_to_input_idx


def get_func_output_origins(func_body, origins):

    model_output_origins = []
    if isinstance(func_body, relay.expr.Tuple):
        for output in func_body.fields:
            model_output_origins.append(trace_to_origin(output, origins))
    else:
        model_output_origins.append(trace_to_origin(func_body, origins))
    
    return model_output_origins

def add_passthrough_if_needed(first_json, second_json, third_json, partitioned_mod, input_names):
    first, second, third = first_json["graph"], second_json["graph"], third_json["graph"]

    second_name = list(second_json["functions"].keys())[0]

    gvars = partitioned_mod.get_global_vars()
    origins = list(partitioned_mod["main"].params)
    funcs = []
    for gvar in gvars:
        if isinstance(gvar.checked_type, relay.FuncType):
            funcs.append(gvar)

    # The list of 'origins' we want to trace to is either the output of a function or an argument to 'main'.
    # This is for the purpose of tracking which outputs of which functions to passthrough
    origins = origins + funcs

    # Determine which functions the outputs of the model originate from
    main_output_origins = get_func_output_origins(partitioned_mod["main"].body, origins)

    # get the second function using the name (the tt device module)
    funcs = extract_function_callnodes(partitioned_mod["main"], origins)
    second_func_idx = -1
    for i, func in enumerate(funcs):
        if func.op.name_hint == second_name:
            second_func_idx = i
    second_func = funcs[second_func_idx]

    # Find where the inputs to the second module originate, (will either be model inputs or outputs from first module)
    second_input_origins = [trace_to_origin(arg, origins) for arg in second_func.args]

    # Determine which outputs from the second module become model outputs. Needed for passthrough
    first_outputs_required = []
    second_outputs_required = []
    for output in main_output_origins:
        if second_name == output[0]:
            second_outputs_required.append(output)

    # Make sure everything that ends up in output is passed through to second
    second = json.loads(second)
    add_to_first = False
    if first != "":

        first_name = list(first_json["functions"].keys())[0]


        for output in main_output_origins:
            if first_name == output[0]:
                first_outputs_required.append(output)

        # Ensure that we are not adding a passthrough from first to second on a variable that is already being passed
        # This covers the case where an output from the first module is both an output of the model and consumed in the second module
        for inp in second_input_origins:
            if inp in first_outputs_required:
                first_outputs_required.remove(inp)

        add_to_first = True
        first = json.loads(first)
        # Generate new input nodes for second module
        first_output_jsons = []
        first_to_second_count = 0
        for output in first_outputs_required:
            first_output_jsons.append(copy.deepcopy(first['nodes'][first['heads'][output[1]][0]]))
            first_output_jsons[-1]['name'] = f'passthrough_first_to_second_{first_to_second_count}'
            first_output_jsons[-1]['op'] = 'input'
            first_to_second_count += 1

        needed_first = [[input_name == node["name"] for node in second["nodes"]].index(True) if any([input_name == node["name"] for node in second["nodes"]]) else -1 for input_name in input_names]

        if any([p >= 0 for p in needed_first]):
            for passthrough_node, name in zip(needed_first, input_names):
                if passthrough_node >= 0:
                    first["nodes"].append(second["nodes"][passthrough_node])
                    first["arg_nodes"].append(len(first["nodes"]) - 1)
                    first["heads"].append([len(first["nodes"]) - 1, 0, 0])


        # add passthrough from first to second
        for output in first_output_jsons:
            second['nodes'].append(output)
            second['arg_nodes'].append(len(second['nodes'])-1)
            second["heads"].append([len(second["nodes"]) - 1, 0, 0])


    if third != "":
        third = json.loads(third)

        needed_first_and_second = [[input_name == node["name"] for node in third["nodes"]].index(True) if any([input_name == node["name"] for node in third["nodes"]]) else -1 for input_name in input_names]

        if any([p >= 0 for p in needed_first_and_second]):
            for passthrough_node, name in zip(needed_first_and_second, input_names):
                if passthrough_node >= 0:
                    if add_to_first:
                        first["nodes"].append(third["nodes"][passthrough_node])
                        first["arg_nodes"].append(len(first["nodes"]) - 1)
                        first["heads"].append([len(first["nodes"]) - 1, 0, 0])

                    second["nodes"].append(third["nodes"][passthrough_node])
                    second["arg_nodes"].append(len(second["nodes"]) - 1)
                    second["heads"].append([len(second["nodes"]) - 1, 0, 0])

        # Create json nodes for model outputs generated in second module
        second_output_jsons = []
        second_to_third_count = 0
        for output in second_outputs_required:
            second_output_jsons.append(copy.deepcopy(second['nodes'][second['heads'][output[1]][0]]))
            second_output_jsons[-1]['name'] = f'passthrough_second_to_third_{second_to_third_count}'
            second_output_jsons[-1]['op'] = 'input'
            second_to_third_count += 1

        # Passthrough all outputs from first and second modules
        for output in first_output_jsons + second_output_jsons:
            third['nodes'].append(output)
            third['arg_nodes'].append(len(third['nodes'])-1)
            third["heads"].append([len(third["nodes"]) - 1, 0, 0])
            
    if add_to_first:
        first = json.dumps(first)
    second = json.dumps(second)
    if third != "":
        third = json.dumps(third)
    # import pdb; pdb.set_trace()
    return first, second, third


def extract_graphs(partitioned_mod, buda_params, input_names, param_name_lookup={}, graph_hash=""):
    mod = partitioned_mod["main"]
    main_graph = str(mod.astext())
    cpu_json_graph["hash"] = graph_hash
    dev_json_graph["hash"] = graph_hash
    cpu_functions = list(cpu_json_graph["functions"].keys())
    dev_functions = list(dev_json_graph["functions"].keys())
    all_functions = cpu_functions + dev_functions
    function_locations = {str(mod.astext()).find(function):function for function in all_functions}
    cpu_pre_functions = []
    device_functions = []
    cpu_post_functions = []
    sort_indices = sorted(function_locations)
    idx = 0
    while idx < len(function_locations) and "cpu" in function_locations[sort_indices[idx]]:
        cpu_pre_functions.append(function_locations[sort_indices[idx]])
        idx += 1
    while idx < len(function_locations) and "cpu" not in function_locations[sort_indices[idx]]:
        device_functions.append(function_locations[sort_indices[idx]])
        idx += 1
    while idx < len(function_locations) and "cpu" in function_locations[sort_indices[idx]]:
        cpu_post_functions.append(function_locations[sort_indices[idx]])
        idx += 1

    assert idx == len(function_locations)

    if len(cpu_pre_functions):
        graph = join_graphs([cpu_json_graph["functions"][function] for function in cpu_pre_functions])
        cpu_pre_json_graph = copy.deepcopy(cpu_json_graph)
        cpu_pre_json_graph["graph"] = graph

        # Only keep the pre function in the pre json
        functions_to_remove = []
        for function in cpu_pre_json_graph["functions"]:
            if function not in cpu_pre_functions:
                functions_to_remove.append(function)
        
        for func in functions_to_remove:
            del cpu_pre_json_graph["functions"][func]

        cpu_pre_json_graph["params"] = {}
        for function_name in buda_params.keys():
            if function_name in cpu_pre_functions:
                cpu_pre_json_graph["params"].update({name:v.numpy() for (k, v), name in zip(buda_params[function_name].items(), cpu_pre_json_graph["param_names"][function_name])})
    else:
        cpu_pre_json_graph = {"graph":""}
    
    dev_graph = join_graphs([dev_json_graph["functions"][function] for function in device_functions])
    dev_json_graph["graph"] = dev_graph

    dev_json_graph["params"] = {}
    for function_name in buda_params.keys():
        if function_name in dev_json_graph["param_names"]:
            dev_json_graph["params"].update({name:v.numpy() for (k, v), name in zip(buda_params[function_name].items(), dev_json_graph["param_names"][function_name])})

    if len(cpu_post_functions):
        graph = join_graphs([cpu_json_graph["functions"][function] for function in cpu_post_functions])
        cpu_post_json_graph = copy.deepcopy(cpu_json_graph)
        cpu_post_json_graph["graph"] = graph

        # Only keep the post function in the post json
        functions_to_remove = []
        for function in cpu_post_json_graph["functions"]:
            if function not in cpu_post_functions:
                functions_to_remove.append(function)
        
        for func in functions_to_remove:
            del cpu_post_json_graph["functions"][func]

        cpu_post_json_graph["params"] = {}
        for function_name in buda_params.keys():
            if function_name in cpu_pre_functions:
                cpu_post_json_graph["params"].update({name:v.numpy() for (k, v), name in zip(buda_params[function_name].items(), cpu_post_json_graph["param_names"][function_name])})
    else:
        cpu_post_json_graph = {"graph":""}
    
    cpu_pre_json_graph["graph"], dev_json_graph["graph"], cpu_post_json_graph["graph"] = add_passthrough_if_needed(
        cpu_pre_json_graph, dev_json_graph, cpu_post_json_graph, partitioned_mod, input_names
    )

    json_graphs = []
    if len(cpu_pre_functions):
        save_nid_to_input_idx(input_names, cpu_pre_json_graph) # Input order might not be preserved by TVM
        cpu_pre_json_graph["num_pybuda_inputs"] = len(input_names)
        json_graphs.append(copy.deepcopy(clean_names(json_graph=cpu_pre_json_graph, buda_params=buda_params, param_name_lookup=param_name_lookup)))
    else:
        save_nid_to_input_idx(input_names, dev_json_graph) # Input order might not be preserved by TVM
        dev_json_graph["num_pybuda_inputs"] = len(input_names)
        
    json_graphs.append(copy.deepcopy(clean_names(json_graph=dev_json_graph, buda_params=buda_params, param_name_lookup=param_name_lookup)))

    if cpu_post_json_graph["graph"] != "":
        json_graphs.append(copy.deepcopy(clean_names(json_graph=cpu_post_json_graph, buda_params=buda_params, param_name_lookup=param_name_lookup)))

    return json_graphs


def compile_pytorch_for_buda(torchmod, *inputs, graph_name, compiler_cfg, verify_cfg=None):
    training_mode = torchmod.training

    # Extract framework model outputs
    framework_outputs = extract_framework_model_outputs(
        framework="pytorch",
        model=torchmod,
        inputs=inputs,
        compiler_cfg=compiler_cfg,
    )

    # (Temporary): Remove when buda supports dropout
    if training_mode and compiler_cfg.enable_tvm_dropout == False:
        torchmod.eval()

    # Trace framework model
    traced_model = torch.jit.trace(torchmod, inputs, strict=False)

    # Extract flatten inputs
    flattened_inputs, flattened_input_names, flattened_name_map, input_structure = extract_flatten_inputs(
        framework="pytorch",
        model=traced_model,
        inputs=inputs,
    )

    graph_string = traced_model.graph.str().encode('utf-8')
    m = hashlib.sha256()
    m.update(graph_string)
    cached_graphs = load_serialized_tvm_graph(compiler_cfg, m.hexdigest())
    if cached_graphs is not None:
        return cached_graphs, flattened_inputs

    # Generate TVM module
    mod, params = tvm.relay.frontend.from_pytorch(traced_model, input_structure)
    mod = tvm.relay.op.contrib.flatten_inputs(mod, flattened_inputs, flattened_name_map)
    
    # Construct TVM IR
    mod, _ = construct_tvm_ir(
        framework="pytorch",
        model=torchmod,
        tvm_mod=mod,
        params=params,
        compiler_cfg=compiler_cfg,
    )

    # Construct NumPy inputs
    flattened_inputs_as_float = (act.float() if torch.is_floating_point(act) else act for act in flattened_inputs)
    np_inputs = {name:inp.detach().numpy() for name, inp in zip(flattened_input_names, flattened_inputs_as_float)}
    
    # Compile TVM for Buda
    partitioned_mod, buda_params = compile_tvm_for_buda(mod, params, np_inputs, framework_outputs, input_names=flattened_input_names, graph_name=graph_name, return_params=True, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)

    if training_mode:
        torchmod.train()

    # Extract Graphs (TT, CPU, ...)
    json_graphs = extract_graphs(partitioned_mod, buda_params, flattened_input_names, graph_hash=m.hexdigest())

    return json_graphs, flattened_inputs


def compile_tvm_for_buda(mod, params, inputs, golden_outputs, graph_name, input_names = [], return_params=False, compiler_cfg=None, verify_cfg=None):
    target = "llvm"
    verify_args = {'inputs': inputs, 'framework_outputs': golden_outputs, 'verify_cfg': verify_cfg}
    mod, params = tvm.relay.op.contrib.compile_for_buda(mod, target=target, params=params, graph_name=graph_name, **verify_args)

    if compiler_cfg is not None and compiler_cfg.varify_tvm_compile:
        verify_tvm_compile(mod, params, inputs, target, golden_outputs, "compile_for_buda", verify_cfg=verify_cfg)

    # Reconstruct Ops + export buda graph
    mod = tvm.relay.op.contrib.buda.reconstruct_ops_for_buda(mod)
    mod, buda_params = tvm.relay.op.contrib.buda.partition_for_buda(mod, graph_name=graph_name, compiler_cfg=compiler_cfg, input_names=input_names)
    tvm.relay.build_module.build(mod, target=target, params=params)

    if return_params:
        return mod, buda_params
    else:
        return mod


def clean_names(json_graph, buda_params, param_name_lookup={}):
    precursor = "tvmgen_default_pybuda_main_" if json_graph["device"] != "cpu" else "tvmgen_default_pybuda_cpudevice_main_"

    def trim_count(name):
        for i in range(-1, -len(name), -1):
            if name[i] == '_':
                return name[:i], name[i+1:]

    if len(json_graph["params"]) > 0:

        old_params = json_graph["params"]
        json_graph["params"] = {}
        for k, v in old_params.items():
            if precursor in k:
                num_digits = k.replace(precursor, "").find("_")
                key = k.replace(precursor, "")[num_digits + 1:] + k.replace(precursor, "")[:num_digits]
            else:
                name, num_digits = trim_count(k)
                old_name = param_name_lookup[name] if name in param_name_lookup else name
                param_name_lookup[k] = old_name + f"_{num_digits}"
                key = param_name_lookup[k] # This is done to sync the node names with the param names
            json_graph["params"][key] = v

    graph = json.loads(json_graph["graph"])

    for node in graph["nodes"]:
        if precursor in node["name"]:
            num_digits = node["name"].replace(precursor, "").find("_")
            node["name"] = node["name"].replace(precursor, "")[num_digits + 1:] + node["name"].replace(precursor, "")[:num_digits]
        elif param_name_lookup is not None and node["name"] in param_name_lookup:
            node["name"] = param_name_lookup[node["name"]]

    json_graph["graph"] = json.dumps(graph)

    return json_graph

def compile_onnx_for_buda(onnx_mod, path, *inputs, graph_name, compiler_cfg, verify_cfg=None):
    input_names = []
    for inp in onnx_mod.graph.input:
        input_names.append(inp.name)

    input_dict = {}
    input_shape_dict = {}
    for name, tensor in zip(input_names, inputs):
        input_dict[name] = tensor
        input_shape_dict[name] = tensor.shape

    assert len(input_names) == len(inputs), "Number of input names must match number of inputs"

    framework_outputs = extract_framework_model_outputs(
        framework="onnx",
        model=onnx_mod,
        inputs=inputs,
        compiler_cfg=compiler_cfg,
        path=path,
        input_dict=input_dict,
    )

    graph_string = str(onnx_mod).encode('utf-8')
    m = hashlib.sha256()
    m.update(graph_string)
    cached_graphs = load_serialized_tvm_graph(compiler_cfg, m.hexdigest())
    if cached_graphs is not None:
        return cached_graphs, inputs

    mod, params = relay.frontend.from_onnx(onnx_mod, input_shape_dict, freeze_params=False)
    mod = relay.transform.DynamicToStatic()(mod)

    if not compiler_cfg.enable_tvm_constant_prop:
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], {}))
    else:
        propped_params = {k: (v, True) for k, v in params.items()}
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], propped_params))

    partitioned_mod, buda_params = compile_tvm_for_buda(mod, params, input_dict, framework_outputs, input_names=input_names, graph_name=graph_name, return_params=True, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)

    json_graphs = extract_graphs(partitioned_mod, buda_params, input_names, graph_hash=m.hexdigest())

    return json_graphs, inputs


def compile_jax_for_buda(jaxmodel, *inputs, graph_name, compiler_cfg, verify_cfg=None):
    # Convert model from Jax to TensorFlow
    tf_model = jax2tf.convert(jaxmodel, enable_xla=False)
    tf_fun = tf.function(tf_model, autograph=False)
    
    # Extract framework model outputs
    framework_outputs = extract_framework_model_outputs(
        framework="jax",
        model=tf_fun,
        inputs=inputs,
        compiler_cfg=compiler_cfg,
    )

    # Get graph definition
    tf_fun = tf_fun.get_concrete_function(*inputs)
    graph_def = tf_fun.graph.as_graph_def()   

    # Extract flatten inputs
    flattened_inputs, flattened_input_names, _, _= extract_flatten_inputs(
        framework="jax",
        model=tf_fun,
        inputs=inputs,
    )

    # Generate TVM module
    outputs = [output.name for output in tf_fun.outputs]
    mod, params = tvm.relay.frontend.from_tensorflow(graph_def, layout="NCHW", outputs=outputs)
    mod = tvm.transform.Sequential([tvm.relay.transform.Inline()])(mod)

    # Construct TVM IR
    mod, param_name_lookup = construct_tvm_ir(
        framework="jax",
        model=jaxmodel,
        tvm_mod=mod,
        params=params,
        compiler_cfg=compiler_cfg,
    )

    # Construct NumPy inputs
    np_inputs = {i : None if x is None else x.numpy() for i, x in  zip(flattened_input_names, flattened_inputs)}

    # Compile TVM for Buda
    partitioned_mod, buda_params = compile_tvm_for_buda(mod, params, np_inputs, framework_outputs, graph_name=graph_name, return_params=True, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)

    # Extract Graphs (TT, CPU, ...)
    json_graphs = extract_graphs(partitioned_mod, buda_params, flattened_input_names, param_name_lookup)

    return json_graphs, flattened_inputs


def compile_tf_for_buda(tfmod, *inputs, graph_name, compiler_cfg, verify_cfg=None):
    # Extract framework model outputs
    framework_outputs = extract_framework_model_outputs(
        framework="tensorflow",
        model=tfmod,
        inputs=inputs,
        compiler_cfg=compiler_cfg,
    )

    # Trace module & get graph definition
    @tf.function
    def trace(*inputs):
        kwargs = {}
        import inspect 
        arg_names = inspect.getfullargspec(tfmod.call).args
        if "return_dict" in arg_names:
            kwargs["return_dict"] = False

        if "training" in arg_names:
            kwargs["training"] = False
        return tfmod(*inputs, **kwargs)

    full_model = trace.get_concrete_function(*inputs)
    frozen_func = convert_variables_to_constants_v2(full_model)
    graph_def = frozen_func.graph.as_graph_def()

    # Extract flatten inputs
    flattened_inputs, flattened_input_names, _, _= extract_flatten_inputs(
        framework="tensorflow",
        model=frozen_func,
        inputs=inputs,
    )

    m = hashlib.sha256()
    m.update(str(graph_def).encode('utf-8'))
    cached_graphs = load_serialized_tvm_graph(compiler_cfg, m.hexdigest())
    if cached_graphs is not None:
        return cached_graphs, flattened_inputs

    flattened_outputs = flatten_structured_output([full_model.structured_outputs])
    # Generate TVM module
    outputs = [x.name for x in flattened_outputs]
    mod, params = tvm.relay.frontend.from_tensorflow(graph_def, layout="NCHW", outputs=outputs)
    mod = tvm.transform.Sequential([tvm.relay.transform.Inline()])(mod)

    # Construct TVM IR
    mod, param_name_lookup = construct_tvm_ir(
        framework="tensorflow",
        model=tfmod,
        tvm_mod=mod,
        params=params,
        compiler_cfg=compiler_cfg,
    )

    # Construct NumPy inputs
    np_inputs = {i : None if x is None else x.numpy() for i, x in  zip(flattened_input_names, flattened_inputs)}

    # Compile TVM for Buda
    partitioned_mod, buda_params = compile_tvm_for_buda(mod, params, np_inputs, framework_outputs, input_names=flattened_input_names, graph_name=graph_name, return_params=True, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)
    
    # Extract Graphs (TT, CPU, ...)
    json_graphs = extract_graphs(partitioned_mod, buda_params, flattened_input_names, param_name_lookup, graph_hash=m.hexdigest())

    return json_graphs, flattened_inputs

# TODO (arui) : Verify graphdef output vs. TVM output
def compile_tf_graphdef_for_buda(graph_def, *inputs, graph_name, compiler_cfg, output_names=None):
    if output_names == None:
        output_list_ = []
    else:
        output_list_ = output_names
    # framework_outputs = tfmod(*inputs)
    # if not isinstance(framework_outputs, (list, tuple)):
    #     framework_outputs = [framework_outputs]

    # supported_outputs = (tf.Tensor, torch.Tensor)
    # framework_outputs = [x.numpy() for x in framework_outputs if isinstance(x, supported_outputs)]

    # @tf.function
    # def trace(*inputs):
    #     return tfmod(*inputs, training=False)

    # full_model = trace.get_concrete_function(*inputs)

    # frozen_func = convert_variables_to_constants_v2(full_model)
    # graph_def = frozen_func.graph.as_graph_def()

    m = hashlib.sha256()
    m.update(str(graph_def).encode('utf-8'))
    cached_graphs = load_serialized_tvm_graph(compiler_cfg, m.hexdigest())
    if cached_graphs is not None:
        return cached_graphs
        
    mod, params = tvm.relay.frontend.from_tensorflow(graph_def, outputs=output_list_)

    assert compiler_cfg.enable_tvm_constant_prop == True, "Pybuda Compile only support tf graphdef model with TVM parameter binding."
    if not compiler_cfg.enable_tvm_constant_prop:
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], {}))
    else:
        if len(compiler_cfg.tvm_constnat_prop_mask):
            propped_params = {k : (v, True) for k, v, in params.items() if any([mask in k for mask in compiler_cfg.tvm_constnat_prop_mask])}
        else:
            propped_params = {k : (v, True) for k, v, in params.items()}
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], propped_params))

    target = "llvm"
    mod, params = tvm.relay.op.contrib.compile_for_buda(mod, target=target, params=params, graph_name=graph_name)

    # Reconstruct Ops + export buda graph
    mod = tvm.relay.op.contrib.buda.reconstruct_ops_for_buda(mod)
    mod, buda_params = tvm.relay.op.contrib.buda.partition_for_buda(mod, graph_name=graph_name, compiler_cfg=compiler_cfg)

    executor_factory = tvm.relay.build_module.build(mod, target=target, params=params)

    # with tvm.transform.PassContext(opt_level=5):
    #     func = relay.create_executor("graph", mod=mod, device=tvm.cpu(0), target="llvm").evaluate()


    dev_json_graph["params"] = {}
    dev_json_graph["hash"] = m.hexdigest()
    for function_name in buda_params.keys():
        dev_json_graph["params"].update({name:v.numpy() for (k, v), name in zip(buda_params[function_name].items(), dev_json_graph["param_names"][function_name])})

    dev_functions = list(dev_json_graph["functions"].keys())
    dev_graph = join_graphs([dev_json_graph["functions"][function] for function in dev_functions])
    dev_json_graph["graph"] = dev_graph

    json_graphs = []
    json_graphs.append(copy.deepcopy(clean_names(json_graph=dev_json_graph, buda_params=buda_params)))
    return json_graphs


def compile_mxnet_for_buda(module, *inputs, graph_name, compiler_cfg, verify_cfg=None):
    framework_outputs = []
    if compiler_cfg is not None and compiler_cfg.varify_tvm_compile:
        framework_outputs = module(*inputs)
        if not isinstance(framework_outputs, (list, tuple)):
            framework_outputs = [framework_outputs]

        framework_outputs = [x.asnumpy() for x in framework_outputs if isinstance(x, mx.ndarray.ndarray.NDArray)]

    input_dict = {
        "input_" + str(i) : inp.shape
        for i, inp in enumerate(inputs)
    }

    mod_inputs = []
    if isinstance(module, mx.gluon.HybridBlock):
        for name in input_dict:
            mod_inputs.append(mx.sym.Variable(name))
        sym = module(*mod_inputs)
        if isinstance(sym, (list, tuple)):
            sym = mx.sym.Group(sym)
    else:
        sym = module
    graph_string = sym.tojson().encode('utf-8')
    m = hashlib.sha256()
    m.update(graph_string)
    cached_graphs = load_serialized_tvm_graph(compiler_cfg, m.hexdigest())
    if cached_graphs is not None:
        return cached_graphs

    input_name_to_tensor = {name : tensor.asnumpy() for name, tensor in zip(input_dict.keys(), inputs)}
    mod, params = relay.frontend.from_mxnet(module, shape=input_dict)

    if not compiler_cfg.enable_tvm_constant_prop:
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], {}))
    else:
        propped_params = {k : (v, True) for k, v, in params.items()}
        mod = tvm.IRModule.from_expr(tvm.relay.build_module.bind_params_by_name(mod["main"], propped_params))

    _, buda_params = compile_tvm_for_buda(mod, params, input_name_to_tensor, framework_outputs, input_names=list(input_dict.keys()), graph_name=graph_name, return_params=True, compiler_cfg=compiler_cfg, verify_cfg=verify_cfg)

    dev_json_graph["hash"] = m.hexdigest()
    dev_json_graph["params"] = {}
    for function_name in buda_params.keys():
        dev_json_graph["params"].update({name:v.numpy() for (k, v), name in zip(buda_params[function_name].items(), dev_json_graph["param_names"][function_name])})

    dev_functions = list(dev_json_graph["functions"].keys())
    dev_graph = join_graphs([dev_json_graph["functions"][function] for function in dev_functions])
    dev_json_graph["graph"] = dev_graph

    json_graph = []
    json_graph.append(copy.deepcopy(clean_names(json_graph=dev_json_graph, buda_params=buda_params)))
    return json_graph


def format_tvm_graph_weights(inputs, module, compiler_cfg, framework=None):
    """
    Formats model weights based on specific framework.

    Parameters
    ----------
    inputs: Tuple[Tensor, ...]
        Input tensors

    module: Module(PyTorchModule or TFModule)
        Module that contains workload which can be assigned to a single device.

    compiler_cfg: CompilerConfig
        Compiler configurations
        
    Returns
    -------
    OrderedDict, Boolean, Tuple
        Weights, Constant evaluation, Input tensors
    """
    if framework == "pytorch":
        if compiler_cfg.enable_training:
            for param in module.parameters():
                param.requires_grad = True

        torch_weights = module.state_dict()
        named_buffers = dict(module.named_buffers())
        torch_weights.update(named_buffers)
        named_params = dict(module.named_parameters())
        weights = {key: (value, named_params[key].requires_grad if key in named_params else False) for key, value in torch_weights.items()}
    elif framework == "tensorflow":
        weights = {weight.name: (torch.Tensor((tf.cast(weight.value(), tf.float32) if weight.value().dtype.is_floating else weight.value()).numpy()), True) for weight in module.weights}
        if not (len(inputs) > 0 and isinstance(inputs[0], torch.Tensor)):
            inputs = [torch.tensor(x.numpy()) for x in inputs if x is not None]  # Maybe we can switch all tensors to numpy?
    elif framework == "tf_graphdef":
        weights = {}
    elif framework == "onnx":
        numpy_weights = [onnx.numpy_helper.to_array(weight) for weight in module.graph.initializer]
        names = [weight.name for weight in module.graph.initializer]
        weights = {
            name : (torch.Tensor(weight), issubclass(weight.dtype.type, np.floating))
            for name, weight in zip(names, numpy_weights)
        }

        if not (len(inputs) > 0 and isinstance(inputs[0], torch.Tensor)):
            inputs = [torch.tensor(onnx.numpy_helper.to_array(x)) for x in inputs if x is not None]
    elif framework == "mxnet":
        weights = {
            name : (torch.Tensor(mx_param.data().asnumpy()), issubclass(mx_param.data().asnumpy().dtype.type, np.floating))
            for name, mx_param in module.collect_params().items()
        }
        if not (len(inputs) > 0 and isinstance(inputs[0], torch.Tensor)):
            inputs = [torch.tensor(x.asnumpy()) for x in inputs if x is not None]
    elif framework == "jax":
        def flatten_params(params, parent_key="", sep="."):
            items = []
            for key, val in params.items():
                new_key = parent_key + sep + key if parent_key else key

                if isinstance(val, MutableMapping):
                    items.extend(flatten_params(val, new_key, sep=sep).items())
                else:
                    items.append((new_key, val))

            return dict(items)

        module_params = flatten_params(module.variables['params']._dict)

        weights = {}
        for key, value in module_params.items():
            torch_tensor = torch.Tensor(np.array(value))
            weights[key] = (torch_tensor, True)

        if not (len(inputs) > 0 and isinstance(inputs[0], torch.Tensor)):
            inputs = [torch.tensor(x.numpy()) for x in inputs if x is not None]
    else:
        raise RuntimeError(f"Unsupported module type {type(module)}")

    return inputs, weights

def get_auto_path(graph_hash, compiler_cfg, is_load):
    """
    Returns auto cache path based on graph hash and tvm submodule git commit

    Parameters
    ----------
    graph_hash: String
        graph hash string

    compiler_cfg: CompilerConfig
        Compiler configurations

    is_load: Boolean
        Are we looking for load path (otherwise store)
        
    Returns
    -------
    String
        path to store/load graph
    """

    auto_cache = int(os.environ.get("PYBUDA_ENABLE_TVM_CACHE", 0))
    if bool(auto_cache) and compiler_cfg.tvm_graph_store_path == "" and compiler_cfg.tvm_graph_load_path == "":
        assert auto_cache == -1 or auto_cache == 1, f"PYBUDA_ENABLE_TVM_CACHE value of {auto_cache} not understood. Set to 1 to enable cache, 0 to disable and -1 to recache module"
        if auto_cache == -1 and is_load:
            auto_path = ""
        else:
            submodules = subprocess.check_output(['git', 'submodule', 'status', '--recursive']).decode('ascii').split("\n")
            tvm_short_cache = None
            for submodule in submodules:
                split_string = submodule.split(" ")
                if split_string[0] != "":
                    split_string.insert(0, "")
                    split_string[1] = split_string[1][1:]
                if len(split_string) > 2 and split_string[2] == "third_party/tvm":
                    tvm_short_cache = split_string[1][:8]
                    break
            assert tvm_short_cache is not None, "Couild not find tvm submodule, are you running from pybuda git repo?"

            auto_path = "generated_modules/tvm_cache/" + tvm_short_cache + "_" + graph_hash
    else:
        auto_path = compiler_cfg.tvm_graph_load_path if is_load else compiler_cfg.tvm_graph_store_path

    return auto_path

def load_serialized_tvm_graph(compiler_cfg, graph_hash):
    """
    Loads serialized TVM graph representation ported to PyBuda in form of python dictionary.

    Parameters
    ----------
    compiler_cfg: CompilerConfig
        Compiler configurations

    graph_hash: String
        graph hash string
        
    Returns
    -------
    Dictionary
        Deserialized TVM graph
    """

    load_path = get_auto_path(graph_hash, compiler_cfg, True)

    if load_path == "" or not file_exists(load_path) or compiler_cfg.enable_tvm_constant_prop:
        return None

    with open(load_path, "r") as file:
        serialized_graph_str = json.load(file)

    json_graphs = []
    for id, json_graph in serialized_graph_str.items():
        serialized_dict = {}
        serialized_dict["graph"] = json.dumps(json_graph["graph"])
        serialized_dict["hash"] = json.dumps(json_graph["hash"])
        serialized_dict["params"] = json_graph["params"]
        serialized_dict["device"] = json_graph["device"]
        if "nid_to_input_idx" in json_graph.keys():
            serialized_dict["nid_to_input_idx"] = {int(k) : v for k, v in json_graph["nid_to_input_idx"].items()}
        json_graphs.append(serialized_dict)

    logger.info(f"Successfully loaded serialized TVM graph from {load_path} path")

    return json_graphs


def serialize_and_store_tvm_graph(json_graphs, compiler_cfg):
    """
    Serializes TVM graph representation ported to PyBuda in form of JSON and stores it 
    on the desired destination.

    Parameters
    ----------
    json_graph: Dictionary
        Previously compiled TVM graph pored to PyBuda representation

    compiler_cfg: CompilerConfig
        Compiler configurations

    Returns
    -------
    """
    class NumpyArrayEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return JSONEncoder.default(self, obj)

    graph_hash = json_graphs[0]["hash"]
    store_path = get_auto_path(graph_hash, compiler_cfg, False)
    if store_path == "" or compiler_cfg.enable_tvm_constant_prop or not len(dev_json_graph["graph"]):
        return

    serilized_dict = {}

    for id, json_graph in enumerate(json_graphs):
        graph_dict = json.loads(json_graph["graph"])
        params_dict = json_graph["params"]
        serilized_dict[str(id)] = {}
        serilized_dict[str(id)]["graph"] = graph_dict
        serilized_dict[str(id)]["params"] = params_dict
        serilized_dict[str(id)]["device"] = json_graph["device"]
        serilized_dict[str(id)]["hash"] = json_graph["hash"]
        if "nid_to_input_idx" in json_graph.keys():
            serilized_dict[str(id)]["nid_to_input_idx"] = json_graph["nid_to_input_idx"]

    serilized_str = json.dumps(serilized_dict, cls=NumpyArrayEncoder, indent=2)
    
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, 'w') as file:
        file.write(serilized_str)

    logger.info(f"Successfully stored serilized TVM graph to {store_path} path")

