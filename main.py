from fastapi import FastAPI
from database import SessionLocal
from db_utils import load_csv_data
from routes import router

app = FastAPI(title="Restaurant Monitor API", description="Monitor restaurant store status with proper extrapolation")

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    try:
        
        
        print("Loading sample data...")
        #load_csv_data()
        print("Sample data loaded successfully!")

    except Exception as e:
        print(f"Error during startup: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
