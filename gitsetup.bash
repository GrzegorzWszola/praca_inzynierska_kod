python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
# Add for fine-tuning training on radeon gpu
# pip3 install -r requirements-rocm.txt --break-system-packages --force-reinstall --no-deps