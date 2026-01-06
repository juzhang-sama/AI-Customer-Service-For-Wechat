
# -*- coding: utf-8 -*-
import sys
import os
import time
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_expert.knowledge_base_manager import KnowledgeBaseManager
from ai_expert.database import AIExpertDatabase

def flush_print(msg):
    print(msg)
    sys.stdout.flush()

def test_rag_flow():
    flush_print("="*50)
    flush_print("Starting RAG Flow Verification")
    flush_print("="*50)

    # 1. Setup Test DBs
    db_path = "test_rag.db"
    vector_db_path = "test_chroma_db"
    
    # Cleanup previous runs
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(vector_db_path):
        shutil.rmtree(vector_db_path)

    flush_print("[1] Initializing Managers...")
    # SQL DB
    db = AIExpertDatabase(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    # Create tables manually if needed, or rely on manager/db init
    # KnowledgeBaseManager relies on database.py tables. 
    # db.init_database() should creating tables.
    db.init_database()
    conn.close()

    # RAG Manager
    kb_manager = KnowledgeBaseManager(db_path=db_path, vector_db_path=vector_db_path)
    
    if not kb_manager.vector_store:
        flush_print("[ERROR] Vector Store not initialized.")
        return

    # 2. Create Test Document
    test_doc_path = "test_doc.txt"
    with open(test_doc_path, "w", encoding="utf-8") as f:
        f.write("此文件包含机密信息。\n")
        f.write("联道科技的 WiFi 密码是 88888888。\n")
        f.write("公司的核心价值观是：客户第一，诚信至上。\n")
        f.write("关于售后服务：所有的维修请求将在 24 小时内响应。\n")
        f.write("无关内容：今天天气不错，适合出去玩。\n" * 20) # Add noise

    flush_print(f"\n[2] Created test document: {test_doc_path}")

    # 3. Ingestion
    flush_print("\n[3] Ingesting Document...")
    # Bound to prompt_id 1 (Specialist A)
    success = kb_manager.add_document(test_doc_path, bound_prompt_id=1, description="Test Manual")
    
    if success:
        flush_print("✅ Document ingested successfully.")
    else:
        flush_print("❌ Document ingestion FAILED.")
        return

    # 4. Retrieval Tests
    flush_print("\n[4] Testing Retrieval...")

    # Case A: Relevant Query (Prompt 1)
    query_a = "WiFi密码是多少？"
    flush_print(f"Query A: '{query_a}' (Bound Prompt ID: 1)")
    # Use 0.1 threshold to catch anything and inspect scores
    results_a = kb_manager.search(query_a, bound_prompt_id=1, top_k=2, threshold=0.1)
    for res in results_a:
        flush_print(f" - Found ({res['score']:.2f}): {res['content'].strip()[:50]}...")
    
    if any("88888888" in r['content'] for r in results_a):
         flush_print("✅ Pass: Found WiFi password.")
    else:
         flush_print("❌ Fail: WiFi password NOT found.")

    # Case B: Relevant Query but Wrong Prompt ID (Prompt 2)
    # Since doc is bound to 1, Prompt 2 should NOT see it (unless logic allows, let's verify logic)
    # Logic says: bound_prompt_id == current OR bound_prompt_id == 0
    # Doc is 1. Current is 2. 1 != 2 and 1 != 0. So should be empty.
    
    flush_print(f"\nQuery B: '{query_a}' (Bound Prompt ID: 2 - Should NOT find it)")
    results_b = kb_manager.search(query_a, bound_prompt_id=2, top_k=2)
    if not results_b:
        flush_print("✅ Pass: Correctly filtered out private document.")
    else:
        flush_print(f"❌ Fail: Found document despite wrong prompt ID: {results_b}")

    # Case C: Global Document
    flush_print("\n[5] Testing Global Document...")
    global_doc_path = "global_doc.txt"
    with open(global_doc_path, "w", encoding="utf-8") as f:
        f.write("公司总部地址：上海市浦东新区陆家嘴。\n")
    
    kb_manager.add_document(global_doc_path, bound_prompt_id=0, description="Global Info") # 0 = Global
    
    # Prompt 2 should see global doc
    query_c = "总部在哪？"
    flush_print(f"Query C: '{query_c}' (Bound Prompt ID: 2 - Should see global)")
    results_c = kb_manager.search(query_c, bound_prompt_id=2)
    
    if any("陆家嘴" in r['content'] for r in results_c):
         flush_print("✅ Pass: Found global info.")
    else:
         flush_print("❌ Fail: Global info NOT found.")

    # Cleanup
    try:
        os.remove(test_doc_path)
        os.remove(global_doc_path)
        # shutil.rmtree(vector_db_path) # Optionally keep for inspection
        # file cleanup
    except:
        pass
        
    flush_print("\nRAG Verification Complete.")

if __name__ == "__main__":
    test_rag_flow()
