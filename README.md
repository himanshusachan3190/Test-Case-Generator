# Jira Test Case Generator

This chapter contains a local Streamlit application that fetches a Jira issue,
uses its description as the requirement source, and generates structured test
cases in Markdown format.

The current implementation uses a local deterministic generator. It does not
require Ollama or Groq.

## Features

- Accepts natural-language requests containing a Jira key, for example:
  `create test cases for SCRUM-1`
- Fetches Jira issue data through the Jira REST API
- Supports Jira Cloud ADF descriptions and plain-text descriptions
- Extracts:
  - issue key
  - summary
  - description
  - acceptance criteria when available
- Loads the prompt template from `templates/testcase_creator.md`
- Generates a Markdown table with:
  - Test ID
  - Description
  - Pre-conditions
  - Steps
  - Expected Result
  - Priority
- Provides a Settings page for Jira configuration
- Saves generated test cases under `templates/`

## Project structure

```text
chapter_03_Local_TC_Generator/
├── README.md
├── requirements.txt
├── src/
│   ├── app.py
│   ├── config_store.py
│   ├── jira_client.py
│   ├── llm_client.py
│   ├── .env
│   └── pages/
│       └── settings.py
└── templates/
    ├── testcase_creator.md
    └── SCRUM-1_test_cases.md
```

## Requirements

- Python 3.10 or newer
- Access to a Jira Cloud project
- A Jira email address
- A Jira API token

Python packages are listed in [requirements.txt](./requirements.txt).

## Configuration

Create or update `src/.env`:

```dotenv
JIRA_URL=https://your-site.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
```

The configuration loader also accepts the existing mixed-case
`Jira_EMAIL` variable name for compatibility.

Do not commit `.env` or `config.json`. They contain credentials and local
runtime settings. The repository `.gitignore` excludes both files.

## Installation

From this chapter directory:

```powershell
cd chapter_03_Local_TC_Generator
python -m pip install -r requirements.txt
```

## Run the application

The Streamlit entry point is inside `src`:

```powershell
cd chapter_03_Local_TC_Generator/src
streamlit run app.py
```

Open the local URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## Usage

1. Open the application.
2. Open **Settings** from the sidebar.
3. Confirm the Jira URL, email, and API token.
4. Use **Test Jira Connection** to verify access.
5. Return to the chat screen.
6. Enter a request containing a Jira key:

   ```text
   create test cases for SCRUM-1
   ```

7. Submit the request.
8. Review the generated Markdown test-case table.

## Generated output

The application generates a local Markdown file when the generation flow is
run programmatically or from an automation wrapper. The expected output
location is:

```text
templates/<JIRA-KEY>_test_cases.md
```

For example:

```text
templates/SCRUM-1_test_cases.md
```

## Module responsibilities

### `src/app.py`

Runs the Streamlit chat interface, extracts Jira keys, fetches ticket details,
loads the template, generates test cases, and renders the result.

### `src/config_store.py`

Loads values from `.env`, merges them with optional `config.json` settings, and
provides configuration helpers to the rest of the application.

### `src/jira_client.py`

Calls Jira REST API endpoints, normalizes the Jira base URL, converts ADF
descriptions to text, and reports authentication, connection, and not-found
errors.

### `src/llm_client.py`

Provides the local generation path used by this version of the application.
It does not call Ollama, Groq, or another external LLM provider.

### `src/pages/settings.py`

Provides the Streamlit settings screen for Jira configuration and connection
testing.

### `templates/testcase_creator.md`

Defines the expected test-case table format and generation rules.

## Troubleshooting

### Jira authentication failed

Check that:

- `JIRA_URL` is the Jira site URL, not a board URL
- `JIRA_EMAIL` matches the account that created the API token
- `JIRA_API_TOKEN` is active and has access to the project

### Ticket not found

Confirm that the Jira key exists and that the configured account can view it.

### No Jira key detected

Include a key in the request using the standard format:

```text
PROJECT-123
```

### Port already in use

Start Streamlit on another local port:

```powershell
streamlit run app.py --server.port 8502
```

## Security notes

- Never hardcode Jira credentials in Python files.
- Never commit `.env` or `config.json`.
- Treat Jira API tokens as passwords.
- Do not paste credentials into issue descriptions, generated test cases, or
  source control.
