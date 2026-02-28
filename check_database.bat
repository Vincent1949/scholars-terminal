@echo off
echo ========================================
echo  Scholar's Terminal - Health Check
echo ========================================
echo.

cd /d D:\Claude\Projects\scholars-terminal\backend

python -c "import chromadb; client = chromadb.PersistentClient(path='D:/Claude/Projects/scholars-terminal/data/vector_db'); collection = client.get_collection('documents'); print(f'Database Status: OK'); print(f'Total Documents: {collection.count():,}')"

echo.
pause
