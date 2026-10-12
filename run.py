import os
import sys
import uvicorn
from backend.demo_generator import generate_sample_batch_files

def main():
    print("=" * 60)
    print("  🚀 Starting ReimburseAI - Expense & Reimbursement Agent")
    print("=" * 60)
    
    # 1. Ensure sample receipts exist
    sample_dir = os.path.join(os.path.dirname(__file__), "backend", "sample_receipts")
    if not os.path.exists(sample_dir) or len(os.listdir(sample_dir)) < 11:
        print("[*] Generating 11 realistic sample receipts (photos & PDFs)...")
        generate_sample_batch_files(sample_dir)
        print("[+] Sample batch generated successfully!")

    print("\n🌐 Web UI available at: http://localhost:8000")
    print("📑 Interactive API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
