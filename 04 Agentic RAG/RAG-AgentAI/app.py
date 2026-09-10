"""DocChat RAG — Gradio web UI for agentic RAG (Ollama + Chroma local + LangGraph)."""
import os

# Configurar modo offline ANTES de importar cualquier librería que use HuggingFace
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import gradio as gr
import hashlib
import requests
import re
from typing import List, Dict, Optional, Tuple
import logging

# Import our modules
from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from agents.workflow import AgentWorkflow
from config import constants
from config.settings import settings
from utils.logging import logger

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)

# Example documents and questions
EXAMPLES = {
    "Reporte Ambiental Google 2024": {
        "question": "¿Cuáles son los valores de eficiencia PUE del centro de datos en la segunda instalación de Singapur en 2019 y 2022? ¿Cuál es el promedio regional de CFE en Asia Pacífico en 2023?",
        "file_paths": ["examples/google-2024-environmental-report.pdf"]
    },
    "Reporte Técnico DeepSeek-R1": {
        "question": "Resumir la evaluación de desempeño del modelo DeepSeek-R1 en todas las tareas de codificación en comparación con el modelo OpenAI o1-mini",
        "file_paths": ["examples/DeepSeek Technical Report.pdf"]
    }
}


def _preflight_checks(retriever_builder: RetrieverBuilder) -> Tuple[bool, str]:
    """Verificar que Ollama y Chroma responden. Retorna (ok, mensaje)."""
    msg = []

    # Check Ollama
    try:
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
        if resp.status_code == 200:
            msg.append("✓ Ollama: OK")
        else:
            msg.append(f"⚠️  Ollama responde con {resp.status_code}")
    except Exception as e:
        msg.append(f"❌ Ollama NO responde ({type(e).__name__}). Asegúrate de ejecutar 'ollama serve'")

    # Check Chroma (with fallback to v2 API if v1 deprecated)
    try:
        resp = requests.get(f"{settings.CHROMA_URL}/api/v1/heartbeat", timeout=2)
        if resp.status_code == 200:
            msg.append("✓ ChromaDB: OK")
        elif resp.status_code == 501 or "deprecated" in resp.text.lower():
            # Fallback to v2 if v1 is deprecated
            resp = requests.get(f"{settings.CHROMA_URL}/api/v2/heartbeat", timeout=2)
            if resp.status_code == 200:
                msg.append("✓ ChromaDB: OK (v2)")
            else:
                msg.append(f"⚠️  ChromaDB responde con {resp.status_code}")
        else:
            msg.append(f"⚠️  ChromaDB responde con {resp.status_code}")
    except Exception as e:
        msg.append(f"❌ ChromaDB NO responde ({type(e).__name__}). Ejecuta: chroma run --host localhost --port 8000")

    ok = all("✓" in m for m in msg)
    return ok, "\n".join(msg)


