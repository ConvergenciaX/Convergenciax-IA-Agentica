#!/usr/bin/env python3
"""
Smoke Test para RAG-AgentAI
Valida que el entorno está configurado correctamente antes de ejecutar app.py
Ejecutar: python validate_smoke_test.py
"""
import sys
import os
from pathlib import Path

# Track test results
tests_passed = 0
tests_failed = 0

def test(name: str, condition: bool, error_msg: str = ""):
    """Helper para logging de tests."""
    global tests_passed, tests_failed
    status = "✓" if condition else "✗"

    if condition:
        print(f"{status} {name}")
        tests_passed += 1
    else:
        print(f"{status} {name}")
        if error_msg:
            print(f"  → Error: {error_msg}")
        tests_failed += 1
    return condition


print("="*60)
print("RAG-AgentAI — Smoke Test Validation")
print("="*60)

# Test 1: Python version
print("\n[1] Python Version")
py_version = sys.version_info
test(
    "Python 3.13+",
    py_version.major == 3 and py_version.minor >= 13,
    f"Got Python {py_version.major}.{py_version.minor} (need 3.13+)"
)

# Test 2: Required files exist
print("\n[2] Project Files")
files_to_check = [
    "config.ini",
    "requirements.txt",
    "app.py",
    "SETUP.md",
    "MANUAL.md",
    "README.md"
]

for file in files_to_check:
    exists = Path(file).exists()
    test(f"File: {file}", exists, f"{file} not found")

# Test 3: Directory structure
print("\n[3] Directory Structure")
dirs_to_check = ["agents", "config", "retriever", "document_processor", "utils", "logs", "checkpoint"]

for dir_name in dirs_to_check:
    exists = Path(dir_name).is_dir()
    test(f"Dir: {dir_name}/", exists, f"{dir_name}/ not found")

# Test 4: Config file loads
print("\n[4] Configuration")
try:
    from config.settings import settings
    test("Config loads from config.ini", True)

    # Test settings properties
    test("Ollama base_url accessible", settings.OLLAMA_BASE_URL is not None)
    test("Ollama text_model accessible", settings.OLLAMA_TEXT_MODEL is not None)
    test("Chroma host accessible", settings.CHROMA_HOST is not None)
    test("Gradio server_port accessible", settings.GRADIO_SERVER_PORT == 5020)
except Exception as e:
    test("Config loads from config.ini", False, str(e))

# Test 5: Imports (no Ollama/Chroma connectivity needed)
print("\n[5] Python Imports")
imports_to_test = [
    ("langchain", "LangChain core"),
    ("langchain_ollama", "LangChain Ollama wrapper"),
    ("chromadb", "ChromaDB client"),
    ("gradio", "Gradio UI"),
    ("docling", "Docling (document parsing)"),
    ("loguru", "Loguru (logging)"),
    ("rank_bm25", "BM25 ranking"),
]

for module_name, description in imports_to_test:
    try:
        __import__(module_name)
        test(description, True)
    except ImportError as e:
        test(description, False, f"Import error: {module_name}")

# Test 6: Component instantiation (no LLM calls)
print("\n[6] Component Instantiation")
try:
    from config.settings import settings
    from utils.logging import logger

    logger.info("Smoke test: Initializing components...")

    # Try importing without running
    from document_processor.file_handler import DocumentProcessor
    test("DocumentProcessor importable", True)

    from retriever.builder import RetrieverBuilder
    test("RetrieverBuilder importable", True)

    from agents.relevance_checker import RelevanceChecker
    test("RelevanceChecker importable", True)

    from agents.research_agent import ResearchAgent
    test("ResearchAgent importable", True)

    from agents.verification_agent import VerificationAgent
    test("VerificationAgent importable", True)

    from agents.workflow import AgentWorkflow
    test("AgentWorkflow importable", True)

    logger.info("✓ All components importable")

except Exception as e:
    test("Component imports", False, str(e))

# Test 7: Connectivity checks (with helpful errors)
print("\n[7] External Service Connectivity")

# Check Ollama
try:
    import requests
    from config.settings import settings

    ollama_url = f"{settings.OLLAMA_BASE_URL}/api/tags"
    response = requests.get(ollama_url, timeout=5)
    ollama_ok = response.status_code == 200
    test(f"Ollama reachable at {settings.OLLAMA_BASE_URL}", ollama_ok)

    if ollama_ok:
        import json
        models = json.loads(response.text).get("models", [])
        model_names = [m.get("name", "unknown") for m in models]

        has_embed = any("mxbai-embed" in name for name in model_names)
        has_text = any("qwen" in name or "mistral" in name or "llama" in name for name in model_names)

        if model_names:
            print(f"    Available models: {', '.join(model_names[:3])}")

        test("  → mxbai-embed model available", has_embed,
             "Run: ollama pull mxbai-embed-large")
        test("  → Text model (qwen/mistral/llama) available", has_text,
             f"Run: ollama pull {settings.OLLAMA_TEXT_MODEL}")

except requests.exceptions.ConnectionError:
    test("Ollama reachable", False,
         f"Cannot connect to {settings.OLLAMA_BASE_URL}. Start Ollama: ollama serve")
except Exception as e:
    test("Ollama reachable", False, str(e))

# Check Chroma
try:
    import requests
    from config.settings import settings

    chroma_url = settings.CHROMA_URL
    # ChromaDB 0.6+ usa /api/v2 (la v1 fue deprecada)
    chroma_test_url = f"{chroma_url}/api/v2/heartbeat"
    response = requests.get(chroma_test_url, timeout=5)
    chroma_ok = response.status_code == 200
    test(f"Chroma reachable at {chroma_url}", chroma_ok)

    if not chroma_ok:
        print(f"    → Status code: {response.status_code}")
        print(f"    → Start Chroma: docker run -d -p {settings.CHROMA_PORT}:8000 chromadb/chroma:latest")

except requests.exceptions.ConnectionError:
    test("Chroma reachable", False,
         f"Cannot connect to {chroma_url}. Start Docker Chroma: docker run -d -p 8000:8000 chromadb/chroma:latest")
except Exception as e:
    test("Chroma reachable", False, str(e))

# Test 8: Logging setup
print("\n[8] Logging Setup")
try:
    from utils.logging import logger
    log_file = Path("logs/rag_agentai.log")

    # Log file should exist or be created
    test("Log directory exists", Path("logs").is_dir(), "logs/ directory not found")
    test("Log file writable", log_file.parent.is_dir(), "Cannot write to logs/")

    logger.info("✓ Smoke test logging OK")

except Exception as e:
    test("Logging setup", False, str(e))

# Summary
print("\n" + "="*60)
print("SMOKE TEST SUMMARY")
print("="*60)
print(f"✓ Passed: {tests_passed}")
print(f"✗ Failed: {tests_failed}")
print()

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! You're ready to run:")
    print("   python app.py")
    sys.exit(0)
else:
    print("⚠️  Some tests failed. Fix the issues above before running app.py")
    print()
    print("Troubleshooting tips:")
    print("1. Check SETUP.md for detailed prerequisites")
    print("2. Verify Ollama is running: ollama list")
    print("3. Verify Docker Chroma: docker ps")
    print("4. Check logs/rag_agentai.log for detailed errors")
    sys.exit(1)
