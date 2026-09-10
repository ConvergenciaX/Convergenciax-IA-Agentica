#!/usr/bin/env python3
"""Inspect ChromaDB — Lee y muestra todo el contenido almacenado."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
import json
from config.settings import settings

def inspect_chroma():
    """Conecta a Chroma y muestra contenido de la colección."""

    try:
        # Conectar a Chroma
        print(f"📡 Conectando a ChromaDB en {settings.CHROMA_HOST}:{settings.CHROMA_PORT}...")
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)

        # Listar colecciones
        collections = client.list_collections()
        print(f"\n📚 Colecciones disponibles ({len(collections)}):")
        for col in collections:
            print(f"  • {col.name}")

        if not collections:
            print("  (ninguna)")
            return

        # Conectar a nuestra colección
        collection_name = settings.CHROMA_COLLECTION_NAME
        print(f"\n🔍 Leyendo colección: '{collection_name}'")
        collection = client.get_collection(name=collection_name)

        # Contar documentos
        count = collection.count()
        print(f"   Total de documentos: {count}")

        if count == 0:
            print("   (vacía)")
            return

        # Obtener todos los documentos
        print(f"\n📄 Contenido:")
        print("=" * 120)

        results = collection.get(include=["documents", "metadatas", "distances"])

        for i, doc_id in enumerate(results["ids"], 1):
            doc = results["documents"][i-1] if results["documents"] else ""
            meta = results["metadatas"][i-1] if results["metadatas"] else {}
            distance = results["distances"][i-1] if results["distances"] else "N/A"

            print(f"\n[{i}] ID: {doc_id}")
            print(f"    Distancia: {distance}")
            print(f"    Archivo: {meta.get('file', 'N/A')}")
            print(f"    Sección: {meta.get('section', 'N/A')}")
            print(f"    Chunk: {doc[:150]}..." if len(doc) > 150 else f"    Chunk: {doc}")
            print(f"    Metadatos: {json.dumps(meta, indent=6, ensure_ascii=False)}")

        print("\n" + "=" * 120)
        print(f"\n✅ Total: {count} fragmentos almacenados en ChromaDB")

        # Estadísticas
        print(f"\n📊 Estadísticas:")
        files = set()
        for meta in results["metadatas"]:
            if "file" in meta:
                files.add(meta["file"])

        print(f"   Archivos únicos: {len(files)}")
        for fname in sorted(files):
            chunks_in_file = sum(1 for m in results["metadatas"] if m.get("file") == fname)
            print(f"     • {fname}: {chunks_in_file} fragmentos")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_chroma()
