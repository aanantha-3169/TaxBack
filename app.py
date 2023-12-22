import streamlit as st
import openai
import pandas as pd
from agent import get_agent
from agent_utils import get_query
import base64

st.set_page_config(page_title="Tax Discounts", page_icon="🎅🏼", layout="centered", initial_sidebar_state="auto", menu_items=None)


openai.api_key = st.secrets["openai_key"]
st.title("Don't Stop Shopping yet! 🛍️")

# Initialize session state
if 'my_df' not in st.session_state:
    st.session_state['my_df'] = pd.DataFrame(columns=["Items", "Check"])

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "It's almost time! Create a list of items you would like to buy and let me help you understand if you can get a tax relief for it?"}
    ]
st.info("The agent will assume your annual income is RM90,000 unless you state otherwise", icon=None)

# Function to add items to the DataFrame
def add_items():
    st.session_state['my_df'] = pd.DataFrame(columns=["Items", "Check"])
    items_list = items_input.split(',')
    # items_set = set(items_list)
    # distinct_list = list(items_set)
    # Truncate list to 10 items if more are entered
    items_list = items_list[:10]
    for item in items_list:
        #print(item)
        response = get_query(item.strip())
        #print(response)
        st.session_state['my_df'].loc[len(st.session_state['my_df'])] = [item.strip(), response]

with st.sidebar:
    st.title("📝 Create your wish list here:")
  
    st.warning("Note: This agent attempts to give helpful information but may be wrong at time.", icon=None)  

    # User input for all items
    items_input = st.text_input("Enter items eg. iphone,sports shoes etc.(10 MAX)")

    # Button to add items
    add_items_button = st.button("Add Items to List", on_click=add_items)

    if add_items_button and len(st.session_state['my_df'].loc[st.session_state['my_df']['Check'] != 'False','Items'].to_list()) > 0 :
        # Display the DataFrame
        st.write("After check, the following items are tax deductible:")
        st.balloons()
        deduc_items = st.session_state['my_df'].loc[st.session_state['my_df']['Check'] != 'False','Items'].to_list()

        str_items = ','.join(deduc_items)
        st.success(str_items, icon="✅")

    # Multiselect widget for selecting items
    if not st.session_state['my_df'].empty:
        all_categories = ['lifestyle', 'sports', 'personal_computer','education','tourism','parent_care','medical']
        selected_items = st.multiselect("Select Items you would like to chat on", st.session_state['my_df'].loc[st.session_state['my_df']['Check'] != 'False','Items'].to_list())
        # Filter the DataFrame based on selected items
        filtered_df = st.session_state['my_df'][st.session_state['my_df']['Items'].isin(selected_items)]

        # Get the 'Check' values from the filtered DataFrame
        if not filtered_df.empty:
            distinct_values = set(filtered_df['Check'])
            distinct_list = list(distinct_values)

            # Determine unselected categories
            unselected_categories = [cat for cat in all_categories if cat not in distinct_list]

            # Input widget for unselected categories
            additional_selection = st.multiselect("Don't miss out! Here are some other items you get a relief on. Select and let's chat:", unselected_categories)
            combined_selection = distinct_list
            # Update distinct_list with combined_selection
            if additional_selection:
                combined_selection.append(additional_selection)
                chat_bot = get_agent(combined_selection,st.secrets["openai_key"],st.secrets["pinecone_key"])
            
            chat_bot = get_agent(distinct_list,st.secrets["openai_key"],st.secrets["pinecone_key"])
            
# Main Page for Chat
if prompt := st.chat_input("Ask your question here"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            try:
                response = chat_bot.chat(prompt)
                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message) # Add response to message history

            except:
                generic_bot = get_agent([],st.secrets["openai_key"],st.secrets["pinecone_key"])
                response = generic_bot.chat(prompt)
                st.write(response.response)
                st.info('Create a list of items you would like to buy in the sidebar to have a more details conversation.', icon="ℹ️")
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message) # Add response to message history
