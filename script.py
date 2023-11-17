import gradio as gr
import modules.shared as shared
from modules import chat
from modules.text_generation import generate_reply_HF, generate_reply_custom, apply_stopping_strings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import urllib
import re

search_access = True
service = Service()
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('--disable-infobars')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--remote-debugging-port=9222')

prompt = """"
Search for weather and tell me a quick summary.
Decide if Google Search needs to be performed. Answer with 'search' or 'no search'. If you want to search, follow 'search' with the query.
search weather
Search for most popular Pokemons.
Decide if Google Search needs to be performed. Answer with 'search' or 'no search'. If you want to search, follow 'search' with the query.
search most popular Pokemons
How are you?
Decide if Google Search needs to be performed. Answer with 'search' or 'no search'. If you want to search, follow 'search' with the query.
no search
Search for latest technology news and give overview.
Decide if Google Search needs to be performed. Answer with 'search' or 'no search'. If you want to search, follow 'search' with the query.
search latest technology news
"""

def google_results(query):

    driver = webdriver.Chrome(service=service,options=options)
    query = urllib.parse.quote_plus(query)
    url="https://www.google.com/search?hl=en&q="+query
    driver.get(url)
    html = driver.find_element(By.CLASS_NAME, 'ULSxyf').text
    driver.quit()
    return html


def ui():
    global search_access
    checkbox = gr.Checkbox(value=search_access, label="Enable Google Search")
    checkbox.change(fn=update_search_access, inputs=checkbox)
    return checkbox, search_access


def update_search_access(checkbox_value):
    global search_access
    search_access = checkbox_value  # assign the value of the checkbox to the variable
    return search_access, checkbox_value

def custom_generate_reply(question, original_question, seed, state, stopping_strings, is_chat):
    stopping_strings = ["\n"]
    print(state["last_user_msg"])
    print(state)
    input_to_search = prompt + str(state["last_user_msg"]) + "\nDecide if Google Search needs to be performed. Only answser with 'search' or 'no search'. If you want to search, follow 'search' with the query.\n"
    print("input_to_search", input_to_search)
    shared.processing_message = "*Creating search querry...*"
    generator = generate_reply_custom(input_to_search, original_question, seed, state, stopping_strings, is_chat=False)
    result = ''
    for a in generator:
        reply, stop_found = apply_stopping_strings(a, ["\n"])
        result = a
        if stop_found:
            break
    print("result", result)

    original_question = re.sub(r'(AI:)(?!.*AI:)', '', original_question)
    print("original_question", original_question)
    if result.lower().startswith("search"):
        shared.processing_message = "*Searching online...*"
        print("Searching online")
        query = result.replace("search", "").strip()
        state["context"] = state["context"] + "Relevant search results are in the Google search results. Use this info in the response."
        search_data = google_results(query)
        user_prompt = original_question + f"\nGoogle search results: {search_data}\nAI:"
    else:
        user_prompt = question
    #print("Generating response")
    print("user_prompt", user_prompt)

    generator = generate_reply_custom(user_prompt, original_question, seed, state, stopping_strings, is_chat=False)
    result = ''
    for a in generator:
        reply, stop_found = apply_stopping_strings(a, stopping_strings)
        result = a
        if stop_found:
            break
    print("result", result)
    shared.processing_message = "*Typing...*"
    yield result

def input_modifier(user_input, state):
    global search_access
    if search_access:
        state["last_user_msg"] = user_input
        #if user_input.lower().startswith("search"):
        #    shared.processing_message = "*Searching online...*"
        #    query = user_input.replace("search", "").strip()
        #    state["context"] = state["context"] + "Relevant search results are in the Google search results. Use this info in the response."
        #    search_data = google_results(query)
        #    user_prompt = f"User question: {user_input}\n Google search results: {search_data}"
        #    return str(user_prompt)
    shared.processing_message = "*Typing...*"
    return user_input

def output_modifier(output):
    return output

def bot_prefix_modifier(prefix):
    return prefix
