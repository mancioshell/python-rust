from pathlib import Path
import uvicorn

if __name__ == "__main__":    

    reload_dir = str(Path(__file__).parent)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        reload_dirs=reload_dir,
        port=9090,
        log_level="debug",
        workers=4
    )