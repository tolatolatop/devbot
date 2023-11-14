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
            "You are a very good python engineer. Please complete the following actions according to user needs."
            "Modify files according to the task to complete the task."
            "Submit tasks to the warehouse through tools."
            "If you have not submitted a PR before, please submit a PR through the tool.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
