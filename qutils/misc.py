import functools
import sys, os, psutil
import datetime
from typing import Any, Dict, List
import subprocess
import time

import matplotlib.pyplot as plt

import json
from qiskit.visualization import plot_coupling_map, plot_gate_map


BARRIER_OP_LIST = ["measure", "reset", "barrier", "bfunc"]


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        func_name = func.__name__
        obj = args[0]

        if not hasattr(obj, "_exec_times"):
            obj._exec_times = {}
        # Record execution time to class member
        obj._exec_times.setdefault(func_name, 0)
        obj._exec_times[func_name] += end_time - start_time
        return result

    return wrapper


def print_statistics(self):
    try:
        for k, v in self._exec_times.items():
            print("{}\t{}".format(k, v))
        # print(self._exec_times)
    except Exception:
        print("No statistics found!")


def profile(t=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            pid = os.getpid()
            subprocess.Popen(["./tools/monitor_mem.sh", str(pid), str(t)])
            time_before = time.time()
            result = func(*args, **kwargs)
            time_after = time.time()
            print(
                "{}:consumed time:\t{:,}".format(
                    func.__name__, time_after - time_before
                )
            )
            return result

        return wrapper

    return decorator


def get_op_lists(qobj_dict):
    """
    Get operation list from Qobj
    """
    op_lists = []
    try:
        exps = qobj_dict["experiments"]
        for exp_id, exp in enumerate(exps):
            op_list = exp["instructions"]
            op_lists.append(op_list)
    except Exception:
        print("Error processing qobj dictionary: no instructions!")
        sys.exit(1)
    return op_lists


def get_op_list(op_list, without_measure=False):
    new_op_list = []
    for op in op_list:
        if without_measure:
            if op["name"] == "measure":
                continue
            if "qubits" not in op:
                continue
        new_op_list.append(op)
    return new_op_list


def get_op_list_without_measure(op_list):
    op_list_wo_meas = []
    for op in op_list:
        if op["name"] == "measure":
            continue
        if "qubits" not in op:
            continue
        op_list_wo_meas.append(op)
    return op_list_wo_meas


def get_n_qubits(qobj_dict):
    n_qubits = None
    try:
        n_qubits = qobj_dict["config"]["n_qubits"]
    except KeyError:
        print("Error processing qobj dictionary: no n_qubits!")
        sys.exit(1)
    return n_qubits


def print_op_list(op_list):
    for op in op_list:
        name = op["name"]
        if name in BARRIER_OP_LIST:
            print("{}".format(name))
            continue
        qubits = op["qubits"]
        print("{}:{}".format(name, ",".join([str(q) for q in qubits])))


def print_qobj(qobj):
    qobj_dict = qobj.to_dict()
    qobj_json = json.dumps(qobj_dict, sort_keys=True, indent=4, separators=(",", ":"))
    print(qobj_json)


def load_qobj_from_path(qobj_path):
    qobj_dict = None
    with open(qobj_path, "r") as fr:
        qobj_dict = json.load(fr)
    return qobj_dict


def plot_topology(backend, figname=None):
    """Plot backend topology"""
    fig = plot_gate_map(backend)
    if figname:
        fig.savefig(figname)


def pretty(d: Dict, indent=0) -> None:
    """
    Pretty print dictionary

    Ref: https://stackoverflow.com/questions/3229419/how-to-pretty-print-nested-dictionaries
    """
    for key, value in d.items():
        print("\t" * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            print("\t" * (indent + 1) + str(value))


def couple_map_to_graph(coupling_map: List[List]):
    """
    Transform coupling map to dictionary for convenience
    """
    graph = {}

    for edge in coupling_map:
        if len(edge) != 2:
            raise ValueError("Each edge should be a List with length 2!")
        node = edge[0]
        neighbor = edge[1]
        graph.setdefault(node, [])
        graph[node].append(neighbor)

    return graph


# TODO(zhaoyilun): graph partition
# 1. DFS and Fix sub-graph size


class DatetimeJsonEncoder(json.JSONEncoder):
    """A simple datetime json encoder for transforming
    datetime within a dictionary to json"""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return super().default(o)


class QiskitBackendJsonEncoder(json.JSONEncoder):
    """Transform qiskit backendconfiguration/properties to json"""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, complex):
            return str(o.real) + str(o.imag) + "j"
        else:
            return super().default(o)


def check_equiv_two_list(first: List[set], second: List[set]):
    """For given two lists, check if they contain the same elements, if so, return true"""
    if len(first) != len(second):
        return False
    for s in first:
        if s not in second:
            return False
    return True
