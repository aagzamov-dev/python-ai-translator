"""
Run the JSON Translation API server.

Usage:
    python run.py
    
The server will start on http://localhost:8000
API documentation available at http://localhost:8000/docs
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
