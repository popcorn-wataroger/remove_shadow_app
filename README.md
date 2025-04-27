# CycleGANベースの影除去API

このプロジェクトは、**FastAPI** を使ったWebアプリケーションで、**CycleGANモデル**による画像変換（例：顔写真の影除去）をHTTP API経由で実行できます。

**Docker** 対応で、**Google Cloud Run** へのデプロイも簡単にできる設計になっています。

---

## ✨ 主な機能

- 画像をアップロードすると、**影を除去した変換画像**を返却
- **PyTorch CycleGANモデル**による推論
- **FastAPI** による軽量・非同期対応APIサーバー
- **Dockerコンテナ化**によりどこでも動作
- **Cloud Run** や **Vertex AI Workbench** へのデプロイを想定

---

## 🛠️ 使用技術
- Python 3.10
- FastAPI
- Uvicorn
- PyTorch
- Docker
- Google Cloud Run

---

## 📦 プロジェクト構成

my-cyclegan-app/ ├── app/ │ ├── main.py # FastAPIエントリーポイント │ ├── shadow_removal.py # CycleGAN推論関数 │ ├── model.py # Generator / Discriminator定義 │ ├── utils.py # 補助的な関数 │ └── models/ # 学習済みモデル（.pthファイル） ├── requirements.txt # Python依存ライブラリ ├── Dockerfile # Dockerビルド用ファイル └── README.md # 本ドキュメント

---

## 🚀 セットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/あなたのGitHubアカウント/my-cyclegan-app.git
cd my-cyclegan-app
```
### 2. Dockerイメージをビルド
```bash
docker build -t cyclegan-api .
```
### 3. ローカルで起動
```bash
docker run -p 8080:8080 cyclegan-api
```
ブラウザで http://localhost:8080/docs にアクセスすると、Swagger UI（APIドキュメント）が確認できます！

---

## 📷 APIエンドポイント
```
POST /convert-a2b/
```
アップロードされた画像を、CycleGANモデルで影除去変換し、**変換後の画像（PNG）**を返します。

### 🔹 リクエスト仕様

- **HTTPメソッド**：`POST`
- **エンドポイントURL**：`/convert-a2b/`
- **リクエスト形式**：`multipart/form-data`
- **送信するデータ**：
  - フィールド名：`file`
  - 内容：変換したい**画像ファイル**（JPG, PNGなど）

### 🔹 レスポンス仕様

- **HTTPステータス**：`200 OK`
- **レスポンス内容**：
  - 変換後の画像ファイル（**PNG形式**）

### 🔹 具体例（curlコマンド）

以下のコマンドで、ローカルサーバーに画像をアップロードし、  
変換後の画像を `output_image.png` として保存します。


例（curlコマンド）：
```bash
curl -X POST "http://localhost:8080/convert-a2b/" \
  -H "accept: image/png" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@input_image.jpg" \
  --output output_image.png
```
レスポンス：変換後の画像ファイル（PNG形式）

---

## ☁️ Google Cloud Runへのデプロイ手順（オプション）
### 1. Google Cloud Buildでビルド
```bash
gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/cyclegan-api
```
### 2. Cloud Runにデプロイ
```bash
gcloud run deploy cyclegan-api \
  --image gcr.io/<YOUR_PROJECT_ID>/cyclegan-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```
※ Cloud Runが自動でスケールし、サーバレスで公開されます。

---

## 🧠 今後の改善アイデア
- ユーザー認証機能（OAuth2/JWT）
- 非同期キューを使ったバックグラウンド処理
- Reactなどを使ったアップロード用フロントエンド実装

