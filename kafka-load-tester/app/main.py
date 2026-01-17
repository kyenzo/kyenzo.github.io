"""FastAPI application for Kafka load testing."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from models import LoadTestConfig, LoadTestStatus, HealthCheck
from producer import producer_pool
import metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Kafka Load Tester")
    try:
        await producer_pool.connect()
        logger.info("Successfully connected to Kafka")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        logger.warning("Application starting without Kafka connection")

    yield

    # Shutdown
    logger.info("Shutting down Kafka Load Tester")
    await producer_pool.disconnect()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return html_file.read_text()
    return "<h1>Kafka Load Tester</h1><p>Static files not found</p>"


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        kafka_connected=producer_pool.is_connected,
        app_name=settings.app_name,
        version=settings.app_version
    )


@app.get("/api/status", response_model=LoadTestStatus)
async def get_status():
    """Get current load test status."""
    return producer_pool.get_status()


@app.post("/api/start")
async def start_load_test(config: LoadTestConfig, background_tasks: BackgroundTasks):
    """Start a new load test."""
    if not producer_pool.is_connected:
        raise HTTPException(status_code=503, detail="Not connected to Kafka")

    status = producer_pool.get_status()
    if status.running:
        raise HTTPException(status_code=409, detail="A load test is already running")

    # Start load test in background
    background_tasks.add_task(producer_pool.run_load_test, config)

    return {"status": "started", "message": "Load test started"}


@app.post("/api/stop")
async def stop_load_test():
    """Stop the current load test."""
    status = producer_pool.get_status()
    if not status.running:
        raise HTTPException(status_code=400, detail="No load test is running")

    await producer_pool.stop_test()
    return {"status": "stopping", "message": "Load test stop requested"}


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates."""
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            # Send current status
            status = producer_pool.get_status()
            await websocket.send_json(status.dict())

            # Wait before sending next update
            await asyncio.sleep(0.5)  # Update twice per second

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=metrics.get_metrics(),
        media_type=metrics.get_content_type()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )



