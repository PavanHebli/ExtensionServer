from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from groq import Groq
import anthropic
import re
from bs4 import BeautifulSoup
import asyncio
import time

def ChromeHeadless(headless = True):
    chrome_options = Options()
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    
    if headless:
        chrome_options.add_argument("--headless=new") # for Chrome >= 109
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument(f"page_load_strategy=none")
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

def GetHTML(url, driver):
    pass


# def GetHTML(url, driver, className='body', explicit=10):
#     # driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=ChromeHeadless(headless))
#     driver.get(url)
#     html=None    
#     try:
#         # myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
#         if className == 'body':
#             myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.TAG_NAME, className)))
#         elif className:
#             myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
#         print ("Page is ready!")
#         html = driver.page_source
#         driver.quit()
#     except TimeoutException:
#         print( "Loading took too much time!")
#     return html

# async def async_GetHTML(url, headless=True, className='body', explicit=10):
#     # Run the synchronous GetHTML in a separate thread
#     return await asyncio.to_thread(GetHTML, url, headless, className, explicit)


def GetBodyStrings(html):
    soup = BeautifulSoup(html, "html.parser")
    # Get the whole body tag
    tag = soup.body
    concatString=""
    if tag:
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
            # word_count=0
            selected_sentences = []
            word_count_history = len(history.split())
            # print(f"Resetting everything...")
        selected_sentences.append(sentence)
        total_words += word_count
        # print(f"----->>>",total_words,"  ",len(' '.join(selected_sentences).split()))
    # outside of loop
    final_text = ' '.join(selected_sentences)
    # print(f"This is the end of the loop...")
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
    # history=AnthropicModels(completePrompt)
    print("--> GenerateQuery Called")
    history=format_paragraph(history)
    return history


def GroqModels(strings, modelSelect="llama-3.1-8b-instant", stream=False): # llama-3.1-8b-instant
    textList=strings.split()
    # print(f"Word Length send to LLaMa Model: {len(textList)}")
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


def AnthropicModels(strings):
    print("calling Claude haiku 3.5")
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key="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",
    )

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=20000,
        temperature=0,
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{strings}"
                }
            ]
        }
    ]
    )
    return message.content