import re
from pathlib import Path

import streamlit as st

from config_store import load_config
from jira_client import (
    AuthenticationError,
    ConnectionError,
    JiraError,
    NotFoundError,
    fetch_ticket,
)
from llm_client import LLMError, generate

st.set_page_config(page_title="Jira Test Case Generator", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR.parent / "templates"


@st.cache_data
def load_template(name: str = "testcase_creator.md") -> str:
    path = TEMPLATE_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def build_prompt(ticket: dict, template: str) -> str:
    description = ticket.get("description") or ""
    acceptance = ticket.get("acceptance_criteria") or ""
    requirements = description
    if acceptance:
        requirements += f"\n\nAcceptance Criteria:\n{acceptance}"

    if not requirements.strip():
        requirements = ticket.get("summary", "No requirement details were provided")

    prompt_template = template.replace("[NUMBER]", "4")
    prompt_template = prompt_template.replace("[PASTE REQUIREMENTS HERE]", requirements)
    return prompt_template


def clean_output(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0]

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|")]
    if not table_lines:
        return cleaned

    has_header = len(table_lines) >= 2 and "Test ID" in table_lines[0]
    if has_header:
        return "\n".join(table_lines)
    return "\n".join([table_lines[0], "| --- | --- | --- | --- | --- | --- |", *table_lines[1:]])


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("## ⚙️ App Info")
    config = load_config()
    provider = config.get("llm_provider", "local")
    st.caption(f"**Mode:** {provider.upper()}")
    jira_url = config.get("jira_url", "")
    st.caption(f"**Jira:** {jira_url or 'Not configured'}")
    if not jira_url:
        st.warning("Configure Jira in Settings before generating test cases.")
    st.markdown("---")
    st.page_link("pages/settings.py", label="Open Settings")

st.title("🧪 Jira Test Case Generator")
st.caption("Use a Jira ticket key like SCRUM-1 or QA-102 to generate a test case draft.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt_text := st.chat_input("Generate test cases for a Jira issue..."):
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    match = re.search(r"\b[A-Z]+-\d+\b", prompt_text)
    if not match:
        response = (
            "I could not find a Jira ticket key in your message. "
            "Please include one like `SCRUM-1` or `QA-102`."
        )
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
    else:
        ticket_key = match.group(0)
        with st.chat_message("assistant"):
            try:
                with st.status(f"Fetching ticket **{ticket_key}** from Jira...", expanded=True):
                    ticket = fetch_ticket(ticket_key)
                template = load_template()
                if not template:
                    response = "Template file not found in the `templates` folder."
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.markdown(response)
                else:
                    prompt = build_prompt(ticket, template)
                    with st.status("Generating a local draft of the test cases...", expanded=True):
                        raw = generate(prompt)
                        result = clean_output(raw)
                    response = f"### {ticket_key}: {ticket['summary']}\n\n{result}"
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.markdown(response)
            except (AuthenticationError, ConnectionError) as exc:
                response = f"❌ Configuration Error: {exc}\n\nGo to Settings and fix the Jira configuration."
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.error(exc)
            except NotFoundError as exc:
                response = f"❌ {exc}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.error(exc)
            except JiraError as exc:
                response = f"❌ Jira Error: {exc}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.error(exc)
            except LLMError as exc:
                response = f"❌ Local generation error: {exc}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.error(exc)
            except Exception as exc:
                response = f"❌ Unexpected Error: {exc}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.error(exc)
