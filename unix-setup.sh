#!/bin/bash

echo "[*] Creating virtual environment..."
python3 -m venv venv || { echo "Python 3 not found."; exit 1; }
source venv/bin/activate

echo "[*] Installing dependencies..."
pip install -r requirements.txt || { echo "pip install failed"; exit 1; }

echo "[*] Creating launcher script..."
cat > run_gui.sh <<EOF
#!/bin/bash
source venv/bin/activate
python gui.py
EOF
chmod +x run_gui.sh

echo "[✓] Setup complete. Use './run_gui.sh' to start the app."