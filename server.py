from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # <--- NEW IMPORT
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# --- FIX: ALLOW BROWSERS TO CONNECT FROM PORT 5500 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" means "Allow everyone". You can also use ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],
)
# -----------------------------------------------------

templates = Jinja2Templates(directory="templates")

# Store items here
detected_items = []

class GroceryItem(BaseModel):
    name: str

# --- WEBPAGE ROUTES ---
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- API ROUTES ---
@app.get("/api/items")
async def get_items():
    return detected_items

@app.post("/api/add")
async def add_item(item: GroceryItem):
    if item.name not in detected_items:
        detected_items.insert(0, item.name)
        print(f"Server: Added {item.name}")
    return {"status": "success"}

@app.post("/api/clear")
async def clear_list():
    detected_items.clear()
    return {"status": "cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)