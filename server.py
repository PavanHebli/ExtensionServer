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
    # using proper headings with 'H' tags paragrpah with 'P' tags
    # and wrap all the code in HTML'<pre>' tag
    # so that your output can be used as is to make your output easy to read
    userString1= f"{urls.search} Provide an exact explainantion to the given query. use HTML H and p tags for headings and paragraphs, your response will be used in an webpage as is "
    userString2=f"do not include head or start with DOCTYPE only use HTML tags. strictly use HTML code tag and no script tags to show any script or code in a code block."
    userString3=f""
    # and 'pre' tags for the code snippents to only show the code without rendering output in browser which will make it 
    userString=userString1+userString2+userString3
    print("--->",len(userString.split()))
    # summary=sh.Summarize(urls, userString)
    summary = await sh.Summarize(urls, userString)
    print("#"*50)
    print(summary)
    print(f"\n\n--- {round((time.time() - start_time), 2)} seconds ---")
    return summary