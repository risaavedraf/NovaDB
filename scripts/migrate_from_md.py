import os
import glob
import re
from novadb.novadb import NovaDB

def chunk_markdown(content: str) -> list:
    """Respeta los bloques de código y agrupa los párrafos como Memos aislados."""
    chunks = []
    in_code_block = False
    current_chunk = []
    
    for line in content.split('\n'):
        if line.startswith('```'):
            in_code_block = not in_code_block
            current_chunk.append(line)
            if not in_code_block:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
        else:
            if in_code_block:
                current_chunk.append(line)
            elif line.strip() == "":
                if current_chunk:
                    chunks.append('\n'.join(current_chunk).strip())
                    current_chunk = []
            else:
                current_chunk.append(line)
                
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
    
    return [c for c in chunks if len(c) > 20]

def extract_links(text: str) -> list:
    """Extrae enlaces [[wikilinks]] y [markdown](links) para trapear conexiones manuales."""
    wiki = re.findall(r'\[\[(.*?)\]\]', text)
    md = re.findall(r'\[(.*?)\]\((.*?)\)', text)
    return wiki + [url for _, url in md]

def migrate_markdown_directory(source_dir: str, db_path: str = "./db/nova_production.msgpack"):
    """
    Script oficial de migración.
    Lee los archivos Markdown del cerebro actual de Nova (`~/.gemini/antigravity/memoria/`)
    y los inyecta en NovaDB como un Knowledge Graph real.
    """
    # Usaremos el Embedder real de Gemini, asegúrese de tener GEMINI_API_KEY
    db = NovaDB(path=db_path)
    
    print(f"🚀 Iniciando migración desde: {source_dir}")
    archivos_md = glob.glob(os.path.join(source_dir, "**", "*.md"), recursive=True)
    
    for file_path in archivos_md:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            basename = os.path.basename(file_path)
            doc_name = basename.replace(".md", "")
            
            print(f"-> Procesando: {doc_name}")
            
            # 1. El documento en sí se convierte en un nodo MACRO
            macro_id = db.insert(
                text=f"Documento fuente: {doc_name}",
                tipo="MACRO",
                metadata={"file_path": file_path}
            )
            
            # 2. Dividir el documento con el Chunking inteligente (preservando código)
            parrafos = chunk_markdown(content)
            
            for p in parrafos:
                extracted_links = extract_links(p)
                db.insert(
                    text=p,
                    tipo="MEMORIA",
                    metadata={
                        "source_doc": doc_name,
                        "extracted_links": extracted_links
                    }
                )
                
        except Exception as e:
            print(f"⚠️ Error leyendo {file_path}: {e}")
            
    print("✅ Migración completa.")
    print("Estadísticas del nuevo Cerebro de Nova:")
    print(db.stats())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate Markdown to NovaDB")
    parser.add_argument("--source", type=str, required=True, help="Ruta a ~/.gemini/antigravity/memoria")
    args = parser.parse_args()
    
    migrate_markdown_directory(args.source)
