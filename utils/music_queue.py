"""Queue management classes for the music playback system."""

from typing import Optional, List


class Track:
    """Represents a single track with title, webpage URL, and raw metadata."""

    def __init__(self, title: str, webpage_url: str, raw_data: dict):
        """Initializes a Track object.

        Args:
            title (str): The track's title.
            webpage_url (str): The primary URL (e.g., YouTube link).
            raw_data (dict): The raw metadata as returned by yt-dlp.
        """
        self.title = title
        self.webpage_url = webpage_url
        self.raw_data = raw_data


class MusicQueue:
    """A queue structure for managing tracks in playback order."""

    def __init__(self):
        """Initializes an empty MusicQueue."""
        self._queue: List[Track] = []

    def add(self, track: Track) -> None:
        """Adds a single track to the queue.

        Args:
            track (Track): The track to be queued.
        """
        self._queue.append(track)

    def add_multiple(self, tracks: List[Track]) -> None:
        """Adds multiple tracks to the queue at once.

        Args:
            tracks (List[Track]): A list of Track objects to enqueue.
        """
        self._queue.extend(tracks)

    def pop_next(self) -> Optional[Track]:
        """Removes and returns the first track in the queue.

        Returns:
            Optional[Track]: The next track, or None if the queue is empty.
        """
        return self._queue.pop(0) if self._queue else None

    def clear(self) -> None:
        """Clears all items from the queue."""
        self._queue.clear()

    def is_empty(self) -> bool:
        """Indicates whether the queue is empty.

        Returns:
            bool: True if no tracks are in the queue, otherwise False.
        """
        return len(self._queue) == 0

    def __len__(self) -> int:
        """Returns the number of tracks in the queue."""
        return len(self._queue)

    def __iter__(self):
        """Enables iteration over the queue."""
        return iter(self._queue)
