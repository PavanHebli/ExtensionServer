from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from ollama import chat
from ollama import ChatResponse
from tqdm import tqdm
from ollama import pull, list as ollamaList
from groq import Groq

import re
from bs4 import BeautifulSoup
import asyncio

def ChromeHeadless(headless = True):
    chrome_options = Options()
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    
    if headless:
        chrome_options.add_argument("--headless=new") # for Chrome >= 109
        chrome_options.add_argument(f'user-agent={user_agent}')
        # chrome_options.add_argument("--headless")
        # chrome_options.headless = True # also works
    return chrome_options


def OpenBrowser(headless=True):
    driver=webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=ChromeHeadless(headless),
        # desired_capabilities=capa
        )
    print("Driver loaded!")
    return driver

def GetURLData(driver, name):
    try:
        driver.switch_to.window(f"{name}")
        driver.execute_script("window.stop();")
        html=driver.page_source
        print("[INFO] GetURLData: Data Received ")
        print(name, driver.title)
        driver.close()
    except Exception as e:
        html=""
        print(f"[ERROR] GetURLData: Exception Occured\n{e} ")
    return html

def OpenURL(driver, url, name):
    driver.execute_script(f"window.open('{url}', '{name}');")
    pass

def GetBodyStrings(html):
    soup = BeautifulSoup(html, "html.parser")
    # Get the whole body tag
    tag = soup.body
    concatString=""
    # Print each string recursively
    for string in tag.strings:
        concatString=concatString + " " +string.strip()
    return concatString

def ExtractUrls(urls):
    urlList=[]
    index=0
    for url in urls.urlArray:
        if url.startswith("http"):
            index+=1
            print(url)
            urlList.append(url)
            if index == 5:
                break
    return urlList

async def Summarize(urls, userString, driver):
    urlList=ExtractUrls(urls)
    history=""
    allSummaries=""
    driver.implicitly_wait(6) # wait for 5 seconds
    initial_tab_handle=driver.current_window_handle
    for index, url in enumerate(urlList):
        OpenURL(driver, url, f"tab_{index}")
    for index in range(len(urlList)):
        html=GetURLData(driver, f"tab_{index}")
        if html:
            print(index)
            FullText = GetBodyStrings(html)
            history = count_words_and_stop(FullText, urls.search, "")
            allSummaries=f"{allSummaries}\n{history}"
    prompt=f"{allSummaries}\n{userString}"
    driver.switch_to.window(initial_tab_handle)
    return GroqModels(prompt)

def count_words_and_stop(text, url, history, word_limit=90000):
    # Split text into sentences using regular expressions to handle punctuation
    sentences = re.split(r'(?<=[.!?]) +', text)
    total_words = 0
    selected_sentences = []
    userString=f"based on the above give me an as exact aswer as possible to {url} in 500 words"
    includeURL=True
    word_count_history = len(history.split())
    for sentence in sentences:
        sentence=sentence.strip()
        word_count = len(sentence.split())
        if total_words + word_count + word_count_history > word_limit:
            final_text = ' '.join(selected_sentences)
            history=GenerateQuery(userString, final_text, history)
            total_words=0
            selected_sentences = []
            word_count_history = len(history.split())
        selected_sentences.append(sentence)
        total_words += word_count
    final_text = ' '.join(selected_sentences)
    history=GenerateQuery(userString, final_text, history)
    return history

def format_paragraph(text):
    # Replace newlines and special characters with a space
    textList=text.split()
    formatted_text = " ".join(textList)
    return formatted_text

def GenerateQuery(prompt: str, data: str, history:str):
    completePrompt=f"{prompt}: \n{history}\n{data}"
    history=GroqModels(completePrompt)
    history=format_paragraph(history)
    # print(history, "\n")
    return history

def DownloadModel(modelName):
    current_digest, bars = '', {}
    for progress in pull(modelName, stream=True):
        digest = progress.get('digest', '')
        if digest != current_digest and current_digest in bars:
            bars[current_digest].close()
        if not digest:
            print(progress.get('status'))
            continue
        if digest not in bars and (total := progress.get('total')):
            bars[digest] = tqdm(total=total, desc=f'pulling {digest[7:19]}', unit='B', unit_scale=True)
        if completed := progress.get('completed'):
            bars[digest].update(completed - bars[digest].n)

        current_digest = digest

def is_model_downloaded(modelName):
    """
    Check if the given model is already downloaded.
    """
    modelsList = ollamaList()
    for model in modelsList["models"]:
        if model["model"] == modelName:
            return True
    return False

def LLMModels(strings, modelSelect="llama3.2:3b", stream=False):
    #TODO: Create a seperate file for prompts
    userString1=f"Your are an Expert in summarizing the informationbased on the information provided to provide an aswer as accurate as possible in 500 words. "
    userString2=f"Also based on the information received "
    userString3=f""
    userString4=f""
    userString5=f""
    systemCommand=f"{userString1} {userString2} {userString3} {userString4} {userString5}"
    # Check if the model is already downloaded
    if not is_model_downloaded(modelSelect):
        print(f"Model '{modelSelect}' is not downloaded. Downloading now...")
        DownloadModel(modelSelect)
        print(f"Model '{modelSelect}' downloaded successfully.")
    else:
        print(f"Model '{modelSelect}' is already downloaded.")
    response: ChatResponse = chat(model=modelSelect, messages=[
    {
        'role':'system',
        'content':f'{systemCommand}',
        'role': 'user',
        'content': f'{strings}',
    },
    ],
    stream=stream)
    return response['message']['content']

def GroqModels(strings, modelSelect="llama-3.1-8b-instant", stream=False): # llama-3.1-8b-instant
    #TODO: Create a seperate file for prompts
    userString1=f"Your are an Expert in summarizing the informationbased on the information provided to provide an aswer as accurate as possible in 500 words. "
    userString2=f"Also based on the information received "
    userString3=f""
    userString4=f""
    userString5=f""
    systemCommand=f"{userString1} {userString2} {userString3} {userString4} {userString5}"
    client = Groq(
        api_key=""
    )
    completion = client.chat.completions.create(
        model=modelSelect,
        messages=[
            {
                'role':'system',
                'content':f'{systemCommand}',
                "role": "user",
                "content": f"{strings}"
            }
        ],
        temperature=1,
        max_tokens=8000,
        top_p=1,
        stream=stream,
        stop=None,
    )
    return completion.choices[0].message.content