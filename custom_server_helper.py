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


# driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=ChromeHeadless())
# driver.implicitly_wait(10)
# driver.get(url)
# html = driver.page_source
# driver.quit()

def GetHTML(url, headless=True, className='body', explicit=10):
    driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=ChromeHeadless(headless))
    driver.implicitly_wait(10)
    driver.get(url)
    html=None    
    try:
        # myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
        if className == 'body':
            myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.TAG_NAME, className)))
        elif className:
            myElem = WebDriverWait(driver, explicit).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
        print ("Page is ready!")
        html = driver.page_source
        driver.quit()
    except TimeoutException:
        print( "Loading took too much time!")
    return html

async def async_GetHTML(url, headless=True, className='body', explicit=10):
    # Run the synchronous GetHTML in a separate thread
    return await asyncio.to_thread(GetHTML, url, headless, className, explicit)


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
            if index == 2:
                break
    return urlList

async def Summarize(urls, userString):
    urlList=ExtractUrls(urls)
    history=""
    coros=[]
    for index, url in enumerate(urlList):
        coros.append(async_GetHTML(url))
        # if index == 4:
        #     break
        # html=GetHTML(url)
    html_results = await asyncio.gather(*coros)
    # for html, url in zip(html_results, urlList[:5]):
    for html, url in zip(html_results, urlList):
        FullText = GetBodyStrings(html)
        # print(url)
        history = count_words_and_stop(FullText, url, history)

    prompt=f"{history}\n{userString}"
    # print("--->",len(history.split()))
    return LLMModels(prompt)



def count_words_and_stop(text, url, history, word_limit=90000):
    # Split text into sentences using regular expressions to handle punctuation
    sentences = re.split(r'(?<=[.!?]) +', text)
    total_words = 0
    selected_sentences = []
    userString=f"give me a detailed summary the following within 500 words"
    includeURL=True
    word_count_history = len(history.split())
    for sentence in sentences:
        sentence=sentence.strip()
        word_count = len(sentence.split())
        # print("word count bug ::",len(sentence),len(sentence.split()) )
        # If adding this sentence exceeds the word limit, stop
        if total_words + word_count + word_count_history > word_limit:
            final_text = ' '.join(selected_sentences)
            # if includeURL:
            #     userString=f"give me a summary in 1000 words {url}"
            #     includeURL=False

            # print(f"{total_words} (total words), {word_count} (word count)\n{len(selected_sentences)} (sentence length)")
            # temp_final_text = len(final_text.split())
            # temp_history = len(history.split())
            
            # print(f"{temp_final_text} (final text) + = {temp_history} (history) = {temp_final_text+temp_history} total")
            
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
    history=LLMModels(completePrompt)
    # history=AnthropicModels(completePrompt)
    history=format_paragraph(history)
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
    userString1=f"Your are an Expert in summarizing the information, Now based on the information provided give as detailed answer as possible in 1000 words "
    userString2=f"Also based on the information provided give list of meaningful questions and their asnwers upto 5 to help understand more about the topic for which you have detailed answers "
    userString3=f"if you think you covered everything it is fine if you do not have any meaningful questions "
    userString4=f"but if you have any strictly write '@@' on a new line and then after the new line start each question with #Q(number) and answers #A(number) E.g. #Q1,  #A1 , #Q2 and so on "
    userString5=f"in plain text without HTML format. This will help me to split the text. remember do not start like 'here is your answer in html format' or any kind of introduction before the answer like that."
    systemCommand=f"{userString1} {userString2} {userString3} {userString4} {userString5}"
    # Check if the model is already downloaded
    if not is_model_downloaded(modelSelect):
        print(f"Model '{modelSelect}' is not downloaded. Downloading now...")
        DownloadModel(modelSelect)
        print(f"Model '{modelSelect}' downloaded successfully.")
    else:
        print(f"Model '{modelSelect}' is already downloaded.")
    # print(f"Word Length send to LLaMa Model: {len(textList)}")
    response: ChatResponse = chat(model=modelSelect, messages=[
    {
        'role':'system',
        'content':f'{systemCommand}',
        'role': 'user',
        'content': f'{strings}',
    },
    ],
    stream=stream)
    # or access fields directly from the response object
    #print(response['message']['content'])
    return response['message']['content']