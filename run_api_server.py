#!/usr/bin/env python3
"""
Script to run STECCOM API server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to run API server"""
    # Get project root
    project_root = Path(__file__).parent
    
    # Change to project directory
    os.chdir(project_root)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the API server
    try:
        print("🚀 Starting STECCOM API Server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API documentation: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/health")
        print("\n" + "="*50)
        
        # Run uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.run_api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 API Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
