"""
Script to start the MITRE ATT&CK Classifier API server
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sentence_transformers',
        'faiss'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.error("Please run: pip install -r requirements.txt")
        return False
    
    return True

def check_data():
    """Check if MITRE data file exists"""
    data_path = Path("data/raw/categories/mitre_training.json")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please ensure the MITRE training data is in the correct location")
        return False
    
    return True

def main():
    """Main startup function"""
    logger.info("="*80)
    logger.info("MITRE ATT&CK Classifier API")
    logger.info("="*80)
    
    # Check dependencies
    logger.info("\n1. Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    logger.info("✓ All dependencies installed")
    
    # Check data
    logger.info("\n2. Checking data files...")
    if not check_data():
        sys.exit(1)
    logger.info("✓ Data files found")
    
    # Start server
    logger.info("\n" + "="*80)
    logger.info("Starting API server...")
    logger.info("API will be available at:")
    logger.info("  - http://localhost:8000")
    logger.info("  - Docs: http://localhost:8000/docs")
    logger.info("  - ReDoc: http://localhost:8000/redoc")
    logger.info("="*80 + "\n")
    
    # Import and run
    import uvicorn
    from api.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nShutting down server...")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
