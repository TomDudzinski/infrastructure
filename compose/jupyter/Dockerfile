FROM quay.io/jupyter/scipy-notebook:latest

USER ${NB_UID}

RUN pip install --no-cache-dir \
    uv \
    ollama \
    requests \
    httpx \
    python-dotenv \
    pydantic \
    pandas \
    matplotlib \
    scikit-learn \
    sentence-transformers \
    jupyterlab-git

USER ${NB_UID}
