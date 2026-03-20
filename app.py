from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from kobi.analysis import bullets, consensus_keywords, pairwise
from kobi.exporters import to_json, to_markdown
from kobi.providers import PROVIDERS
from kobi.storage import load_sessions, save_session

st.set_page_config(page_title="KOBI v2", page_icon="🧠", layout="wide")

DEFAULT_SYSTEM = (
    "You are part of KOBI, a multi-model deliberation workflow. "
    "Answer clearly and concretely. Structure your answer with: 1) main position, "
    "2) strongest reasons, 3) key risks or objections, 4) practical next step."
)

DEFAULT_MODELS = {
    "OpenAI": "gpt-5.4",
    "Anthropic": "claude-sonnet-4-5",
    "Mistral": "mistral-large-latest",
}

for key, value in {
    "responses": [],
    "question": "",
    "system_prompt": DEFAULT_SYSTEM,
    "synthesis": "",
    "session_name": "KOBI Session",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def run_models(selected: list[str], labels: dict[str, str], models: dict[str, str], keys: dict[str, str | None]) -> None:
    results = []
    prompt = st.session_state["question"].strip()
    system_prompt = st.session_state["system_prompt"].strip()
    if not prompt:
        st.warning("Bitte zuerst eine Frage eingeben.")
        return

    progress = st.progress(0, text="Running models...")
    for idx, provider_name in enumerate(selected, start=1):
        fn = PROVIDERS[provider_name]
        result = fn(
            prompt=prompt,
            system_prompt=system_prompt,
            api_key=keys.get(provider_name),
            model=models[provider_name],
        )
        results.append(
            {
                "label": labels[provider_name],
                "provider": provider_name,
                "model": result.model,
                "answer": result.text,
                "error": result.error,
            }
        )
        progress.progress(idx / len(selected), text=f"Finished {provider_name}")
    st.session_state["responses"] = results
    progress.empty()


st.title("🧠 KOBI v2")
st.caption("Multi-provider deliberation workspace with live model calls, divergence view, and human synthesis.")

with st.sidebar:
    st.header("Models")
    enabled = {
        provider: st.checkbox(provider, value=(provider in ["OpenAI", "Anthropic", "Mistral"]))
        for provider in PROVIDERS.keys()
    }

    labels = {}
    model_ids = {}
    api_keys = {}
    for provider in PROVIDERS.keys():
        st.subheader(provider)
        labels[provider] = st.text_input(f"Label for {provider}", value=provider, key=f"label_{provider}")
        model_ids[provider] = st.text_input(f"Model for {provider}", value=DEFAULT_MODELS[provider], key=f"model_{provider}")
        api_keys[provider] = st.text_input(
            f"{provider} API key (optional if set in env/secrets)",
            value="",
            type="password",
            key=f"api_{provider}",
        ) or st.secrets.get(f"{provider.upper()}_API_KEY", None)

    st.markdown("---")
    st.subheader("Saved sessions")
    saved = load_sessions(8)
    if saved:
        for item in saved:
            st.caption(f"{item['timestamp']} — {item['session_name']}")
    else:
        st.caption("Noch keine lokalen Sessions gespeichert.")

left, right = st.columns([1.2, 1])

with left:
    with st.form("kobi_run_form"):
        session_name = st.text_input("Session name", value=st.session_state["session_name"])
        question = st.text_area(
            "Core question",
            value=st.session_state["question"],
            height=140,
            placeholder="z. B. Should a public-sector AI ever withhold information to prevent panic?",
        )
        system_prompt = st.text_area(
            "Shared system prompt",
            value=st.session_state["system_prompt"],
            height=130,
        )
        submitted = st.form_submit_button("Run selected models", use_container_width=True)

    if submitted:
        st.session_state["session_name"] = session_name
        st.session_state["question"] = question
        st.session_state["system_prompt"] = system_prompt
        selected = [p for p, on in enabled.items() if on]
        if not selected:
            st.warning("Bitte mindestens einen Provider aktivieren.")
        else:
            run_models(selected, labels, model_ids, api_keys)

with right:
    st.subheader("Human synthesis")
    st.session_state["synthesis"] = st.text_area(
        "Document your synthesis / SKI note",
        value=st.session_state["synthesis"],
        height=320,
        placeholder="Summarize convergence, divergence, trade-offs, and your final synthesis here.",
    )

responses = st.session_state["responses"]

if responses:
    st.markdown("---")
    st.header("Responses")
    tabs = st.tabs([r["label"] for r in responses])
    for tab, row in zip(tabs, responses):
        with tab:
            st.caption(f"{row['provider']} · {row['model']}")
            if row.get("error"):
                st.error(row["error"])
            else:
                st.write(row["answer"])
                key_points = bullets(row["answer"])[:4]
                if key_points:
                    st.markdown("**Key points**")
                    for point in key_points:
                        st.write(f"- {point}")

    st.markdown("---")
    st.header("Divergence view")
    pw = pairwise(responses)
    if pw:
        df = pd.DataFrame(pw)
        st.dataframe(df, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Strong divergence", sum(1 for r in pw if r["Assessment"] == "Strong divergence"))
        c2.metric("Moderate divergence", sum(1 for r in pw if r["Assessment"] == "Moderate divergence"))
        c3.metric("High overlap", sum(1 for r in pw if r["Assessment"] == "High overlap"))
    else:
        st.info("At least two successful responses are needed for a comparison.")

    st.subheader("Consensus signals")
    kws = consensus_keywords(responses)
    if kws:
        st.write(", ".join(kws))
    else:
        st.caption("No consensus keywords yet.")

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_name": st.session_state["session_name"],
        "question": st.session_state["question"],
        "system_prompt": st.session_state["system_prompt"],
        "responses": responses,
        "pairwise": pw,
        "consensus_keywords": kws,
        "synthesis": st.session_state["synthesis"],
    }

    st.markdown("---")
    st.header("Export")
    export_col1, export_col2, export_col3 = st.columns(3)
    export_col1.download_button(
        "Download Markdown",
        to_markdown(record),
        file_name="kobi_v2_session.md",
        mime="text/markdown",
        use_container_width=True,
    )
    export_col2.download_button(
        "Download JSON",
        to_json(record),
        file_name="kobi_v2_session.json",
        mime="application/json",
        use_container_width=True,
    )
    if export_col3.button("Save session locally", use_container_width=True):
        save_session(record)
        st.success("Session saved to data/sessions.jsonl")
else:
    st.info("Run at least one model to populate the comparison workspace.")

st.markdown("---")
st.header("Manual fallback")
st.caption("If one provider fails or you want to compare with another system manually, paste the text here.")
manual_text = st.text_area("Manual pasted answer", height=150, key="manual_answer")
manual_label = st.text_input("Manual label", value="Manual / External AI")
if st.button("Add manual response"):
    if manual_text.strip():
        st.session_state["responses"].append(
            {
                "label": manual_label,
                "provider": "Manual",
                "model": "pasted",
                "answer": manual_text,
                "error": None,
            }
        )
        st.success("Manual response added.")
    else:
        st.warning("Paste a response first.")
