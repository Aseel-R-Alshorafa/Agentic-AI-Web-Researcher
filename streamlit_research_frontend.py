from __future__ import annotations

import json
import traceback
from typing import Any, Callable, Dict, List, Optional

import streamlit as st

from agents.assistant_selector import select_assistant
from agents.report_writer import write_research_report
from agents.web_researcher import (
    evaluate_search_relevance,
    generate_search_queries,
    perform_web_searches,
    summarize_search_results,
)

MAX_ITERATIONS = 3


st.set_page_config(
    page_title="Researcher Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1320px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        .hero {
            padding: 1.15rem 1.25rem;
            border: 1px solid rgba(120,120,120,0.16);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(59,130,246,0.10), rgba(16,185,129,0.06));
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
        }
        .hero p {
            margin: 0.35rem 0 0 0;
            opacity: 0.92;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


State = Dict[str, Any]
StepFunction = Callable[[State], Dict[str, Any]]
StatusCallback = Optional[Callable[[str, str, int, int], None]]


# ---------- State helpers ----------
def build_initial_state(question: str) -> State:
    return {
        "user_question": question,
        "assistant_info": None,
        "search_queries": None,
        "search_results": None,
        "search_summaries": None,
        "research_summary": None,
        "final_report": None,
        "used_fallback_search": False,
        "relevance_evaluation": None,
        "should_regenerate_queries": None,
        "iteration_count": 0,
        "ui_steps": [],
    }


def merge_state(state: State, updates: Optional[Dict[str, Any]]) -> State:
    if updates:
        state.update(updates)
    return state


def append_ui_step(state: State, key: str, title: str, details: str) -> None:
    state.setdefault("ui_steps", []).append(
        {"key": key, "title": title, "details": details}
    )


def pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except Exception:
        return str(value)


def extract_unique_urls(state: State) -> List[str]:
    seen = set()
    urls: List[str] = []
    for item in state.get("search_summaries") or []:
        url = item.get("result_url")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


# ---------- Pipeline ----------
def describe_step(state: State, step_key: str) -> str:
    if step_key == "assistant":
        assistant = (state.get("assistant_info") or {}).get("assistant_type", "Unknown assistant")
        return f"Selected assistant: {assistant}"
    if step_key == "queries":
        queries = state.get("search_queries") or []
        return f"Generated {len(queries)} search quer{'ies' if len(queries) != 1 else 'y'}."
    if step_key == "results":
        results = state.get("search_results") or []
        suffix = " Fallback search was used." if state.get("used_fallback_search") else ""
        return f"Collected {len(results)} result{'s' if len(results) != 1 else ''}.{suffix}"
    if step_key == "summaries":
        summaries = state.get("search_summaries") or []
        return f"Created {len(summaries)} source summar{'ies' if len(summaries) != 1 else 'y'}."
    if step_key == "relevance":
        evaluation = state.get("relevance_evaluation") or {}
        pct = evaluation.get("relevance_percentage", "N/A")
        regen = bool(state.get("should_regenerate_queries"))
        action = "Will regenerate queries." if regen else "Proceeding to report writing."
        return f"Relevance: {pct}%. {action}"
    if step_key == "report":
        report = state.get("final_report") or ""
        return f"Generated final report ({len(report):,} characters)."
    return "Step completed."


def get_total_steps() -> int:
    # 1 assistant + up to 4 steps per iteration + 1 report
    return 1 + (MAX_ITERATIONS * 4) + 1


def run_step(
    state: State,
    key: str,
    title: str,
    fn: StepFunction,
    step_number: int,
    total_steps: int,
    status_callback: StatusCallback = None,
) -> State:
    if status_callback:
        status_callback(title, "running", step_number, total_steps)

    updates = fn(state)
    merge_state(state, updates)
    append_ui_step(state, key, title, describe_step(state, key))

    if status_callback:
        status_callback(title, "done", step_number, total_steps)
    return state


def run_research_pipeline(question: str, status_callback: StatusCallback = None) -> State:
    state = build_initial_state(question)
    total_steps = get_total_steps()
    current_step = 1

    run_step(
        state,
        "assistant",
        "Selecting assistant",
        select_assistant,
        current_step,
        total_steps,
        status_callback,
    )
    current_step += 1

    while True:
        iteration = int(state.get("iteration_count", 0)) + 1

        run_step(
            state,
            "queries",
            f"Generating search queries (iteration {iteration})",
            generate_search_queries,
            current_step,
            total_steps,
            status_callback,
        )
        current_step += 1

        run_step(
            state,
            "results",
            f"Searching the web (iteration {iteration})",
            perform_web_searches,
            current_step,
            total_steps,
            status_callback,
        )
        current_step += 1

        run_step(
            state,
            "summaries",
            f"Summarizing sources (iteration {iteration})",
            summarize_search_results,
            current_step,
            total_steps,
            status_callback,
        )
        current_step += 1

        run_step(
            state,
            "relevance",
            f"Evaluating relevance (iteration {iteration})",
            evaluate_search_relevance,
            current_step,
            total_steps,
            status_callback,
        )
        current_step += 1

        state["iteration_count"] = iteration
        should_retry = bool(state.get("should_regenerate_queries"))
        if iteration >= MAX_ITERATIONS or not should_retry:
            break

    run_step(
        state,
        "report",
        "Writing final report",
        write_research_report,
        current_step,
        total_steps,
        status_callback,
    )
    return state


# ---------- UI helpers ----------
def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>🔎 Researcher Agent</h1>
            <p>Follow the full research workflow from assistant selection to a polished final report.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, bool]:
    with st.sidebar:
        st.header("Run researcher")
        question = st.text_area(
            "Research question",
            value="",
            placeholder="What can you tell me about Astorga's roman spas?",
            height=100,
        )
        run_clicked = st.button("Run", type="primary", use_container_width=True)

        st.divider()
        st.caption(f"Max iterations: {MAX_ITERATIONS}")

    return question, run_clicked


