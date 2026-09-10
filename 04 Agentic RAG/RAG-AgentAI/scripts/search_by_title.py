#!/usr/bin/env python3
"""Search indexed documents by title — lee y busca en los índices."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from retriever.builder import RetrieverBuilder
from langchain_ollama import OllamaEmbeddings
from config.settings import settings
from utils.logging import logger
import json


def list_indexed_documents():
    """List all indexed documents (colecciones en ChromaDB)."""
    logger.info("📚 Indexed documents:")
    print("=" * 80)

    retriever_builder = RetrieverBuilder()
    collections = retriever_builder.list_collections()

    if not collections:
        print("(none)")
        return

    for i, coll_name in enumerate(sorted(collections), 1):
        try:
            collection = retriever_builder.chroma_client.get_collection(name=coll_name)
            count = collection.count()
            print(f"  [{i}] {coll_name}")
            print(f"       Chunks: {count}")
        except Exception as e:
            print(f"  [{i}] {coll_name} (error: {e})")

    print("=" * 80)
    print(f"Total: {len(collections)} indexed document(s)\n")


def search_in_document(collection_name: str, query: str, k: int = 5):
    """Search for similar content in a specific indexed document."""
    logger.info(f"🔍 Searching in '{collection_name}' for: '{query}'")

    retriever_builder = RetrieverBuilder()
    embeddings = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )

    try:
        # Get collection
        collection = retriever_builder.chroma_client.get_collection(name=collection_name)

        # Generate embedding for query
        logger.info("   Generating embedding...")
        query_embedding = embeddings.embed_query(query)

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        if not results["ids"] or len(results["ids"][0]) == 0:
            print("\n(no results)")
            return

        print(f"\n📋 Top {len(results['ids'][0])} results:\n")

        for i, doc_id in enumerate(results["ids"][0], 1):
            doc = results["documents"][0][i-1]
            meta = results["metadatas"][0][i-1]
            distance = results["distances"][0][i-1]
            similarity = 1 - distance

            print(f"[{i}] Similarity: {similarity:.3f}")
            print(f"    {doc[:100]}..." if len(doc) > 100 else f"    {doc}")
            if meta:
                print(f"    Metadata: {json.dumps(meta, ensure_ascii=False)}")
            print()

    except Exception as e:
        logger.error(f"❌ Search failed: {e}", exc_info=True)


def show_document_content(collection_name: str):
    """Show all content from an indexed document."""
    logger.info(f"📖 Content from '{collection_name}':")

    retriever_builder = RetrieverBuilder()

    try:
        collection = retriever_builder.chroma_client.get_collection(name=collection_name)
        results = collection.get(include=["documents", "metadatas"])

        if not results["ids"]:
            print("(empty)")
            return

        print(f"\n{'='*80}\n")

        for i, doc_id in enumerate(results["ids"], 1):
            doc = results["documents"][i-1] if results["documents"] else ""
            meta = results["metadatas"][i-1] if results["metadatas"] else {}

            print(f"[Chunk {i}]")
            print(f"  {doc}\n")

        print(f"{'='*80}")
        print(f"Total chunks: {len(results['ids'])}\n")

    except Exception as e:
        logger.error(f"❌ Failed to retrieve content: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search indexed documents by title"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # list
    subparsers.add_parser("list", help="List all indexed documents")

    # search
    search_parser = subparsers.add_parser("search", help="Search in a document")
    search_parser.add_argument("collection", help="Collection/document name")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", type=int, default=5, help="Number of results (default: 5)")

    # show
    show_parser = subparsers.add_parser("show", help="Show all content from a document")
    show_parser.add_argument("collection", help="Collection/document name")

    args = parser.parse_args()

    if args.command == "list":
        list_indexed_documents()
    elif args.command == "search":
        search_in_document(args.collection, args.query, args.k)
    elif args.command == "show":
        show_document_content(args.collection)
    else:
        parser.print_help()
