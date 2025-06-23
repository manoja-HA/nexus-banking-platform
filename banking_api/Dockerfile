# syntax=docker/dockerfile:1.3

####################################################################################################
# Stage: base-deps
FROM python:3.12-slim AS base-deps

ENV WORKSPACE_PATH=/workspace/banking_api
ENV POETRY_VERSION=1.5.1
ENV PYTHONPATH=$PYTHONPATH:${WORKSPACE_PATH}/src
ENV PYTHONUNBUFFERED=1

# Install poetry
ARG POETRY_VERSION=1.5.1
ENV PIP_DEFAULT_TIMEOUT=60 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    VENV_PATH=${WORKSPACE_PATH}/.venv
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir poetry==${POETRY_VERSION}

ENV PATH=$VENV_PATH/bin:$PATH

# Install dependencies (in .venv)
COPY pyproject.toml poetry.lock ${WORKSPACE_PATH}/
RUN --mount=type=cache,target=~/.cache/pypoetry \
    poetry install --directory=${WORKSPACE_PATH} --no-root --only main

WORKDIR /workspace
EXPOSE 8080

####################################################################################################
# Stage: prod
FROM base-deps AS prod

ARG BUILD_TYPE
ARG GIT_HASH
ARG GIT_TAG

LABEL build-type=$BUILD_TYPE
LABEL git-hash=$GIT_HASH
LABEL git-tag=$GIT_TAG

ENV PYTHONDONTWRITEBYTECODE=1

COPY src ${WORKSPACE_PATH}/src/
COPY pyproject.toml ${WORKSPACE_PATH}/

CMD ["bash", "-c", "${WORKSPACE_PATH}/src/cmd/run_api.sh"]