def render_overview(state: State) -> None:
    assistant_info = state.get("assistant_info") or {}
    queries = state.get("search_queries") or []
    results = state.get("search_results") or []
    evaluation = state.get("relevance_evaluation") or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assistant", assistant_info.get("assistant_type", "—"))
    c2.metric("Queries", len(queries))
    c3.metric("Sources", len(results))
    c4.metric("Relevance", f"{evaluation.get('relevance_percentage', '—')}%")

    st.subheader("Question")
    st.write(state.get("user_question", ""))

    if assistant_info:
        st.subheader("Assistant instructions")
        st.code(assistant_info.get("assistant_instructions", ""), language="markdown")

    st.subheader("Execution log")
    for step in state.get("ui_steps", []):
        with st.container(border=True):
            st.markdown(f"**{step['title']}**")
            st.caption(step["details"])


def render_assistant_tab(state: State) -> None:
    assistant_info = state.get("assistant_info") or {}
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Assistant")
        st.write(assistant_info.get("assistant_type", "—"))

    with right:
        st.subheader("Question")
        st.write(state.get("user_question", ""))

    st.subheader("Instructions")
    st.code(assistant_info.get("assistant_instructions", ""), language="markdown")


def render_queries_tab(state: State) -> None:
    queries = state.get("search_queries") or []
    st.subheader("Generated search queries")

    if not queries:
        st.info("No queries were generated.")
        return

    for idx, item in enumerate(queries, start=1):
        with st.container(border=True):
            st.markdown(f"**Query {idx}**")
            st.write(item.get("search_query", ""))


def render_results_tab(state: State) -> None:
    results = state.get("search_results") or []
    st.subheader("Search results")

    if not results:
        st.info("No results were collected.")
        return

    for idx, item in enumerate(results, start=1):
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**Result {idx}**")
                st.write(item.get("result_url", ""))
                st.caption(f"Query: {item.get('search_query', '')}")
            with right:
                st.metric("Fallback", "Yes" if item.get("is_fallback") else "No")


