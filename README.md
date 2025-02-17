# Taint-FM Discord Bot

Taint-FM is a Discord bot that provides YouTube audio playback functionality. It supports queuing YouTube videos (or playlists), downloading the audio locally before playing (to avoid streaming issues), and managing playback with commands to join voice channels, skip tracks, view the queue, and more. Any downloaded audio is removed post song completion or skip.

## Features

- **Join**: The bot joins your current voice channel.
- **Play**: Queue a YouTube video or playlist for playback. The bot downloads the audio locally, queues it, and plays it from your voice channel.
- **Skip**: Skip the currently playing track.
- **Queue**: Display the list of tracks in the queue.
- **Clear**: Clear the entire playback queue.
- **Leave**: Disconnect the bot from the voice channel.

## Commands

Below are the available commands:

- **`!join`**  
  **Usage:** `!join`  
  **Description:** Joins the voice channel of the user who invoked the command.

- **`!play <url>`**  
  **Usage:** `!play https://www.youtube.com/watch?v=XYZ`  
  **Description:** Loads a YouTube video or playlist and queues it for playback. The audio is downloaded to a temporary directory (`/tmp/taint-fm`) before playing.

- **`!skip`**  
  **Usage:** `!skip`  
  **Description:** Skips the currently playing track.

- **`!queue`**  
  **Usage:** `!queue`  
  **Description:** Displays the current music queue.

- **`!clear`**  
  **Usage:** `!clear`  
  **Description:** Clears the current music queue.

- **`!leave`**  
  **Usage:** `!leave`  
  **Description:** Disconnects the bot from the current voice channel.

## Local Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/cbtibs/taint-fm.git
   cd taint-fm
   ```
2. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```
3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Configure your bot:**
      Create a .env file or update your configuration to include your Discord Bot Token.

5. **Run the bot:**
    ```bash
    python bot.py
    ```

## TODO:
* Add `!pause` and `!resume`
* Add queue pagination
* Add persistent queues, `!loop` and `!shuffle`
* Add `!volume`
* Tweak FFMPEG options
* Dockerize
