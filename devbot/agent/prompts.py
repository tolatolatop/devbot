from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

summary_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, but bad at summarizing thingws.",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

issue_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful coding assistant."
            "Please answer the question based on the actual contents of repo."
            "You are allowed to use tools to view "
            "the repository and specific files",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

coding_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a very good python engineer. Please complete user needs by following actions."
            "Modify files to complete the task by update_file function."
            "Submit tasks to the repo by function commit_task."
            "If you have not submitted a PR before, please submit a PR through create_pull_request.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
