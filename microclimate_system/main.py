import subprocess
import sys
import os

def get_python_exec():
    base = os.path.dirname(os.path.abspath(__file__))
    for v in ["venv", ".venv"]:
        p = os.path.join(base, v, "Scripts", "python.exe")
        if os.path.exists(p):
            return p
    return sys.executable

def main():
    py_exec = get_python_exec()
    print("=== Step 1: Data Ingestion ===")
    subprocess.run([py_exec, "data_ingestion.py"], check=True)
    
    print("\n=== Step 2: Preprocessing ===")
    subprocess.run([py_exec, "preprocessing.py"], check=True)
    
    print("\n=== Step 3: Model Training ===")
    subprocess.run([py_exec, "train_model.py"], check=True)
    
    print("\n=== Step 4: Real-Time Inference ===")
    subprocess.run([py_exec, "inference.py"], check=True)
    
    print("\n=== Step 5: Alert Layer ===")
    subprocess.run([py_exec, "alert_layer.py"], check=True)

    print("\n=== Step 6: Ward-Level Geospatial Generation ===")
    subprocess.run([py_exec, os.path.join("scripts", "generate_ward_data.py")], check=True)

if __name__ == "__main__":
    main()
