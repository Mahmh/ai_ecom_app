FROM python:3.11-slim
WORKDIR /app

COPY ./src /app/src
COPY ./tests /app/tests
COPY ./setup.py /app/
RUN pip install --no-cache-dir -r /app/src/requirements.txt
RUN pip install -e /app/

COPY ./src/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
ENTRYPOINT ["/wait-for-it.sh", "db_c:5432", "--timeout=30", "--", "/wait-for-it.sh", "ollama_c:11434", "--timeout=200", "--", "/wait-for-it.sh", "backend_c:8000", "--timeout=200", "--"]

WORKDIR /app/tests
CMD ["pytest", "-sv"]