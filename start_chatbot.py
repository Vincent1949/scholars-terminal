"""
Unified Knowledge Chatbot V8 - Startup Script
Automatically updates database and launches chatbot
"""

import os
import sys
import logging
import subprocess
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_INITIALIZER = None
DB_LAST_RESULT = None


def check_ollama_status():
    """Check if Ollama is running."""
    try:
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            logger.info(f"Ollama is running with {len(models)} models")
            return True
    except Exception:
        pass

    logger.warning("Ollama is not running. Attempting to start Ollama...")

    try:
        if os.name == "nt":
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Wait longer for Ollama to fully initialize (especially on slower systems)
        time.sleep(15)

        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            logger.info("Ollama started successfully")
            return True

    except Exception as e:
        logger.error(f"Failed to start Ollama: {e}")

    return False


def update_database():
    """
    Initialize and/or update the vector database on startup.

    We use ONE shared vector store for BOTH sources.
    DatabaseInitializer (in database_initializer.py) does the real work.
    """
    global DB_INITIALIZER, DB_LAST_RESULT

    logger.info("\nChecking for database updates...")

    try:
        from database_initializer import DatabaseInitializer
    except ImportError as e:
        logger.error(f"Could not import DatabaseInitializer: {e}")
        DB_LAST_RESULT = {"status": "error", "message": str(e)}
        return DB_LAST_RESULT

    try:
        if DB_INITIALIZER is None:
            # must match your actual DatabaseInitializer signature
            DB_INITIALIZER = DatabaseInitializer(
                books_path="D:/Books",
                github_path="D:/GitHub",
                github_db_path="D:/Claude/Projects/scholars-terminal/data/vector_db",
            )

        # 🔴 THIS was causing the error:
        # update_result = DB_INITIALIZER.initialize_and_update()

        # ✅ THIS is the method your class actually has now:
        update_result = DB_INITIALIZER.scan_and_update()

        DB_LAST_RESULT = update_result

        status = update_result.get("status", "unknown")

        if status == "updated":
            logger.info(
                f"Processed {update_result.get('books_processed', 0)} new book files"
            )
            logger.info(
                f"Processed {update_result.get('github_processed', 0)} new GitHub files"
            )
        elif status == "error":
            logger.error(
                f"Database initialization error: {update_result.get('message', 'Unknown error')}"
            )
        else:
            logger.info("Databases are already up to date")

        return update_result

    except Exception as e:
        logger.exception(f"Unexpected error during database initialization: {e}")
        DB_LAST_RESULT = {"status": "error", "message": str(e)}
        return DB_LAST_RESULT


def start_background_db_update():
    """Kick off DB update in a background thread so startup isn't blocked."""
    logger.info("Spawning background database updater thread...")
    t = threading.Thread(target=update_database, daemon=True)
    t.start()
    return t


def refresh_databases():
    """Manual refresh that reuses the same initializer."""
    logger.info("\nManual database refresh initiated...")
    return update_database()


def launch_chatbot():
    """Launch the main chatbot interface."""
    logger.info("Launching Unified Knowledge Chatbot V8...")

    try:
        from unified_knowledge_chatbot_v8_enhanced import create_gradio_interface

        interface = create_gradio_interface()
        logger.info("Chatbot is ready!")
        logger.info("Access at: http://localhost:7860")

        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            inbrowser=True,
        )

    except Exception as e:
        logger.error(f"Failed to launch chatbot: {e}")
        raise


def main():
    print(
        """
    ==============================================
             VIRTUAL SPACE COMPUTERS
      Unified Knowledge Chatbot V8 (Ollama)
    ==============================================
    """
    )

    logger.info("Starting initialization sequence.")

    # 1. Check packages
    logger.info("Checking required packages...")
    required_packages = [
        "gradio",
        "chromadb",
        "sentence-transformers",
        "PyPDF2",
        "python-docx",
        "ebooklib",
        "beautifulsoup4",
        "numpy",
        "requests",
        "PyCryptodome",
        "python-dotenv",
    ]

    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    if missing:
        logger.warning(f"Missing packages: {missing}")
        logger.info("Installing missing packages...")
        for pkg in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        logger.info("Packages installed.")
    else:
        logger.info("All required packages are available.")

    # 2. Check Ollama
    logger.info("Checking Ollama status...")
    ollama_ready = check_ollama_status()

    if not ollama_ready:
        logger.warning("Ollama is not available. LLM features will be limited.")
        resp = input("Continue without Ollama? (y/n): ")
        if resp.lower() != "y":
            logger.info("Exiting...")
            return

    # 3. Start DB update in background
    start_background_db_update()

    # 4. Launch UI
    logger.info("============================================================")
    launch_chatbot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Chatbot shutdown complete.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        input("Press Enter to exit...")
