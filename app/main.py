"""
Main FastAPI Application
Zero-cost nonprofit intelligence platform
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from pathlib import Path
import logging
import json
from datetime import datetime

# Import our modules
from app.config import config
from app.database import db
from app.irs_processor import irs_processor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nonprofit Intelligence Platform",
    description="Free, open-source platform for nonprofit data analysis",
    version="1.0.0"
)

# Configure CORS for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
config.ensure_directories()

# Mount static files
if config.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Serve the main application"""
    index_path = config.STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Nonprofit Platform</title></head>
            <body>
                <h1>Nonprofit Intelligence Platform</h1>
                <p>Platform is running! Please ensure index.html is in the static folder.</p>
                <p>API Documentation: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": config.ENV,
        "database": "connected" if db else "disconnected"
    }

@app.get("/api/search")
async def search_organizations(
    q: Optional[str] = Query(None, description="Search query"),
    state: Optional[str] = Query(None, description="State code (e.g., CA, NY)"),
    city: Optional[str] = Query(None, description="City name"),
    ntee: Optional[str] = Query(None, description="NTEE code prefix"),
    min_revenue: Optional[int] = Query(None, description="Minimum revenue"),
    max_revenue: Optional[int] = Query(None, description="Maximum revenue"),
    min_assets: Optional[int] = Query(None, description="Minimum assets"),
    max_assets: Optional[int] = Query(None, description="Maximum assets"),
    limit: int = Query(50, ge=1, le=500, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Search nonprofit organizations with various filters
    
    - **q**: Full-text search across name, EIN, city
    - **state**: Filter by state (2-letter code)
    - **ntee**: Filter by NTEE code (can be partial)
    - **min_revenue/max_revenue**: Revenue range filter
    - **min_assets/max_assets**: Asset range filter
    """
    try:
        results, total = db.search_organizations(
            query=q,
            state=state,
            city=city,
            ntee_code=ntee,
            min_revenue=min_revenue,
            max_revenue=max_revenue,
            min_assets=min_assets,
            max_assets=max_assets,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/organization/{ein}")
async def get_organization(ein: str):
    """Get detailed information about a specific organization"""
    
    org = db.get_organization(ein)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "success": True,
        "organization": org
    }

@app.get("/api/statistics")
async def get_statistics():
    """Get platform statistics and data overview"""
    
    stats = db.get_statistics()
    
    # Add NTEE category names
    if 'ntee_distribution' in stats:
        for item in stats['ntee_distribution']:
            item['category_name'] = irs_processor.NTEE_CATEGORIES.get(
                item['category'], 'Unknown'
            )
    
    return {
        "success": True,
        "statistics": stats,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/import/start")
async def start_data_import(background_tasks: BackgroundTasks):
    """
    Start the IRS data import process
    This runs in the background and may take 10-30 minutes
    """
    
    def import_task():
        """Background task to import data"""
        try:
            logger.info("Starting data import task")
            
            # Download and process IRS data
            stats, organizations = irs_processor.process_all_data()
            
            # Insert into database
            if organizations:
                inserted = db.insert_organizations(organizations)
                logger.info(f"Inserted {inserted} organizations into database")
            
            # Log completion
            logger.info(f"Data import completed: {stats}")
            
        except Exception as e:
            logger.error(f"Import task failed: {e}")
    
    # Add to background tasks
    background_tasks.add_task(import_task)
    
    return {
        "success": True,
        "message": "Data import started in background. This may take 10-30 minutes.",
        "check_status": "/api/import/status"
    }

@app.get("/api/import/status")
async def import_status():
    """Check the status of data import"""
    
    # Get latest import log from database
    # For now, return basic status
    stats = db.get_statistics()
    
    return {
        "success": True,
        "total_organizations": stats.get('total_organizations', 0),
        "status": "complete" if stats.get('total_organizations', 0) > 0 else "pending"
    }

@app.get("/api/export")
async def export_data(
    format: str = Query("csv", description="Export format: csv or json"),
    q: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(1000, le=10000)
):
    """Export search results as CSV or JSON"""
    
    # Get data
    results, total = db.search_organizations(
        query=q,
        state=state,
        limit=limit,
        offset=0
    )
    
    if format == "json":
        return JSONResponse(
            content={"organizations": results, "total": total},
            headers={
                "Content-Disposition": f"attachment; filename=nonprofits_{datetime.now():%Y%m%d}.json"
            }
        )
    
    else:  # CSV
        import csv
        import io
        
        output = io.StringIO()
        
        if results:
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        return HTMLResponse(
            content=output.getvalue(),
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": f"attachment; filename=nonprofits_{datetime.now():%Y%m%d}.csv"
            }
        )

@app.get("/api/states")
async def get_states():
    """Get list of states with organization counts"""
    
    conn = db.get_connection()
    
    states = conn.execute("""
        SELECT 
            state,
            COUNT(*) as count
        FROM organizations
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY state
    """).fetchall()
    
    conn.close()
    
    return {
        "success": True,
        "states": [dict(row) for row in states]
    }

@app.get("/api/ntee-categories")
async def get_ntee_categories():
    """Get NTEE categories with descriptions"""
    
    return {
        "success": True,
        "categories": [
            {"code": code, "description": desc}
            for code, desc in irs_processor.NTEE_CATEGORIES.items()
        ]
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# =============================================================================
# STARTUP EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Nonprofit Intelligence Platform")
    logger.info(f"Environment: {config.ENV}")
    logger.info(f"Database: {config.DATABASE_URL}")
    
    # Check if database has data
    stats = db.get_statistics()
    
    if stats['total_organizations'] == 0:
        logger.warning("Database is empty. Run /api/import/start to load IRS data")
    else:
        logger.info(f"Database contains {stats['total_organizations']} organizations")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Nonprofit Intelligence Platform")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if config.ENV == "development" else False
    )
