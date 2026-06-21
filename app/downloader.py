import os
import re
import shutil
from pathlib import Path
from typing import Literal, Optional

import yt_dlp

# bgutil-ytdlp-pot-provider 1.3.1 的 bug：在 debug() 呼叫時多傳了 once=True，
# 但 IEContentProviderLogger.debug() 不接受該參數。
# 在此透過 monkey-patch 讓 debug() 能接受並忽略多餘的 keyword arguments。
try:
    from yt_dlp.extractor.youtube.pot._director import YoutubeIEContentProviderLogger as _YtLogger
    _orig_debug = _YtLogger.debug

    def _debug_compat(self, message: str, **_):
        return _orig_debug(self, message)

    _YtLogger.debug = _debug_compat
except Exception:
    pass

DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED_BROWSERS = ("chrome", "safari", "firefox", "brave", "edge", "chromium")
DEFAULT_BROWSER = os.environ.get("YTDLP_BROWSER", "chrome")
HAS_FFMPEG = shutil.which("ffmpeg") is not None
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
UNRECOVERABLE_ERROR_MARKERS = (
    "drm protected",
)


def _cookie_opts(browser: str) -> dict:
    if browser not in SUPPORTED_BROWSERS:
        browser = DEFAULT_BROWSER
    return {"cookiesfrombrowser": (browser,)}


def _strategies(browser: Optional[str] = None) -> list[dict]:
    """依序嘗試的下載策略。android_vr 目前最穩定，且不需要 cookies。"""
    strategies = [
        {
            "extractor_args": {
                "youtube": {"player_client": ["android_vr"]},
            },
        },
        {
            "extractor_args": {
                "youtube": {"player_client": ["tv"]},
            },
        },
    ]

    if browser and browser != "auto":
        strategies.append({
            **_cookie_opts(browser),
            "extractor_args": {
                "youtube": {"player_client": ["web", "mweb"]},
            },
        })

    return strategies


def _common_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,
    }


def _clean_error_message(exc: Exception) -> str:
    return ANSI_RE.sub("", str(exc)).strip()


def _is_unrecoverable_error(exc: Exception) -> bool:
    msg = _clean_error_message(exc).lower()
    return any(marker in msg for marker in UNRECOVERABLE_ERROR_MARKERS)


def _friendly_error(exc: Exception) -> str:
    msg = _clean_error_message(exc)
    if "drm protected" in msg.lower():
        return (
            "此影片受 DRM 保護，yt-dlp 無法下載。"
            "請改用未受 DRM 保護的影片；如果是播放清單中的其中一支，請略過該影片。"
        )
    if "Sign in to confirm" in msg or "not a bot" in msg:
        return (
            "YouTube 要求驗證身分。請在進階選項選擇已登入 YouTube 的瀏覽器後重試。"
        )
    if "403" in msg or "Forbidden" in msg:
        return (
            "YouTube 拒絕下載請求（403 Forbidden）。請稍後再試，"
            "或在進階選項選擇已登入 YouTube 的瀏覽器。"
        )
    if "ffmpeg" in msg.lower() or "ffprobe" in msg.lower():
        return "音訊轉檔需要 FFmpeg，請執行：brew install ffmpeg"
    if "could not find" in msg.lower() and "cookies" in msg.lower():
        return (
            "無法讀取瀏覽器 cookies。請確認已安裝該瀏覽器並登入 YouTube；"
            "macOS 可能需在「系統設定 → 隱私權 → 完整磁碟取用權限」允許終端機。"
        )
    if "not available" in msg.lower() and "format" in msg.lower():
        return "找不到可用的影片格式，請稍後再試。"
    if "Video unavailable" in msg or "unavailable" in msg.lower():
        return "此影片無法存取（可能有地區限制或已被移除）。"
    # 去掉 yt-dlp 的 [youtube] 前綴，留下純訊息
    if msg.startswith("["):
        parts = msg.split(":", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return msg


def _extract_with_fallback(
    url: str,
    extra_opts: dict,
    browser: Optional[str] = None,
    download: bool = False,
) -> dict:
    last_error: Optional[Exception] = None

    for strategy_opts in _strategies(browser):
        ydl_opts = {**_common_opts(), **strategy_opts, **extra_opts}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_error = e
            if _is_unrecoverable_error(e):
                break
            continue

    raise RuntimeError(_friendly_error(last_error or RuntimeError("下載失敗")))


def get_video_info(url: str, browser: Optional[str] = None) -> dict:
    """取得影片基本資訊（不下載）。"""
    try:
        info = _extract_with_fallback(url, {}, browser=browser, download=False)
        return {
            "title": info.get("title", "未知標題"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
        }
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(_friendly_error(e)) from e


def _resolve_output_file(title: str, preferred_ext: Optional[str] = None) -> tuple[Path, str]:
    if preferred_ext:
        candidate = DOWNLOAD_DIR / f"{title}.{preferred_ext}"
        if candidate.exists():
            return candidate, candidate.name

    for f in DOWNLOAD_DIR.iterdir():
        if f.stem == title and f.is_file():
            return f, f.name

    raise FileNotFoundError(f"找不到下載檔案：{title}")


def download(
    url: str,
    mode: Literal["video", "audio"],
    browser: Optional[str] = None,
    audio_format: Literal["m4a", "mp3"] = "m4a",
) -> dict:
    """下載 YouTube 影片或音訊，回傳檔案資訊。"""
    extra_opts = {
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
    }

    if mode == "video":
        extra_opts["format"] = "18/best[ext=mp4]/best"
        preferred_ext = "mp4"
    elif audio_format == "mp3":
        if not HAS_FFMPEG:
            raise RuntimeError(
                "MP3 轉檔需要 FFmpeg，請先安裝：brew install ffmpeg（macOS）"
                " 或參閱 README.md 的安裝說明。"
            )
        extra_opts["format"] = "bestaudio/best"
        extra_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
        preferred_ext = "mp3"
    else:
        extra_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        preferred_ext = "m4a"

    try:
        info = _extract_with_fallback(url, extra_opts, browser=browser, download=True)
        title = info.get("title", "download")
        filepath, filename = _resolve_output_file(title, preferred_ext)
        return {
            "title": title,
            "filename": filename,
            "filepath": str(filepath),
            "mode": mode,
            "audio_format": audio_format if mode == "audio" else None,
        }
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(_friendly_error(e)) from e
