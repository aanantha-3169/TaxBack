def get_agent(list_filters,openai_key,pinecone_key):

    import logging
    import sys
    import os
    import pandas as pd
    import pinecone
    import openai
    from llama_index import VectorStoreIndex
    from llama_index.vector_stores import PineconeVectorStore
    from llama_index.query_engine import RetrieverQueryEngine
    from llama_index.chat_engine.condense_question import CondenseQuestionChatEngine
    from llama_index.agent import OpenAIAgent
    from llama_index.llms import OpenAI
    from llama_index.tools import BaseTool, FunctionTool
    from agent_utils import get_rebate,get_tax
    from llama_index.tools import QueryEngineTool, ToolMetadata
    from llama_index.llms import ChatMessage
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
    
    #Openai and Pinecone private key
    openai.api_key = openai_key
    api_key = pinecone_key
    
    #Instantiate pinecone vector store
    pinecone.init(api_key=api_key, environment="gcp-starter")
    pinecone_index = pinecone.Index("quickstart-index")
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index
    )

    index = VectorStoreIndex.from_vector_store(vector_store)
    
    if not list_filters:
        list_filters = ['rates','claim']

    else:
        list_filters += ['rates','claim']
    #Define retriever
    retriever = index.as_retriever(
    vector_store_kwargs={"filter": {"category": {"$in":list_filters}}},streaming=True)

    # assemble query engine
    query_engine = RetrieverQueryEngine(retriever=retriever)

    #Get agent tools from agent_utils file and instantiate tools
    tax_tool = FunctionTool.from_defaults(fn=get_tax)
    relief_tool = FunctionTool.from_defaults(fn=get_rebate)

    
    #Create list of tool for agent
    tools = [
        QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="tax_relief_retriever",
                description=(
                    "Provides information on reliefs for a given item category and information on how to claim tax reliefs"
                    "Use a detailed plain text question as input to the tool."
                ),
            ),
        ),
        tax_tool,relief_tool]

    #Define chat agent
    llm = OpenAI(model="gpt-3.5-turbo-0613")
    #Set a default chat history to handle cases where information is not provided
    str_cat = ','.join(list_filters)
    chat_history = [ChatMessage(role= 'user', content=f"Assume I earn an income of RM90,000. If I state my income chat, update it to the stated income. I want to buy an items in category {str_cat}")]

    agent = OpenAIAgent.from_tools(tools, chat_history = chat_history, verbose=True)
    # chat_engine = CondenseQuestionChatEngine.from_defaults(
    #     query_engine=query_engine,
    #     # condense_question_prompt=custom_prompt,
    #     # chat_history=custom_chat_history,
    #     verbose=True,
    # )

    return agent
