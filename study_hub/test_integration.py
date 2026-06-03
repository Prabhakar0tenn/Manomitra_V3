import subprocess
import time
import urllib.request
import json
import os
import fitz

def create_test_pdf():
    print("Creating test PDF...")
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, (
        "Operating Systems Lecture Notes.\n"
        "Topic: Deadlocks\n\n"
        "A deadlock occurs when a set of processes are blocked because each process is holding a resource and waiting for another resource held by some other process.\n\n"
        "The four Coffman conditions that must hold simultaneously for a deadlock to occur are:\n"
        "1. Mutual Exclusion: At least one resource must be held in a non-shareable mode. Only one process can use the resource at any given time.\n"
        "2. Hold and Wait: A process must be holding at least one resource and waiting to acquire additional resources that are currently being held by other processes.\n"
        "3. No Preemption: Resources cannot be preempted; a resource can be released only voluntarily by the process holding it, after that process has completed its task.\n"
        "4. Circular Wait: A process must be waiting for a resource which is being held by another process, which in turn is waiting for the first process to release its resource.\n\n"
        "Deadlock prevention can be done by design, specifically by eliminating any one of the four Coffman conditions. For example, circular wait can be prevented by ordering all resources and requiring processes to request resources in increasing order."
    ))
    doc.save("test_deadlock.pdf")
    doc.close()
    print("Test PDF 'test_deadlock.pdf' created successfully.\n")

def run_integration_tests():
    print("Starting FastAPI server...")
    # Start server
    server_process = subprocess.Popen(
        [".venv\\Scripts\\python", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to initialize
    time.sleep(5)
    
    try:
        # Check health
        print("Checking health endpoint...")
        req = urllib.request.urlopen("http://127.0.0.1:8000/health")
        health = json.loads(req.read().decode('utf-8'))
        print("Health status:", health)
        
        # We use httpx to handle multipart upload easily
        import httpx
        
        print("\n--- Testing Document Upload ---")
        with open("test_deadlock.pdf", "rb") as f:
            files = {"file": ("test_deadlock.pdf", f, "application/pdf")}
            response = httpx.post("http://127.0.0.1:8000/documents/upload", files=files)
        
        upload_result = response.json()
        print("Upload Result:")
        print(json.dumps(upload_result, indent=2))
        
        if not upload_result.get("success"):
            print("Upload failed! Aborting tests.")
            return
            
        doc_id = upload_result["document_id"]
        
        # Test Chat Q&A (Present info)
        print("\n--- Testing Chat QA (Topic: Circular Wait) ---")
        chat_payload = {"question": "What is the Circular Wait condition?", "document_id": doc_id}
        chat_response = httpx.post("http://127.0.0.1:8000/chat", json=chat_payload, timeout=30.0)
        print("Chat Response:")
        print(json.dumps(chat_response.json(), indent=2))
        
        # Test Chat Q&A (Not present info)
        print("\n--- Testing Chat QA (Topic: Linux kernel history - should say not found) ---")
        chat_payload_fail = {"question": "Explain the history of the Linux kernel.", "document_id": doc_id}
        chat_response_fail = httpx.post("http://127.0.0.1:8000/chat", json=chat_payload_fail, timeout=30.0)
        print("Chat Response:")
        print(json.dumps(chat_response_fail.json(), indent=2))
        
        # Test Notes Generation
        print("\n--- Testing Notes Generation ---")
        notes_payload = {"document_id": doc_id, "detail_level": "brief"}
        notes_response = httpx.post("http://127.0.0.1:8000/notes/generate", json=notes_payload, timeout=30.0)
        print("Notes Response:")
        print(json.dumps(notes_response.json(), indent=2))
        
        # Test Quiz Generation
        print("\n--- Testing Quiz Generation ---")
        quiz_payload = {"document_id": doc_id, "num_questions": 2, "difficulty": "medium"}
        quiz_response = httpx.post("http://127.0.0.1:8000/quiz/generate", json=quiz_payload, timeout=30.0)
        print("Quiz Response:")
        print(json.dumps(quiz_response.json(), indent=2))
        
        # Test GET /documents
        print("\n--- Testing Documents List ---")
        list_response = httpx.get("http://127.0.0.1:8000/documents")
        print("Documents List:")
        print(json.dumps(list_response.json(), indent=2))
        
        # Test Delete
        print("\n--- Testing Delete Document ---")
        delete_response = httpx.delete(f"http://127.0.0.1:8000/documents/{doc_id}")
        print("Delete Response:", delete_response.json())
        
    except Exception as e:
        print("An error occurred during verification:", e)
    finally:
        print("\nStopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        
        # Cleanup test files
        if os.path.exists("test_deadlock.pdf"):
            os.remove("test_deadlock.pdf")
            print("Removed local test_deadlock.pdf.")

if __name__ == "__main__":
    create_test_pdf()
    run_integration_tests()
