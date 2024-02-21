from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Dataset:
    def __init__(self, id: int, filename: str, size: int):
        self.id = id
        self.filename = filename
        self.size = size

datasets = {}

@app.get("/csv/")
async def list_datasets():
    response_data = {"datasets": []}
    for dataset_id, dataset in datasets.items():
        response_data["datasets"].append({
            "id": dataset_id,
            "filename": f"dataset_{dataset_id}.csv",
            "size": len(dataset)
        })
    return response_data

@app.post("/csv/")
async def create_dataset(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file, sep=';')
        dataset_id = len(datasets) + 1
        datasets[dataset_id] = df
        return {"id": dataset_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/csv/{dataset_id}/")
async def get_dataset_info(dataset_id: int):
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    df = datasets[dataset_id]
    return {"filename": f"dataset_{dataset_id}.csv", "size": len(df)}

@app.delete("/csv/{dataset_id}/")
async def delete_dataset(dataset_id: int):
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    del datasets[dataset_id]
    return JSONResponse(content={"message": "Dataset deleted successfully"})

@app.get("/csv/{dataset_id}/plot/")
async def generate_plot(dataset_id: int):
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = datasets[dataset_id]

    try:
        # Assuming your dataset has columns 'email', 'invoicing date', and 'amount'
        df['invoicing date'] = pd.to_datetime(df['invoicing date'])
        df['month'] = df['invoicing date'].dt.to_period('M')
        
        # Group by 'email' and 'month' and sum the amounts excluding 'invoicing date'
        formatted_dataset = df.groupby(['email', 'month'])['amount'].sum().reset_index()
        formatted_dataset = formatted_dataset.pivot(index='month', columns='email', values='amount')
        formatted_dataset = formatted_dataset.fillna(0)
        
        # Convert the formatted dataset to a list of dictionaries for JSON response
        formatted_data_list = formatted_dataset.to_dict(orient='list')
        
        return formatted_data_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))