from typing import Union
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import server_helper as sh


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URL(BaseModel):
    search: str
    urlArray: list

@app.get("/test/")
def read_root():
    return {"Hello": "World"}

@app.post("/summary")
async def GetSummary(urls: URL):
    start_time = time.time()
    userString1=f"based on the information provided give as detailed answer as possible {urls.search} in 500 words in html format (H tags and P tags) to be able to paste directly in a div tag."
    userString2=f"Also based on the information provided give list of meaningful questions and their asnwers upto 5 to help understand more about the topic for which you have detailed answers"
    userString3=f"it is fine if you do not have any meaningful questions because you covered everything but if you have questions strictly start them as '##' on a new line"
    userString4=f"and below that strictly start each question with #Q(number) and answers #A(number) E.g. #Q1,  #A1 , #Q2 and so on in plain text without HTML format."
    userString5=f"This will help me to split he text. strictly do not start like 'here is your answer in html format' or any kind of introduction before the answer like that."
    userString=f"{userString1} {userString2} {userString3} {userString4} {userString5}"

    print("--->",len(userString.split()))
    # summary=sh.Summarize(urls, userString)
    summary = await sh.Summarize(urls, userString)
    print("#"*50)
    print(summary)
    print(f"\n\n--- {round((time.time() - start_time), 2)} seconds ---")
    return summary




