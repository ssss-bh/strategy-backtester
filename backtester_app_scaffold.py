# ==== server/main.py ====
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload_excel, upload_image, backtest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_excel.router)
app.include_router(upload_image.router)
app.include_router(backtest.router)

# ==== server/routes/upload_excel.py ====
from fastapi import APIRouter, UploadFile, File
import pandas as pd
from io import BytesIO

router = APIRouter()

@router.post("/upload_excel")
def upload_excel(file: UploadFile = File(...)):
    content = file.file.read()
    if file.filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
    else:
        df = pd.read_excel(BytesIO(content))
    return {"columns": df.columns.tolist(), "rows": df.head(5).to_dict(orient="records")}

# ==== server/routes/upload_image.py ====
from fastapi import APIRouter, UploadFile, File
import shutil
import os

router = APIRouter()
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload_image")
def upload_image(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

# ==== server/routes/backtest.py ====
from fastapi import APIRouter
from strategy_engine import run_backtest

router = APIRouter()

@router.post("/run_backtest")
def run():
    result = run_backtest()
    return result

# ==== server/strategy_engine.py ====
def run_backtest():
    return {
        "summary": {
            "win_rate": 65.3,
            "rr_ratio": 1.8,
            "pnl": 1542,
            "max_drawdown": -320
        },
        "trades": [
            {"entry": "2023-01-01", "exit": "2023-01-02", "pnl": 100},
            {"entry": "2023-01-03", "exit": "2023-01-04", "pnl": -50},
        ],
        "equity_curve": [100, 200, 150, 250]
    }

# ==== requirements.txt ====
fastapi
uvicorn
pandas
openpyxl
python-multipart

# ==== client/src/components/UploadExcel.jsx ====
import React from "react";

export default function UploadExcel({ onUpload }) {
  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload_excel", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      onUpload(json);
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  return <input type="file" accept=".xlsx,.csv" onChange={handleChange} />;
}

# ==== client/src/components/UploadImage.jsx ====
import React from "react";

export default function UploadImage({ onUpload }) {
  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload_image", {
        method: "POST",
        body: formData,
      });
      const json = await res.json();
      onUpload(json.filename);
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  return <input type="file" accept="image/*" onChange={handleChange} />;
}

# ==== client/src/components/TradingViewWidget.jsx ====
import React, { useEffect } from "react";

export default function TradingViewWidget({ symbol = "BINANCE:BTCUSDT" }) {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      if (window.TradingView) {
        new window.TradingView.widget({
          container_id: "tv_chart",
          width: "100%",
          height: 500,
          symbol: symbol,
          interval: "D",
          timezone: "Etc/UTC",
          theme: "light",
          style: "1",
          locale: "en",
          toolbar_bg: "#f1f3f6",
          enable_publishing: false,
          hide_top_toolbar: true,
          withdateranges: true,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          save_image: false,
        });
      }
    };
    const chartEl = document.getElementById("tv_chart");
    if (chartEl) chartEl.innerHTML = "";
    chartEl?.appendChild(script);
  }, [symbol]);

  return <div id="tv_chart" className="w-full"></div>;
}

# ==== client/src/App.jsx ====
import React, { useState } from "react";
import UploadExcel from "./components/UploadExcel";
import UploadImage from "./components/UploadImage";
import TradingViewWidget from "./components/TradingViewWidget";

function App() {
  const [excelData, setExcelData] = useState(null);
  const [image, setImage] = useState(null);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Strategy Backtester</h1>
      <UploadExcel onUpload={setExcelData} />
      <UploadImage onUpload={setImage} />
      <TradingViewWidget symbol="BINANCE:BTCUSDT" />
      {excelData && <pre>{JSON.stringify(excelData, null, 2)}</pre>}
      {image && <img src={`http://localhost:8000/static/uploads/${image}`} alt="Uploaded chart" className="max-w-md" />}
    </div>
  );
}

export default App;
