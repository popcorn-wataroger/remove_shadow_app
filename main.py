import os
from google.cloud import storage
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import shutil
from cycle_gan_master.module_remove_shadow import remove_shadow_single_image

app = FastAPI()

# 環境変数でGCSの使用を切り替え
USE_GCS = os.getenv("USE_GCS", "false").lower() == "true"

# GCS設定
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "shadow-eraser-bucket")
storage_client = storage.Client() if USE_GCS else None

# 静的ファイルとテンプレートの設定
templates = Jinja2Templates(directory="templates")

# ローカルディレクトリ設定
UPLOAD_DIR = "uploaded"
RESULT_DIR = "results"
if not USE_GCS:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
if not USE_GCS:
    app.mount("/uploaded", StaticFiles(directory="uploaded"), name="uploaded")
    app.mount("/results", StaticFiles(directory="results"), name="results")

def upload_to_gcs(file_data, filename):
    """GCSにファイルをアップロード"""
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(file_data)
    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

def download_from_gcs(filename):
    """GCSからファイルをダウンロード"""
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"File not found in GCS: {filename}")
    return blob.download_as_bytes()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """ルートパスにアクセスしたときにアップロードフォームを表示"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "uploaded_image": None,
        "result_image": None,
    })

@app.post("/upload/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """画像をアップロードして保存"""
    # ファイル名にタイムスタンプを追加
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"

    # ファイルデータをバイナリ形式で読み込む
    file_data = await file.read()

    if USE_GCS:
        # GCSにアップロード
        uploaded_url = upload_to_gcs(file_data, unique_filename)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": uploaded_url,
            "result_image": None,
        })
    else:
        # ローカルに保存
        uploaded_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(uploaded_path, "wb") as uploaded_file:
            uploaded_file.write(file_data)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": f"/uploaded/{unique_filename}",
            "result_image": None,
        })


@app.post("/process/")
async def process_image(request: Request):
    
    """影除去処理を実行"""
    form_data = await request.form()
    uploaded_image = form_data.get("uploaded_image")
    if not uploaded_image:
        raise HTTPException(status_code=400, detail="No uploaded image found.")

    if USE_GCS:
        # GCSから画像をダウンロード
        input_filename = os.path.basename(uploaded_image)
        input_data = download_from_gcs(input_filename)

        # 一時ファイルに保存
        input_path = f"/tmp/{input_filename}"
        with open(input_path, "wb") as input_file:
            input_file.write(input_data)

        # 処理結果を一時ファイルに保存
        output_filename = f"processed_{input_filename}"
        output_path = f"/tmp/{output_filename}"
        remove_shadow_single_image(input_path=input_path, output_path=output_path)

        # 処理結果をGCSにアップロード
        with open(output_path, "rb") as output_file:
            output_data = output_file.read()
        result_url = upload_to_gcs(output_data, output_filename)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": uploaded_image,
            "result_image": result_url,
        })
    else:
        # ローカルで処理
        input_path = os.path.join(UPLOAD_DIR, os.path.basename(uploaded_image))
        output_path = os.path.join(RESULT_DIR, f"processed_{os.path.basename(uploaded_image)}")
        remove_shadow_single_image(input_path=input_path, output_path=output_path)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": uploaded_image,
            "result_image": f"/results/processed_{os.path.basename(uploaded_image)}",
        })


@app.post("/download/")
async def download_image(request: Request):
    form_data = await request.form()
    uploaded_image = form_data.get("uploaded_image")
    result_image = form_data.get("result_image")

    if not uploaded_image or not result_image:
        raise HTTPException(status_code=400, detail="No images to download.")

    result_filename = os.path.basename(result_image)

    if USE_GCS:
        # GCSからダウンロード（再保存は不要）
        result_data = download_from_gcs(result_filename)
        temp_path = f"/tmp/{result_filename}"
        with open(temp_path, "wb") as f:
            f.write(result_data)

        return FileResponse(
            path=temp_path,
            media_type="image/jpeg",
            filename=result_filename,
        )

    else:
        # ローカル保存処理
        saved_dir = "saved"
        os.makedirs(saved_dir, exist_ok=True)
        source_result_path = os.path.join(RESULT_DIR, result_filename)
        saved_path = os.path.join(saved_dir, result_filename)

        if os.path.exists(source_result_path):
            shutil.copy(source_result_path, saved_path)

        return FileResponse(
            path=saved_path,
            media_type="image/jpeg",
            filename=result_filename,
        )


    
@app.get("/clear/")
async def clear_files(request: Request):
    """アップロードされたファイルや処理結果を削除"""
    if not USE_GCS:
        # ローカルディレクトリのファイルを削除
        for folder in [UPLOAD_DIR, RESULT_DIR]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        # 初期画面に戻す
        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": None,
            "result_image": None,
        })
    else:
        # ここでは削除処理を省略し、テンプレートを初期化
        return templates.TemplateResponse("index.html", {
            "request": request,
            "uploaded_image": None,
            "result_image": None,
        })