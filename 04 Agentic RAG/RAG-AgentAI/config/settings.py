"""DocChat RAG — Settings loaded from config.ini (not .env)."""
import configparser
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Settings:
    """Load settings from config.ini file."""

    def __init__(self, config_file="config.ini"):
        self.config = configparser.ConfigParser()
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file '{config_file}' not found. "
                                  "Please create it based on the template in MANUAL.md.")

        self.config.read(config_file)
        logger.info(f"Configuration loaded from '{config_file}'")

    # ===== Ollama settings =====
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return self.config.get("ollama", "base_url", fallback="http://localhost:11434")

    @property
    def OLLAMA_TEXT_MODEL(self) -> str:
        return self.config.get("ollama", "text_model", fallback="qwen2.5:7b-instruct-q4_K_M")

    @property
    def OLLAMA_TIMEOUT(self) -> int:
        return self.config.getint("ollama", "timeout", fallback=180)

    @property
    def OLLAMA_KEEP_ALIVE(self) -> str:
        return self.config.get("ollama", "keep_alive", fallback="10m")

    @property
    def OLLAMA_TEMPERATURE(self) -> float:
        return self.config.getfloat("ollama", "temperature", fallback=0.1)

    @property
    def OLLAMA_TOP_P(self) -> float:
        return self.config.getfloat("ollama", "top_p", fallback=0.9)

    @property
    def OLLAMA_NUM_PREDICT(self) -> int:
        return self.config.getint("ollama", "num_predict", fallback=300)

    # ===== Embeddings settings =====
    @property
    def EMBEDDING_MODEL(self) -> str:
        return self.config.get("embeddings", "embedding_model", fallback="mxbai-embed-large")

    # ===== Document Processor settings (Docling + OCR) =====
    @property
    def DOCLING_ARTIFACTS_PATH(self) -> str:
        """Ruta local con modelos pre-descargados de Docling (layout, tablas, etc.)."""
        return self.config.get("document_processor", "docling_artifacts_path", fallback="./models/docling")

    @property
    def DOCLING_DO_OCR(self) -> bool:
        """Habilitar OCR en PDFs con imágenes (usar easyocr)."""
        return self.config.getboolean("document_processor", "do_ocr", fallback=True)

    @property
    def DOCLING_OCR_MODELS_PATH(self) -> str:
        """Ruta local con modelos pre-descargados de EasyOCR."""
        return self.config.get("document_processor", "docling_ocr_models_path", fallback="./models/easyocr")

    # ===== Chroma settings =====
    @property
    def CHROMA_HOST(self) -> str:
        return self.config.get("chroma", "host", fallback="localhost")

    @property
    def CHROMA_PORT(self) -> int:
        return self.config.getint("chroma", "port", fallback=8000)

    @property
    def CHROMA_COLLECTION_NAME(self) -> str:
        return self.config.get("chroma", "collection_name", fallback="rag_agentai_documents")

    @property
    def CHROMA_URL(self) -> str:
        """Construct Chroma HTTP URL."""
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"

    # ===== RAG settings =====
    @property
    def VECTOR_SEARCH_K(self) -> int:
        return self.config.getint("rag", "vector_search_k", fallback=10)

    @property
    def ENSEMBLE_WEIGHTS(self) -> list:
        """Parse "weight1,weight2" format from config."""
        weights_str = self.config.get("rag", "ensemble_weights", fallback="0.4,0.6")
        return [float(w.strip()) for w in weights_str.split(",")]

    @property
    def MAX_CONTEXT_DOCS(self) -> int:
        return self.config.getint("rag", "max_context_docs", fallback=5)

    # ===== Gradio settings =====
    @property
    def GRADIO_SERVER_NAME(self) -> str:
        return self.config.get("gradio", "server_name", fallback="127.0.0.1")

    @property
    def GRADIO_SERVER_PORT(self) -> int:
        return self.config.getint("gradio", "server_port", fallback=5020)

    @property
    def GRADIO_SHARE(self) -> bool:
        return self.config.getboolean("gradio", "share", fallback=False)

    # ===== Logging settings =====
    @property
    def LOG_LEVEL(self) -> str:
        return self.config.get("logging", "level", fallback="INFO")

    @property
    def LOG_DIR(self) -> str:
        log_dir = self.config.get("logging", "log_dir", fallback="logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    @property
    def LOG_FILE(self) -> str:
        return self.config.get("logging", "log_file", fallback="rag_agentai.log")

    @property
    def LOG_MAX_SIZE_MB(self) -> int:
        return self.config.getint("logging", "log_max_size_mb", fallback=10)

    @property
    def LOG_BACKUP_COUNT(self) -> int:
        return self.config.getint("logging", "log_backup_count", fallback=5)


# Global settings instance
try:
    settings = Settings(config_file="config.ini")
except FileNotFoundError as e:
    logger.error(str(e))
    raise SystemExit(1)
