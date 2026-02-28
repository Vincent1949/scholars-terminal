# Set UTF-8 environment before anything else
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Reconfigure stdout to use UTF-8 with error replacement
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Now run the actual script
exec(open('reindex_with_metadata.py', encoding='utf-8').read())
