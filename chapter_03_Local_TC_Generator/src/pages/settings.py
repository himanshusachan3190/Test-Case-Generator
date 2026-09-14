import streamlit as st

from config_store import get_setting, load_config, save_config
from jira_client import AuthenticationError, JiraError, test_connection

st.set_page_config(page_title="Settings", page_icon="⚙️")

config = load_config()

st.title("⚙️ Settings")
st.caption("Local configuration for Jira access and local test-case generation mode.")

with st.form("settings_form"):
    jira_url = st.text_input("Jira URL", value=config.get("jira_url", ""))
    jira_email = st.text_input("Jira Email", value=config.get("jira_email", ""))
    jira_api_token = st.text_input("Jira API Token", value=config.get("jira_api_token", ""), type="password")
    llm_provider = st.selectbox("Generation Mode", ["local", "ollama", "groq"], index=["local", "ollama", "groq"].index((config.get("llm_provider") or "local")))
    groq_api_key = st.text_input("Groq API Key", value=config.get("groq_api_key", ""), type="password")

    if st.form_submit_button("Save Settings"):
        save_config(
            {
                "jira_url": jira_url,
                "jira_email": jira_email,
                "jira_api_token": jira_api_token,
                "llm_provider": llm_provider,
                "groq_api_key": groq_api_key,
            }
        )
        st.success("Settings saved locally.")

if st.button("Test Jira Connection"):
    try:
        result = test_connection()
        st.success(f"Jira connection successful: {result}")
    except AuthenticationError as exc:
        st.error(f"Authentication failed: {exc}")
    except JiraError as exc:
        st.error(f"Connection failed: {exc}")

st.markdown("---")
st.caption("This app is configured to generate test cases locally without requiring Ollama or Groq.")
