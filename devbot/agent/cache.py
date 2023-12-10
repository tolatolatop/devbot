import hashlib
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.chat_models import ChatOpenAI


def llm_cache(llm: ChatOpenAI, cache_storage):
    def www(chat_prompt: ChatPromptTemplate):
        hash_data = hash_chat_prompt(chat_prompt)
        if hash_data in cache_storage:
            return cache_storage[hash_data]
        else:
            resp = llm(chat_prompt)
            cache_storage[hash_data]
            return resp

    return RunnableLambda(www)


def hash_chat_prompt(chat_prompt: ChatPromptTemplate) -> str:
    md5 = hashlib.md5()
    data = chat_prompt.to_json()
    str_data = ""
    for k, v in data.items():
        str_data = f"{k}:{v}\n"
    md5.update(str_data.encode())
    return md5.hexdigest()
