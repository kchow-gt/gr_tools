#!/usr/bin/python
"""Convenience functions for generating signals with GNU Radio components

This module houses functions to launch a source and sink around a
component to quickly run an input and extract an output.  Although
it may sound similiar to creating a flowgraph for the same purpose,
this allows for scripting the scenario with different input source,
and configuring the component under various parameters.

Examples
--------
>>> import numpy as np
>>> r = np.random.rand(10000)
>>> r.astype(np.complex64).tofile("/tmp/input.32cf")

>>> in_sig = {"path":"/tmp/input.32cf",
>>>     "type":DTYPE["COMPLEX"], "repeat":True}
>>> out_sig = {"path":"/tmp/output.32cf",
>>>     "type":DTYPE["COMPLEX"], "n_items":4000}
>>> component = blocks.multiply_const_cc(1.0)

# run simulation and load output from file.
>>> run_file_source(component, in_sig, out_sig)
>>> output = np.fromfile("/tmp/output.32cf", dtype=np.complex64)
"""
import os
import sys
import numpy as np
import time
from gnuradio import gr, blocks

DTYPE = {
    "BYTE": gr.sizeof_char * 1,
    "FLOAT": gr.sizeof_float,
    "COMPLEX": gr.sizeof_gr_complex,
    "SHORT":gr.sizeof_short,
    "INT":gr.sizeof_int,
}
DEFAULT_FILE_SPEC = {
    "path":"",
    "type":gr.sizeof_char * 1,
    "repeat":True,
}
DEFAULT_MESSAGE_SPEC = {
    "message": "hello world",
    "period(ms)": 300,
}
DEFAULT_OUT_SPEC = {
    "path":"",
    "type": DTYPE["BYTE"],
    "n_items":10000,
}
FILE_EXT = {
    "COMPLEX":".32cf",  # complex with float 32 real and imag
    "BYTE":".byte",     # bytes (8 bit int)
    "FLOAT":".32rf",    # 32 bit floats
    "INT":".32i",       # 32 bit integer
    "SHORT":".16i"      # 16 bit ints/shorts
}
def run_file_source(component,
        file_spec=DEFAULT_FILE_SPEC, out_spec=DEFAULT_OUT_SPEC,
        connections=None):
    """Run simulation with file source as input

    Parameters
    ----------
    component : gnuradio component
        This will typically be a subclass of gnuradio.gr.hier_block2
        Since this will need to import itself, that will be left to
        the calling function to import, create this instance and
        configure.

    file_spec : dict
        Dictionary with "type", "path", "repeat"

    out_spec : dict
        Dictionary with "type", "path", "n_items"

    connections : None or (tuple)
        If None, just try to connect.
        If provided, enforce connect to the right port
        First element of tuple defines the port on input
        Second element of tuple defines the port on output
    """
    top = gr.top_block()

    # ------------------------  setup scenario  -----------------------------
    file_src = blocks.file_source(
        file_spec["type"], file_spec["path"], file_spec["repeat"])

    # use the head block to limit output
    head = blocks.head(out_spec["type"], out_spec["n_items"])
    file_sink = blocks.file_sink(
        out_spec["type"], out_spec["path"]
    )

    # add connections
    if connections is None:
        top.connect(file_src, component, head, file_sink)
    else:
        top.connect((file_src), (component, connections[0]))
        top.connect((component, connections[1]), (head))
        top.connect(head, file_sink)

    # -----------------------  run simulation  ------------------------------
    top.run(max_noutput_items=out_spec["n_items"])

def run_msg_source(component,
        msg_spec=DEFAULT_MESSAGE_SPEC, out_spec=DEFAULT_OUT_SPEC,
        connections=None):
    """Run simulation with file source as input

    Parameters
    ----------
    component : gnuradio component
        This will typically be a subclass of gnuradio.gr.hier_block2
        Since this will need to import itself, that will be left to
        the calling function to import, create this instance and
        configure.

    msg_spec : dict
        Dictionary with "message", "periodic"

    out_spec : dict
        Dictionary with "type", "path", "n_items"

    connections : None or (tuple)
        If None, just try to connect.
        If provided, enforce connect to the right port
        First element of tuple defines the port on input
        Second element of tuple defines the port on output
    """
    top = gr.top_block()

    # ------------------------  setup scenario  -----------------------------
    import pmt
    source = blocks.message_strobe(pmt.intern("".join(msg_spec["message"])),
        msg_spec["period(ms)"])

    # use the head block to limit output
    head = blocks.head(out_spec["type"], out_spec["n_items"])
    file_sink = blocks.file_sink(
        out_spec["type"], out_spec["path"]
    )


    top.msg_connect((source, "strobe"), (component, connections[0]))
    top.connect((component, connections[1]), (head, 0))
    top.connect(head, file_sink)

    # -----------------------  run simulation  ------------------------------
    # NOTE: top.run() does not seem to check head
    #       when tested on msg_source -> wifi -> file_sink
    top.start(max_noutput_items=out_spec["n_items"])
    while head.nitems_written(0) < out_spec["n_items"]:
        time.sleep(1e-3)

    print("Completed simulation")
    #top.stop() # FIXME: get "boost::thread_interrupted"

