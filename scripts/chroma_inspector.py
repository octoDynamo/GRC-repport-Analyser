"""
ChromaDB Inspector — lists all analyse_* collections with chunk counts and metadata.
Usage:  python scripts/chroma_inspector.py
"""
import sys
import chromadb
from chromadb.config import Settings

CHROMA_HOST = "localhost"
CHROMA_PORT = 8001

def main():
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False),
        )
        version = client.get_version()
    except Exception as e:
        print(f"[ERREUR] Impossible de se connecter à ChromaDB : {e}")
        print(f"         Assurez-vous que ChromaDB tourne sur http://{CHROMA_HOST}:{CHROMA_PORT}")
        sys.exit(1)

    print(f"\n{'='*65}")
    print(f"  ChromaDB {version}  —  http://{CHROMA_HOST}:{CHROMA_PORT}")
    print(f"{'='*65}\n")

    collections = client.list_collections()
    if not collections:
        print("  Aucune collection trouvée.")
        print("  -> Lancez une analyse pour indexer un document.\n")
        return

    print(f"  {'Collection':<45} {'Chunks':>6}")
    print(f"  {'-'*45} {'-'*6}")

    total_chunks = 0
    for col in sorted(collections, key=lambda c: c.name):
        count = col.count()
        total_chunks += count
        print(f"  {col.name:<45} {count:>6}")

    print(f"  {'─'*45} {'─'*6}")
    print(f"  {'TOTAL  (' + str(len(collections)) + ' collections)':<45} {total_chunks:>6}\n")

    # Show sample metadata from first collection
    if collections:
        first = collections[0]
        print(f"  Exemple de métadonnées ({first.name}) :")
        sample = first.get(limit=3, include=["metadatas"])
        for i, meta in enumerate(sample["metadatas"]):
            print(f"    chunk {i}: {meta}")
        print()

if __name__ == "__main__":
    main()
