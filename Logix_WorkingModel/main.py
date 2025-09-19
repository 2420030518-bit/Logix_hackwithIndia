import os
import uvicorn
import pathway as pw
import threading
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# --- API Key Authentication ---
API_KEY = os.getenv("BACKEND_API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- NEW: Pathway Live Data Pipeline ---
# This is our mock live data source (e.g., a news feed)
mock_live_data = [
    {"id": 1, "headline": "Pathway raises $5M for real-time data processing", "source": "TechCrunch"},
    {"id": 2, "headline": "The future of AI is real-time, says Pathway CEO", "source": "VentureBeat"},
    {"id": 3, "headline": "How to build a real-time search engine with Python", "source": "Blogpost"},
]

# Define the data schema for Pathway
class NewsArticle(pw.Schema):
    id: int
    headline: str
    source: str

# Set up the Pathway table from our mock data
news_table = pw.debug.Table.from_list(mock_live_data, schema=NewsArticle)

# This is our global variable to store results from Pathway
pathway_results = []

def run_pathway_pipeline(query_term: str):
    """
    This function defines and runs the Pathway pipeline.
    """
    global pathway_results
    # We define a query that filters the table based on the headline
    results = news_table.filter(pw.this.headline.contains(query_term, case_sensitive=False))
    
    # We use pw.debug.collect to get the results out of the pipeline
    # In a real app, this would connect to a live output like Kafka or a database
    pathway_results = pw.debug.collect(results)
    print(f"Pathway pipeline ran. Found {len(pathway_results)} results for '{query_term}'.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Logix Research API",
    description="API for the Logix AI Research Assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# --- Pydantic Models for Request Data ---
class ResearchQuery(BaseModel):
    query: str

# --- API Endpoints ---
@app.post("/api/research", dependencies=[Depends(get_api_key)])
async def research(request: ResearchQuery):
    print(f"Received query: {request.query}")
    
    # --- NEW: Run the Pathway pipeline in a thread ---
    # We run the pipeline in a separate thread so it doesn't block the API
    pathway_thread = threading.Thread(target=run_pathway_pipeline, args=(request.query,))
    pathway_thread.start()
    pathway_thread.join() # Wait for the thread to finish

    # Return the results collected from the pipeline
    return {"status": "success", "live_data_results": pathway_results}

# --- Serve Frontend ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse, include_in_schema=False)
async def read_root():
    return 'static/index.html'

# --- Run the App ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)