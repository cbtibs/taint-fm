# utils/youtube_extractor.py

import os
import yt_dlp
import tempfile
import logging

logger = logging.getLogger(__name__)

class YouTubeExtractor:
    """Handles YouTube extraction logic with flat extraction and on-demand downloads."""

    def __init__(self):
        """Initializes the YouTubeExtractor with flat extraction for metadata."""
        # We'll do a flat extraction to retrieve minimal data (titles, etc.)
        self.meta_extractor_options = {
            "format": "bestaudio/best",
            "ignoreerrors": True,
            "nocheckcertificate": True,
            "restrictfilenames": True,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
            "noplaylist": False,
            "extract_flat": True,
        }
        self.meta_ytdl = yt_dlp.YoutubeDL(self.meta_extractor_options)

        # Ensure our download directory exists
        self.download_dir = "/tmp/taint-fm"
        os.makedirs(self.download_dir, exist_ok=True)

    def extract_playlist_info(self, url: str) -> dict:
        """Extracts basic/flat info for a playlist or single video without downloading.

        Args:
            url (str): The YouTube or playlist URL.

        Returns:
            dict: Metadata. If it's a playlist, the dict may contain 'entries'.
        """
        return self.meta_ytdl.extract_info(url, download=False)

    def download_audio_file(self, url: str) -> str:
        """Downloads the audio track for the given URL into /tmp/taint-fm.

        Args:
            url (str): The YouTube (or other site) URL to download.

        Returns:
            str: The local file path to the downloaded audio file.
        """
        # We'll let yt-dlp choose the correct extension (e.g. webm, m4a, opus).
        # outtmpl places it in /tmp/taint-fm with a generated base name.
        outtmpl = os.path.join(self.download_dir, "taint-fm-%(id)s.%(ext)s")

        # Download options for best audio
        download_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "ignoreerrors": False,  # So we get an exception if something is wrong
            "nocheckcertificate": True,
            "restrictfilenames": True,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
            "noplaylist": True,  # Only download a single item
        }

        with yt_dlp.YoutubeDL(download_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # The extension used by YT-DLP
        final_ext = info_dict.get("ext", "webm")  
        video_id = info_dict.get("id", "unknown")

        # This matches our outtmpl pattern "taint-fm-%(id)s.%(ext)s"
        final_path = os.path.join(self.download_dir, f"taint-fm-{video_id}.{final_ext}")

        # Check if file actually exists and log some debug info
        if not os.path.isfile(final_path):
            logger.error("Downloaded file not found at %s", final_path)
            raise FileNotFoundError(f"Download failed or file missing: {final_path}")

        size = os.path.getsize(final_path)
        logger.info("Downloaded file: %s (size: %s bytes)", final_path, size)

        # If size is suspiciously small (e.g., 0), it might be an error file
        if size < 1024:  # just an arbitrary small threshold
            logger.warning(
                "File %s is very small. Could be an error page or truncated download.",
                final_path
            )

        return final_path