def main():
    """Launch the Gradio web UI for DocChat RAG."""
    logger.info("=== DocChat RAG Initialization ===")
    logger.info(f"Modo offline: HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}, "
               f"TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')}")

    # Initialize the three main components
    try:
        processor = DocumentProcessor()
        retriever_builder = RetrieverBuilder()
        workflow = AgentWorkflow()
        logger.info("✓ All components initialized successfully")

        # Preflight checks
        ok, check_msg = _preflight_checks(retriever_builder)
        logger.info("Preflight checks:\n" + check_msg)
        if not ok:
            logger.warning("⚠️  Some services may not be available; check logs above")

    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}", exc_info=True)
        raise

    # CSS styling
    css = """
    .title {
        font-size: 1.5em !important;
        text-align: center !important;
        color: #00d4ff;
    }
    .subtitle {
        font-size: 1em !important;
        text-align: center !important;
        color: #00d4ff;
    }
    .text {
        text-align: center;
    }
    """

    # Gradio blocks UI
    with gr.Blocks(theme=gr.themes.Ocean(), title="DocChat RAG", css=css) as demo:
        gr.Markdown("## DocChat RAG: RAG agéntico local 🌊", elem_classes="subtitle")
        gr.Markdown("### Powered by Ollama + Chroma + LangGraph", elem_classes="subtitle")
        gr.Markdown("# ¿Cómo funciona? ✨:", elem_classes="title")
        gr.Markdown("📤 Sube documentos, ingresa tu pregunta, presiona Enviar 📝", elem_classes="text")
        gr.Markdown("O carga un ejemplo del menú desplegable 🛠️", elem_classes="text")
        gr.Markdown("⚠️ Formatos soportados: `.pdf`, `.docx`, `.txt`, `.md`", elem_classes="text")

        # Session state for caching retrievers
        session_state = gr.State({
            "file_hashes": frozenset(),
            "selected_collections": frozenset(),
            "retriever": None
        })

        # Tabs: Query + Explore indexed documents
        with gr.Tabs():
            # Tab 1: Query (Preguntar sobre documentos)
            with gr.Tab("💬 Preguntar", id="query"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Cargar Ejemplo 📂")
                        example_dropdown = gr.Dropdown(
                            label="Selecciona un ejemplo",
                            choices=list(EXAMPLES.keys()),
                            value=None
                        )
                        load_example_btn = gr.Button("Cargar Ejemplo 🛠️")

                        gr.Markdown("### O Reutiliza Colecciones 📚")
                        existing_collections = gr.Dropdown(
                            label="Colecciones indexadas",
                            choices=retriever_builder.list_collections(),
                            multiselect=True,
                            interactive=True
                        )
                        refresh_collections_btn = gr.Button("🔄 Refrescar colecciones")

                        gr.Markdown("### O Sube Documentos Nuevos 📄")
                        files = gr.Files(label="Subir documentos", file_types=constants.ALLOWED_TYPES)

                        gr.Markdown("### Ingresa tu Pregunta ❓")
                        question = gr.Textbox(label="Pregunta", lines=3, placeholder="Pregunta algo sobre los documentos...")

                        submit_btn = gr.Button("Enviar 🚀", variant="primary")

                    with gr.Column():
                        gr.Markdown("### Resultados 📊")
                        answer_output = gr.Textbox(
                            label="Respuesta Generada",
                            interactive=False,
                            lines=10
                        )
                        verification_output = gr.Textbox(
                            label="Reporte de Verificación",
                            interactive=False,
                            lines=5
                        )

            # Tab 2: Query indexed collections (sin subir docs nuevos) + ChromaDB health
            with gr.Tab("❓ Consultar Colecciones", id="query_collections"):
                gr.Markdown("### Preguntar sobre documentos ya indexados")

                with gr.Row():
                    with gr.Column():
                        collection_selector = gr.Dropdown(
                            label="Selecciona colecciones",
                            choices=retriever_builder.list_collections(),
                            multiselect=True,
                            interactive=True
                        )
                        refresh_query_collections_btn = gr.Button("🔄 Refrescar colecciones")

                        # Feature 2: "Usar todas las colecciones" checkbox
                        use_all_collections_checkbox = gr.Checkbox(
                            label="✅ Usar TODAS las colecciones disponibles",
                            value=False,
                            interactive=True
                        )

                        collection_question = gr.Textbox(
                            label="Tu pregunta",
                            lines=3,
                            placeholder="Pregunta algo sobre los documentos seleccionados..."
                        )
                        query_collections_btn = gr.Button("Enviar ❓", variant="primary")

                    with gr.Column():
                        collection_answer_output = gr.Textbox(
                            label="Respuesta",
                            interactive=False,
                            lines=10
                        )
                        collection_verification_output = gr.Textbox(
                            label="Reporte de Verificación",
                            interactive=False,
                            lines=5
                        )

                # Feature 3: ChromaDB Health Status Panel
                gr.Markdown("---")
                gr.Markdown("### 🩺 Estado de ChromaDB")

                with gr.Row():
                    with gr.Column():
                        check_health_btn = gr.Button("🔄 Verificar salud", variant="secondary")
                    with gr.Column():
                        pass

                chroma_health_output = gr.Markdown(label="Estado de ChromaDB")

            # Tab 3: Index RAG documents + Upload & Optimize
            with gr.Tab("📚 Indexar RAG Documentos", id="explore"):
                gr.Markdown("### Documentos indexados en ChromaDB")

                with gr.Row():
                    with gr.Column():
                        explore_dropdown = gr.Dropdown(
                            label="Selecciona documento",
                            choices=retriever_builder.list_collections(),
                            interactive=True
                        )
                        explore_btn = gr.Button("🔍 Explorar", variant="primary")
                        refresh_explore_btn = gr.Button("🔄 Refrescar lista")

                    with gr.Column():
                        doc_info_output = gr.Markdown(label="Información del documento")

                with gr.Row():
                    doc_content_output = gr.Markdown(label="Chunks")

                # Feature 1: Upload & Optimize section
                gr.Markdown("---")
                gr.Markdown("### 📤 Cargar y Optimizar Documentos")

                with gr.Row():
                    with gr.Column():
                        upload_files = gr.Files(
                            label="Subir documentos para indexar",
                            file_types=constants.ALLOWED_TYPES
                        )

                        ocr_checkbox = gr.Checkbox(
                            label="🖼️ Activar OCR (imágenes/gráficos/tablas escaneadas)",
                            value=settings.DOCLING_DO_OCR,
                            interactive=True
                        )

                        custom_title = gr.Textbox(
                            label="Título personalizado (opcional)",
                            placeholder="Si dejas vacío, se usa el nombre del archivo..."
                        )

                    with gr.Column():
                        gr.Markdown("### 💡 Recomendaciones:")
                        gr.Markdown("""
- **Documentos solo texto**: desactiva OCR (3-5x más rápido)
- **Con gráficos/tablas**: actívalo (requiere modelos pre-descargados)
- **Archivos grandes** (>50 págs): indexar tarda varios minutos
- Usa el título personalizado para renombrar la colección

Primero descarga modelos (si usarás OCR):
```
python scripts/download_easyocr_models.py
```
                        """)

                index_btn = gr.Button("📥 Indexar documento(s)", variant="primary")
                upload_status_output = gr.Textbox(
                    label="Estado de indexación",
                    interactive=False,
                    lines=3
                )

            # Tab 4: Manage collections (delete/update)
            with gr.Tab("🗂️ Gestionar Colecciones", id="manage"):
                gr.Markdown("### Administra tus colecciones indexadas")
                gr.Markdown("Elimina colecciones para actualizarlas con documentos nuevos")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Colecciones disponibles:**")
                        manage_collections_list = gr.Dataframe(
                            label="Colecciones",
                            interactive=False,
                            wrap=True,
                            column_widths=["50%", "30%", "20%"]
                        )

                        refresh_manage_btn = gr.Button("🔄 Refrescar lista", variant="secondary")

                    with gr.Column():
                        gr.Markdown("**Eliminar colección:**")
                        manage_collection_dropdown = gr.Dropdown(
                            label="Selecciona colección a eliminar",
                            choices=retriever_builder.list_collections(),
                            interactive=True
                        )

                        delete_btn = gr.Button("🗑️ Eliminar Colección", variant="stop")

                        manage_status_output = gr.Textbox(
                            label="Estado",
                            interactive=False,
                            lines=3
                        )

                gr.Markdown("---")
                gr.Markdown("""
### 💡 Flujo de Actualización:

1. **Selecciona** la colección a actualizar en "Eliminar colección"
2. Click **"🗑️ Eliminar Colección"** → confirma eliminación
3. Ve a **"📚 Indexar RAG Documentos"** tab
4. Sube el documento **ACTUALIZADO**
5. Click **"📥 Indexar documento(s)"**
6. ¡Hecho! Tu colección está actualizada con contenido nuevo

**Nota:** Los índices eliminados no se pueden recuperar. Asegúrate que realmente quieres reemplazarlo.
                """)

        # --- Wiring de eventos (fuera de las tabs) ---

        # Load example documents
        def load_example(example_key: str):
            """Carga documentos de ejemplo y pregunta."""
            if not example_key or example_key not in EXAMPLES:
                return [], ""

            ex_data = EXAMPLES[example_key]
            question_text = ex_data["question"]
            file_paths = ex_data["file_paths"]

            loaded_files = []
            for path in file_paths:
                if os.path.exists(path):
                    loaded_files.append(path)
                else:
                    logger.warning(f"Example file not found: {path}")

            return loaded_files, question_text

        load_example_btn.click(
            fn=load_example,
            inputs=[example_dropdown],
            outputs=[files, question]
        )

        def refresh_collections_ui():
            """Refrescar lista de colecciones en el dropdown."""
            collections = retriever_builder.list_collections()
            logger.info(f"Colecciones actualizadas: {collections}")
            return gr.Dropdown(choices=collections)

        refresh_collections_btn.click(
            fn=refresh_collections_ui,
            outputs=[existing_collections]
        )

        # Main processing function for queries
        def process_question(question_text: str, uploaded_files: List,
                           selected_colls: List[str], state: Dict):
            """Procesa la pregunta a través del pipeline RAG agéntico."""
            try:
                # Validar entradas
                if not question_text.strip():
                    return "❌ Error: La pregunta no puede estar vacía", "", state

                has_files = bool(uploaded_files)
                has_collections = bool(selected_colls)

                if not has_files and not has_collections:
                    return "❌ Error: Sube documentos O selecciona colecciones existentes", "", state

                logger.info(f"Procesando pregunta: {question_text[:50]}... "
                           f"(archivos: {len(uploaded_files) if uploaded_files else 0}, "
                           f"colecciones: {len(selected_colls) if selected_colls else 0})")

                # Detectar cambios: hash de (archivos + colecciones seleccionadas)
                current_hashes = _get_file_hashes(uploaded_files) if uploaded_files else frozenset()
                selected_set = frozenset(selected_colls) if selected_colls else frozenset()
                current_state_key = (current_hashes, selected_set)

                needs_rebuild = (
                    state["retriever"] is None or
                    current_hashes != state["file_hashes"] or
                    selected_set != state["selected_collections"]
                )

                if needs_rebuild:
                    logger.info("Construyendo nuevo recuperador...")

                    # 1. Procesar documentos subidos (si los hay)
                    collections_to_index = {}
                    if has_files:
                        try:
                            doc_collections = processor.process(uploaded_files)
                            logger.info(f"Procesados {len(doc_collections)} documento(s)")
                            collections_to_index.update(doc_collections)
                        except Exception as e:
                            # Errores específicos: Ollama, Docling, EasyOCR
                            if "Failed to connect to Ollama" in str(e) or "No se puede conectar" in str(e):
                                return ("❌ Error: No se puede conectar a Ollama.\n"
                                       "Ejecuta en terminal: ollama serve"), "", state
                            elif "Missing models" in str(e) or "EasyOCR" in str(e) or "modelo" in str(e).lower():
                                return ("❌ Error: Modelos EasyOCR faltantes.\n"
                                       "Ejecuta: python scripts/download_easyocr_models.py\n"
                                       "O desactiva OCR en config.ini (do_ocr = false)"), "", state
                            else:
                                return f"❌ Error al procesar documentos: {str(e)[:100]}", "", state

                    # 2. Construir recuperador (combina nuevas + existentes)
                    try:
                        retriever = retriever_builder.build_retriever(
                            collections_to_index=collections_to_index,
                            selected_existing=selected_colls if selected_colls else None
                        )
                        logger.info("✓ Recuperador híbrido construido")

                        state.update({
                            "file_hashes": current_hashes,
                            "selected_collections": selected_set,
                            "retriever": retriever
                        })
                    except Exception as e:
                        if "Failed to connect to Ollama" in str(e):
                            return ("❌ Error: No se puede conectar a Ollama.\n"
                                   "Ejecuta: ollama serve"), "", state
                        else:
                            return f"❌ Error al construir recuperador: {str(e)[:100]}", "", state

                # Ejecutar el pipeline RAG agéntico
                logger.info("Iniciando pipeline RAG agéntico...")
                result = workflow.full_pipeline(
                    question=question_text,
                    retriever=state["retriever"]
                )
                logger.info("✓ Pipeline completado")

                return result["draft_answer"], result["verification_report"], state

            except Exception as e:
                logger.error(f"Error no manejado: {e}", exc_info=True)
                return f"❌ Error inesperado: {str(e)[:150]}", "", state

        submit_btn.click(
            fn=process_question,
            inputs=[question, files, existing_collections, session_state],
            outputs=[answer_output, verification_output, session_state]
        )

        # Explore indexed documents function
        def explore_document(collection_name: str) -> Tuple[str, str]:
            """Mostrar información del documento seleccionado."""
            if not collection_name:
                return "Selecciona un documento", ""

            try:
                collection = retriever_builder.chroma_client.get_collection(
                    name=collection_name
                )
                results = collection.get(include=["documents", "metadatas"])

                if not results["ids"]:
                    return f"Documento '{collection_name}': vacío", ""

                # Build info
                info = f"**📄 {collection_name}**\n\n"
                info += f"- **Total chunks:** {len(results['ids'])}\n"

                # Group chunks with numbering
                doc_info = f"**Chunks indexados:**\n\n"
                for i, doc_id in enumerate(results["ids"], 1):
                    doc = results["documents"][i-1] if results["documents"] else ""
                    meta = results["metadatas"][i-1] if results["metadatas"] else {}

                    doc_info += f"**[{i}] {doc_id[:16]}...**\n"
                    if meta:
                        doc_info += f"  Metadata: {meta}\n"
                    doc_info += f"  Contenido: {doc[:80]}...\n\n"

                return info, doc_info

            except Exception as e:
                return f"Error: {e}", ""

        explore_btn.click(
            fn=explore_document,
            inputs=[explore_dropdown],
            outputs=[doc_info_output, doc_content_output]
        )

        def refresh_explore():
            """Refrescar lista de documentos."""
            new_choices = retriever_builder.list_collections()
            logger.info(f"Documentos actualizados: {new_choices}")
            return gr.Dropdown(choices=new_choices)

        refresh_explore_btn.click(
            fn=refresh_explore,
            outputs=[explore_dropdown]
        )

        # Query indexed collections (sin subir docs nuevos) - Feature 2: "use all" checkbox support
        def process_collection_query(question_text: str, selected_colls: List[str], use_all: bool, state: Dict):
            """Procesa pregunta sobre colecciones ya indexadas.

            Si use_all=True, ignora selected_colls y usa todas las colecciones disponibles.
            """
            try:
                if not question_text.strip():
                    return "❌ Error: La pregunta no puede estar vacía", "", state

                # Feature 2: Use all collections if checkbox is enabled
                if use_all:
                    colls_to_use = retriever_builder.list_collections()
                    if not colls_to_use:
                        return "❌ Error: No hay colecciones indexadas. Primero indexa documentos en '📚 Indexar RAG Documentos'", "", state
                    logger.info(f"Usando TODAS las colecciones: {colls_to_use}")
                else:
                    if not selected_colls:
                        return "❌ Error: Selecciona al menos una colección o marca '✅ Usar TODAS las colecciones'", "", state
                    colls_to_use = selected_colls
                    logger.info(f"Consultando colecciones seleccionadas: {colls_to_use}")

                logger.info(f"Pregunta: {question_text[:50]}...")

                # Solo construir retriever sobre colecciones existentes (sin procesar docs nuevos)
                try:
                    retriever = retriever_builder.build_retriever(
                        collections_to_index={},  # Sin documentos nuevos
                        selected_existing=colls_to_use
                    )
                    logger.info("✓ Recuperador construido desde colecciones existentes")
                except Exception as e:
                    return f"❌ Error al construir recuperador: {str(e)[:100]}", "", state

                # Ejecutar pipeline RAG
                logger.info("Iniciando pipeline RAG...")
                result = workflow.full_pipeline(
                    question=question_text,
                    retriever=retriever
                )
                logger.info("✓ Pipeline completado")

                return result["draft_answer"], result["verification_report"], state

            except Exception as e:
                logger.error(f"Error en consulta de colecciones: {e}", exc_info=True)
                return f"❌ Error: {str(e)[:150]}", "", state

        def refresh_query_collections():
            """Refrescar lista de colecciones para consulta."""
            new_choices = retriever_builder.list_collections()
            logger.info(f"Colecciones disponibles: {new_choices}")
            return gr.Dropdown(choices=new_choices)

        refresh_query_collections_btn.click(
            fn=refresh_query_collections,
            outputs=[collection_selector]
        )

        # Feature 3: ChromaDB health check
        def check_chroma_health():
            """Verificar estado de salud de ChromaDB y mostrar en panel."""
            try:
                health = retriever_builder.get_health_status()

                # Format health status
                status_md = "### 🩺 ChromaDB Health Report\n\n"

                if health["heartbeat_ok"]:
                    status_md += f"**Heartbeat:** ✅ OK ({health['heartbeat_ms']:.1f}ms)\n\n"
                else:
                    status_md += f"**Heartbeat:** ❌ FAILED\n"
                    status_md += f"**Error:** {health['error']}\n\n"
                    return status_md

                # Connection details
                status_md += f"**Host:Port:** `{health['host']}:{health['port']}`\n\n"

                # Collections summary
                status_md += f"**Total Collections:** {health['total_collections']}\n"
                status_md += f"**Total Chunks:** {health['total_chunks']}\n\n"

                # Per-collection detail
                if health["collections_detail"]:
                    status_md += "**Collections Detail:**\n\n"
                    status_md += "| Collection | Chunks |\n"
                    status_md += "|---|---|\n"
                    for col_detail in health["collections_detail"]:
                        status_md += f"| `{col_detail['name']}` | {col_detail['count']} |\n"

                logger.info(f"✓ ChromaDB health: {health['total_collections']} collections, {health['total_chunks']} chunks")
                return status_md

            except Exception as e:
                logger.error(f"Error checking ChromaDB health: {e}", exc_info=True)
                return f"❌ Error verificando estado de ChromaDB: {str(e)[:150]}"

        check_health_btn.click(
            fn=check_chroma_health,
            outputs=[chroma_health_output]
        )

        query_collections_btn.click(
            fn=process_collection_query,
            inputs=[collection_question, collection_selector, use_all_collections_checkbox, session_state],
            outputs=[collection_answer_output, collection_verification_output, session_state]
        )

        # Feature 1: Index from Explore tab
        def index_from_explore(files_to_upload: List, do_ocr: bool, custom_title: str, state: Dict):
            """Indexar documentos desde la pestaña Explorar con opciones personalizadas.

            - do_ocr: override local de OCR por este indexado
            - custom_title: renombrar la colección en lugar del nombre del archivo
            """
            try:
                if not files_to_upload:
                    return "❌ Error: No hay documentos para indexar", state

                logger.info(f"Indexando {len(files_to_upload)} documento(s)")
                logger.info(f"  OCR habilitado: {do_ocr}, Título personalizado: '{custom_title}'")

                # Procesar documentos con override de OCR
                processor_with_override = DocumentProcessor(do_ocr_override=do_ocr)
                collections_dict = processor_with_override.process(files_to_upload)

                if not collections_dict:
                    return "❌ Error: No se pudieron procesar los documentos. Verifica que sean PDFs válidos.", state

                # Si hay título personalizado, renombrar la(s) colección(es)
                if custom_title and custom_title.strip():
                    # Renombrar primera colección (si hay varias, se indexan con su nombre original)
                    new_collections = {}
                    for i, (col_name, chunks) in enumerate(collections_dict.items()):
                        if i == 0:
                            # Slugify custom title like upload_and_index.py does
                            slug = re.sub(r'[^a-z0-9\s\-]', '', custom_title.lower())
                            slug = re.sub(r'[\s]+', '_', slug.strip())
                            slug = re.sub(r'[\-]+', '_', slug)
                            slug = slug.rstrip('_')

                            if len(slug) < 3:
                                slug = f"doc_{slug}"
                            if len(slug) > 63:
                                slug = slug[:60]

                            logger.info(f"  Renombrando colección: '{col_name}' → '{slug}'")
                            new_collections[slug] = chunks
                        else:
                            new_collections[col_name] = chunks
                    collections_dict = new_collections

                # Indexar
                retriever_builder.build_retriever(
                    collections_to_index=collections_dict,
                    selected_existing=None
                )

                logger.info(f"✓ Indexados {len(collections_dict)} colección(es)")

                # Refrescar dropdowns en todas las pestañas
                new_collections_list = retriever_builder.list_collections()

                status_msg = f"✅ Éxito: Indexadas {len(collections_dict)} colección(es)\n"
                status_msg += f"Collections: {', '.join(list(collections_dict.keys())[:3])}"
                if len(collections_dict) > 3:
                    status_msg += f" ... (+{len(collections_dict) - 3} más)"

                return status_msg, state, \
                    gr.Dropdown(choices=new_collections_list), \
                    gr.Dropdown(choices=new_collections_list), \
                    gr.Dropdown(choices=new_collections_list)

            except Exception as e:
                if "Missing models" in str(e) or "EasyOCR" in str(e) or "modelo" in str(e).lower():
                    msg = ("❌ Error: Modelos EasyOCR no disponibles.\n"
                           "Ejecuta en terminal: python scripts/download_easyocr_models.py\n"
                           "O desactiva OCR en config.ini")
                elif "Failed to connect to Ollama" in str(e) or "Ollama" in str(e):
                    msg = ("❌ Error: No se puede conectar a Ollama.\n"
                           "Ejecuta en terminal: ollama serve")
                else:
                    msg = f"❌ Error al indexar: {str(e)[:100]}"

                logger.error(f"Error en index_from_explore: {e}", exc_info=True)
                return msg, state, \
                    gr.Dropdown(choices=retriever_builder.list_collections()), \
                    gr.Dropdown(choices=retriever_builder.list_collections()), \
                    gr.Dropdown(choices=retriever_builder.list_collections())

        # Wire the index button to refresh all collection dropdowns
        index_btn.click(
            fn=index_from_explore,
            inputs=[upload_files, ocr_checkbox, custom_title, session_state],
            outputs=[upload_status_output, session_state,
                    explore_dropdown, existing_collections, collection_selector]
        )

        # Feature 4: Manage Collections (Delete/Update)
        def refresh_collections_list():
            """Refrescar lista de colecciones con detalles."""
            try:
                collections = retriever_builder.list_collections()

                if not collections:
                    return gr.Dataframe(value=None)

                # Build dataframe with collection details
                data = []
                for col_name in sorted(collections):
                    details = retriever_builder.get_collection_details(col_name)
                    if details:
                        data.append({
                            "Colección": col_name,
                            "Chunks": details["chunks"],
                            "Tamaño": f"{details['chunks']} docs"
                        })

                logger.info(f"✓ Lista de colecciones refrescada: {len(data)} colecciones")

                return gr.Dataframe(
                    value=data,
                    interactive=False
                )
            except Exception as e:
                logger.error(f"Error refrescando lista: {e}", exc_info=True)
                return gr.Dataframe(value=None)

        def delete_collection(collection_to_delete: str):
            """Eliminar una colección y refrescar lists."""
            if not collection_to_delete:
                return "❌ Error: Selecciona una colección para eliminar", \
                       gr.Dropdown(choices=retriever_builder.list_collections()), \
                       refresh_collections_list()

            try:
                logger.info(f"🗑️ Eliminando colección: '{collection_to_delete}'")

                # Delete from ChromaDB
                success = retriever_builder.delete_collection(collection_to_delete)

                if success:
                    logger.info(f"✓ Colección '{collection_to_delete}' eliminada")

                    # Get updated list
                    updated_collections = retriever_builder.list_collections()

                    # Refresh all dropdowns
                    manage_dropdown_update = gr.Dropdown(choices=updated_collections)
                    explore_dropdown_update = gr.Dropdown(choices=updated_collections)
                    existing_collections_update = gr.Dropdown(choices=updated_collections)
                    collection_selector_update = gr.Dropdown(choices=updated_collections)

                    status_msg = f"✅ Éxito: Colección '{collection_to_delete}' eliminada\n\nPuede volver a indexarla en '📚 Indexar RAG Documentos'"

                    return status_msg, manage_dropdown_update, refresh_collections_list()
                else:
                    return "❌ Error al eliminar la colección", \
                           gr.Dropdown(choices=retriever_builder.list_collections()), \
                           refresh_collections_list()

            except Exception as e:
                logger.error(f"Error eliminando colección: {e}", exc_info=True)
                return f"❌ Error: {str(e)[:100]}", \
                       gr.Dropdown(choices=retriever_builder.list_collections()), \
                       refresh_collections_list()

        # Wire manage tab buttons
        refresh_manage_btn.click(
            fn=refresh_collections_list,
            outputs=[manage_collections_list]
        )

        delete_btn.click(
            fn=delete_collection,
            inputs=[manage_collection_dropdown],
            outputs=[manage_status_output, manage_collection_dropdown, manage_collections_list]
        )

        # Load initial collection list on startup
        with gr.Row():
            pass  # Dummy to trigger initial load

        # Initial load of collections
        demo.load(
            fn=refresh_collections_list,
            outputs=[manage_collections_list]
        )

    # Launch
    logger.info(f"Launching Gradio server on {settings.GRADIO_SERVER_NAME}:{settings.GRADIO_SERVER_PORT}")
    demo.launch(
        server_name=settings.GRADIO_SERVER_NAME,
        server_port=settings.GRADIO_SERVER_PORT,
        share=settings.GRADIO_SHARE
    )


def _get_file_hashes(uploaded_files: List) -> frozenset:
    """Generate SHA-256 hashes for file change detection."""
    hashes = set()
    for file in uploaded_files:
        with open(file.name, "rb") as f:
            hashes.add(hashlib.sha256(f.read()).hexdigest())
    return frozenset(hashes)


if __name__ == "__main__":
    main()