def render_summaries_tab(state: State) -> None:
    summaries = state.get("search_summaries") or []
    st.subheader("Source summaries")

    if not summaries:
        st.info("No summaries are available.")
        return

    for idx, item in enumerate(summaries, start=1):
        with st.expander(f"Summary {idx}", expanded=(idx == 1)):
            st.markdown(item.get("summary", ""))

    st.subheader("Combined research summary")
    st.text_area(
        "research_summary",
        value=state.get("research_summary", ""),
        height=300,
        label_visibility="collapsed",
    )


def render_relevance_tab(state: State) -> None:
    evaluation = state.get("relevance_evaluation") or {}
    st.subheader("Relevance evaluation")

    if evaluation:
        c1, c2, c3 = st.columns(3)
        c1.metric("Relevant %", evaluation.get("relevance_percentage", "—"))
        c2.metric("Relevant count", evaluation.get("relevant_count", "—"))
        c3.metric("Total count", evaluation.get("total_count", "—"))
        st.markdown("**Explanation**")
        st.write(evaluation.get("explanation", ""))
    else:
        st.info("No relevance evaluation was returned.")

    st.markdown("**Raw evaluation**")
    st.code(pretty_json(evaluation), language="json")


def render_report_tab(state: State) -> None:
    report = state.get("final_report") or ""
    st.subheader("Final report")

    if report:
        st.markdown(report)
    else:
        st.info("No report is available.")

    left, right = st.columns(2)
    with left:
        st.download_button(
            "Download report.md",
            data=report.encode("utf-8"),
            file_name="research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "Download full state.json",
            data=pretty_json(state).encode("utf-8"),
            file_name="research_state.json",
            mime="application/json",
            use_container_width=True,
        )

    urls = extract_unique_urls(state)
    if urls:
        st.markdown("**Sources used**")
        for url in urls:
            st.write(f"- {url}")


def render_results_view(state: State) -> None:
    tabs = st.tabs([
        "Overview",
        "Assistant",
        "Queries",
        "Results",
        "Summaries",
        "Relevance",
        "Report",
    ])

    with tabs[0]:
        render_overview(state)
    with tabs[1]:
        render_assistant_tab(state)
    with tabs[2]:
        render_queries_tab(state)
    with tabs[3]:
        render_results_tab(state)
    with tabs[4]:
        render_summaries_tab(state)
    with tabs[5]:
        render_relevance_tab(state)
    with tabs[6]:
        render_report_tab(state)


# ---------- App ----------
def main() -> None:
    render_header()
    question, run_clicked = render_sidebar()

    if run_clicked:
        if not question.strip():
            st.warning("Please enter a research question.")
        else:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()

            progress_bar = progress_placeholder.progress(0, text="Starting researcher...")
            status_box = status_placeholder.info("Preparing pipeline...")

            def update_status(title: str, stage: str, current_step: int, total_steps: int) -> None:
                progress_value = min(current_step / total_steps, 1.0)
                if stage == "running":
                    progress_bar.progress(progress_value, text=f"Current step: {title}")
                    status_box.info(f"Currently working on: {title}")
                else:
                    progress_bar.progress(progress_value, text=f"Completed: {title}")
                    status_box.success(f"Completed: {title}")

            try:
                st.session_state["researcher_state"] = run_research_pipeline(
                    question.strip(),
                    status_callback=update_status,
                )
                progress_bar.progress(1.0, text="Research complete")
                status_placeholder.success("Research pipeline finished successfully.")
            except Exception as exc:
                status_placeholder.error("The Streamlit app could not run the research pipeline.")
                st.code("".join(traceback.format_exception(exc)), language="python")

    state = st.session_state.get("researcher_state")
    if state:
        render_results_view(state)
    else:
        st.info("Enter a question in the sidebar and run the researcher to populate the tabs.")


if __name__ == "__main__":
    main()
