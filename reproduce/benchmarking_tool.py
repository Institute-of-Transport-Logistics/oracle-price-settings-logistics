"""Streamlit UI for the benchmarking tool — configure, queue, and monitor runs."""

from __future__ import annotations

import html
import logging
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from oracle_paper.benchmark import BenchmarkConfig
from oracle_paper.benchmark.results import BenchmarkResults
from oracle_paper.benchmark.runner import BenchmarkRunner


class ColorfulLogHandler(logging.Handler):
    def __init__(self, container):
        super().__init__()
        self.container = container.empty()
        self.log_lines = []

    def emit(self, record):
        msg = self.format(record)
        color = "#CCCCCC"
        if record.levelno == logging.INFO:
            color = "#28a745"
        elif record.levelno == logging.WARNING:
            color = "#ffc107"
        elif record.levelno == logging.ERROR:
            color = "#dc3545"

        if "\n" in msg and not msg.startswith("\n"): msg = "\n" + msg
        clean_msg = html.escape(msg)

        log_line_html = f"""<div style="font-family: 'Courier New', monospace; font-size: 13px; margin-bottom: 2px; white-space: pre-wrap; line-height: 1.2;">
<span style="color: {color}; font-weight: bold;">[{record.levelname}]</span>
<span style="color: #bbbbbb;">{clean_msg}</span>
</div>"""
        self.log_lines.append(log_line_html)
        if len(self.log_lines) > 500: self.log_lines.pop(0)

        log_content = "".join(self.log_lines)
        terminal_html = f"""<div style="background-color: #1e1e1e; color: #c5c5c5; padding: 15px; border-radius: 5px; border: 1px solid #333; height: 400px; overflow-y: auto; display: flex; flex-direction: column-reverse;">
<div>{log_content}</div></div>"""
        self.container.markdown(terminal_html, unsafe_allow_html=True)


if "benchmark_results" not in st.session_state: st.session_state.benchmark_results = BenchmarkResults()
if "n_nodes_range" not in st.session_state: st.session_state.n_nodes_range = set()
if "n_clients_range" not in st.session_state: st.session_state.n_clients_range = set()
if "benchmark_queue" not in st.session_state: st.session_state.benchmark_queue = []

st.set_page_config(page_title="Benchmarking Tool Professional", layout="wide", page_icon="🚀")

with st.sidebar:
    st.header("🌍 Global Settings")
    st.markdown("---")

    dataset = st.selectbox(" 📁Dataset", ("CAB100"))
    max_n_nodes = 100


    random_nodes = st.checkbox('Select random nodes?', value=True)
    st.markdown("---")
    if "n_runs" not in st.session_state: st.session_state._n_runs = 10
    n_runs = st.slider("🔄 Number of Runs", 1, 20, value=st.session_state._n_runs)

    if n_runs != st.session_state._n_runs:
        st.session_state._n_runs = n_runs
        st.session_state._seed_dict = {i: i for i in range(1, n_runs + 1)}
    elif "seed_dict" not in st.session_state:
        st.session_state._seed_dict = {i: i for i in range(1, st.session_state._n_runs + 1)}

    with st.expander("🎲 Seed Configuration"):
        seed_dict = st.session_state._seed_dict
        selected_run = st.selectbox("Select Run #", list(seed_dict.keys()))
        if selected_run:
            new_seed = st.number_input(f"Seed for Run {selected_run}", value=seed_dict[selected_run], min_value=1)
            st.session_state._seed_dict[selected_run] = new_seed

    st.markdown("---")
    scaling = st.checkbox("Scale Costs?", value=True)
    cur_scaling_factor = 1
    if scaling:
        cur_scaling_factor = st.number_input("Factor", value=1000, step=100)

st.title("🚀 Benchmark Automation")

tab_config, tab_queue, tab_results = st.tabs(["⚙️ Configuration", "🐍 Queue", "📈 Live Results"])

