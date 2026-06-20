# YouTube 下載器

一個具備 Web UI 的 YouTube 影片／音訊下載工具，支援：

- **下載影片** — MP4 格式
- **下載音訊** — M4A 格式（無需額外套件）或 MP3 格式（需要 FFmpeg）

## 環境需求

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/)（下載 MP3 格式時必須，M4A 格式不需要）

### 安裝 FFmpeg

**macOS（Homebrew）**

```bash
brew install ffmpeg
```

**Ubuntu / Debian**

```bash
sudo apt update && sudo apt install -y ffmpeg
```

**Windows**

1. 若系統已啟用 `winget`，可直接在 PowerShell 執行：

```powershell
winget install --id=Gyan.FFmpeg -e
```

2. 如果不想使用 `winget`，請前往 [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) 下載 Windows 版本，或使用可靠第三方編譯版本，例如：
   - https://www.gyan.dev/ffmpeg/builds/
   - https://www.gyan.dev/ffmpeg/builds/

3. 下載「Static」版本 ZIP，解壓到資料夾，例如 `C:\ffmpeg`。

4. 將 `C:\ffmpeg\bin` 加入系統 PATH：
   - 開啟「設定」>「系統」>「關於」>「進階系統設定」>「環境變數」
   - 在「系統變數」中找到 `Path`，編輯並新增 `C:\ffmpeg\bin`

5. 重新啟動 PowerShell。

6. 驗證安裝是否成功：

```powershell
ffmpeg -version
```

安裝完成後重新啟動服務即可使用 MP3 格式；若未安裝 FFmpeg 而選擇 MP3，下載時會顯示錯誤提示。

> 安裝完成後重新啟動服務即可使用 MP3 格式；若未安裝 FFmpeg 而選擇 MP3，下載時會顯示錯誤提示。

## 安裝與啟動

```bash
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 啟動服務
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

瀏覽器開啟 [http://localhost:8000](http://localhost:8000) 即可使用。

## 使用方式

1. 在輸入框貼上 YouTube 影片網址
2. 選擇「下載影片」或「下載音訊」
3. 若選擇音訊，可進一步選擇格式：
   - **M4A** — 直接下載，不需要 FFmpeg
   - **MP3** — 需要系統已安裝 FFmpeg（見上方安裝說明）
4. 點擊「開始下載」
5. 下載完成後點擊「儲存檔案」

預設使用 **自動模式**，不需要登入 YouTube。若出現機器人驗證錯誤，可展開「進階選項」選擇已登入 YouTube 的瀏覽器。

若出現 cookies 讀取失敗，macOS 使用者可能需在「系統設定 → 隱私權與安全性 → 完整磁碟取用權限」中，允許終端機（Terminal）或 Python。

檔案會儲存在專案根目錄的 `downloads/` 資料夾。

## 專案結構

```
youtube-downloader/
├── app/
│   ├── main.py          # FastAPI 後端
│   ├── downloader.py    # yt-dlp 下載邏輯
│   └── static/          # Web UI
├── downloads/           # 下載檔案存放處
├── requirements.txt
└── README.md
```

## 注意事項

本工具僅供個人學習使用，請尊重版權，勿用於商業用途或散佈受版權保護的內容。
