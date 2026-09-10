"""DocChat RAG — Constants (file size limits, allowed types)."""

# File upload constraints
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500 MB for all files combined
ALLOWED_TYPES = [".pdf", ".docx", ".txt", ".md"]