with tab_config:
    st.subheader("Create new Benchmark Configuration")
    col_topo, col_algo = st.columns([1, 1], gap="medium")
    with col_topo:
        st.info("📍 **Network Configuration**")
        n_hubs = st.slider("Number of Hubs", 1, max_n_nodes, 3)
        benchmark_type = st.radio("Benchmark Type:", ("Variable Nodes", "Variable Clients"), horizontal=True)
        benchmark_type_str = "n_nodes" if benchmark_type == "Variable Nodes" else "n_clients"

        if benchmark_type == "Variable Nodes":
            st.caption("List of Nodes:")
            c1, c2 = st.columns([3, 1])
            new_node = c1.number_input("Add Number of Nodes", min_value=n_hubs + 1, max_value=max_n_nodes, step=1)
            if c2.button("➕ Node"):
                st.session_state.n_nodes_range.add(int(new_node))
            if st.session_state.n_nodes_range:
                st.write(f"**Actual List:** {sorted(st.session_state.n_nodes_range)}")
                if st.button("Remove Last Node", key="del_node"):
                    st.session_state.n_nodes_range.pop()
                    st.rerun()
            else:
                st.warning("⚠️ List is empty!")
            st.markdown("---")
            option_random_clients = st.checkbox('Choose Random Number of Clients', value=False)
            max_n_clients = st.slider(f"Maxium Clients per Route", 1, 200, 5)
            st.session_state.n_clients_range = {max_n_clients}
        else:
            st.caption("List of Number of Clients:")
            fix_nodes = st.slider("Fixed Number of Nodes", n_hubs + 1, max_n_nodes, n_hubs + 2)
            st.session_state.n_nodes_range = {fix_nodes}
            c1, c2 = st.columns([3, 1])
            new_client = c1.number_input("Add number of Clients per Route:", min_value=1, step=1)
            if c2.button("➕ Client"):
                st.session_state.n_clients_range.add(int(new_client))
            if st.session_state.n_clients_range:
                st.write(f"**Actual List:** {sorted(st.session_state.n_clients_range)}")
                if st.button("Remove the last added Number of Clients", key="del_client"):
                    st.session_state.n_clients_range.pop()
                    st.rerun()
            option_random_clients = False

    with col_algo:
        st.info("🧮 **Algorithms & Constraints**")
        methods = st.multiselect('Methods', ['pc_hlp', 'ppc_hlp', 'ps_hlp', 'ps_bhlp'], default=['pc_hlp'])
        c_alpha, c_time = st.columns(2)
        alpha_val = c_alpha.selectbox('Alpha Value', [round(0.1 + i * 0.1, 2) for i in range(9)], index=6)
        time_lim = c_time.number_input('Time Limit for Solver (Seconds)', value=3600)
        st.write("**Budget Factors**")
        b1, b2 = st.columns(2)
        min_b = b1.number_input("Min Factor", 0.1, 5.0, 0.2)
        max_b = b2.number_input("Max Factor", 0.1, 5.0, 5.0)
        output_dir = st.text_input(
            "Output directory",
            str(Path.cwd() / "reproduce" / "benchmark_results"),
        )
        file_name = st.text_input("Base file name", "benchmark_run")

    st.markdown("---")
    if st.button("📥 Add to Queue", type="primary", use_container_width=True):
        if not methods or not st.session_state.n_nodes_range or not st.session_state.n_clients_range:
            st.error("Please select at least one method and complete the Node/Client lists.")
        else:
            new_config = BenchmarkConfig(
                n_hubs=n_hubs,
                n_nodes_range=sorted(list(st.session_state.n_nodes_range)),
                n_clients_range=sorted(list(st.session_state.n_clients_range)),
                methods=methods,
                random_nodes=random_nodes,
                random_n_clients_route=option_random_clients,
                alpha=alpha_val,
                min_budget_factor=min_b,
                max_budget_factor=max_b,
                time_limit=time_lim,
                benchmark_type=benchmark_type_str,
                file_name=file_name,
                output_dir=output_dir,
                seed_dict=st.session_state._seed_dict,
                n_runs=st.session_state._n_runs,
                scaling=scaling,
                scaling_factor=cur_scaling_factor
            )
            st.session_state.benchmark_queue.append(new_config)
            st.toast(f"✅ '{file_name}' add to the Queue!")

