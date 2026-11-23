# Isolated converter for untrusted HUST pickles. Run with --network none --read-only.
FROM python:3.12-slim
RUN pip install --no-cache-dir pandas==2.2.3 numpy==2.1.3
COPY extract.py /extract.py
USER nobody
ENTRYPOINT ["python", "-I", "/extract.py"]
