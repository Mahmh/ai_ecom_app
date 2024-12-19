FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ./requirements.txt ./src/
RUN pip install --no-cache-dir -r ./src/requirements.txt
COPY ./db ./src/db
COPY ./lib ./src/lib
COPY ./server ./src/server
RUN echo "from setuptools import setup, find_packages; setup(name='ai_ecom_app', packages=find_packages())" > setup.py
RUN pip install -e .

EXPOSE 8000

COPY ./wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
ENTRYPOINT ["/wait-for-it.sh", "db_c:5432", "--timeout=30", "--", "/wait-for-it.sh", "ollama_c:11434", "--timeout=500", "--"]

CMD ["sh", "-c", "python3 /app/src/db/scripts/add_data_to_db.py && python3 /app/src/db/scripts/recommendation_data_pipeline.py & python3 /app/src/server/api/main.py"]