with tab_queue:
    st.subheader("📋 Actual Queue")
    if st.session_state.benchmark_queue:
        queue_data = []
        for i, conf in enumerate(st.session_state.benchmark_queue):
            queue_data.append({
                "ID": i + 1,
                "File": conf.file_name,
                "Type": conf.benchmark_type,
                "Methods": ", ".join(conf.methods),
                "Alpha:": str(conf.alpha),
                "Nodes": str(conf.n_nodes_range),
                "Hubs": str(conf.n_hubs),
                "Number of Clients per Route": str(conf.n_clients_range),
                "Number of Runs": conf.n_runs
            })
        st.dataframe(pd.DataFrame(queue_data).set_index("ID"), use_container_width=True)
        c_clear, c_run = st.columns([1, 4])
        if c_clear.button("🗑️ Delete Everything"):
            st.session_state.benchmark_queue = []
            st.rerun()
        run_clicked = c_run.button("▶️ Start Execution Queue", type="primary", use_container_width=True)
    else:
        st.info("The queue is empty. Go to 'Configuration' to add jobs.")
        run_clicked = False

with tab_results:
    st.subheader("📈 Live Monitoring")
    status_container = st.container()
    col_vis, col_log = st.columns([1, 1])
    with col_vis:
        st.write("##### Data table")
        results_spot = st.empty()
    with col_log:
        st.write("##### Terminal Output")
        log_spot = st.empty()

    if run_clicked and st.session_state.benchmark_queue:
        logger = logging.getLogger("BenchmarkResultsSaver")
        logger.setLevel(logging.INFO)
        st_handler = ColorfulLogHandler(log_spot)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        st_handler.setFormatter(formatter)
        logger.addHandler(st_handler)

        total_jobs = len(st.session_state.benchmark_queue)

        st.write("---")
        st.caption("🚀 Total progress (queue)")
        queue_progress_bar = st.progress(0)
        st.caption("⚡ Current job progress")
        job_progress_bar = st.progress(0)
        job_status_text = st.empty()

        try:
            for idx, config in enumerate(st.session_state.benchmark_queue):
                status_container.info(f"⏳ **Processed job {idx + 1}/{total_jobs}:** `{config.file_name}`")


                def on_new_result(benchmark_results: BenchmarkResults):
                    df = benchmark_results.to_dataframe()
                    results_spot.dataframe(df, use_container_width=True)


                def update_job_progress(current, total, text):
                    ratio = current / total
                    safe_ratio = min(ratio, 1.0)
                    job_progress_bar.progress(safe_ratio)
                    job_status_text.markdown(f"### ⏳ {int(safe_ratio * 100)}% \n**Task:** `{text}`")


                runner = BenchmarkRunner(config)
                runner.add_callback(on_new_result)
                runner.set_progress_callback(update_job_progress)


                try:
                    runner.run()

                    queue_progress_bar.progress((idx + 1) / total_jobs)
                    st.toast(f"✅ Job {config.file_name} completed!")
                    job_progress_bar.progress(0)
                    job_status_text.empty()

                    st.success(f"✅ Finished: {config.file_name}")

                except Exception as benchmark_error:
                    st.error(f"❌ Error in Benchmark '{config.file_name}': {str(benchmark_error)}")
                    logger.error(f"Cancellation: {str(benchmark_error)}")

                time.sleep(1)


            status_container.success("🎉 All benchmarks in the queue have been executed!")

        except Exception as e:

            status_container.error(f"❌ Critical System Error: {str(e)}")
            logger.error(f"System Crash: {str(e)}")

        finally:
            logger.removeHandler(st_handler)


def main() -> None:
    """Launch the Streamlit benchmarking UI (when invoked directly)."""
    # Guard: if Streamlit already loaded this file, don't re-spawn.
    import os
    if os.environ.get("STREAMLIT_RUN_APP_PATH"):
        return
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve())],
    )