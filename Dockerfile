ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION}-buster as builder

WORKDIR /home/app

RUN python -m venv /opt/venv

COPY ./requirements.txt ./

ENV PATH=/opt/venv/bin:${PATH}

RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip pip install -r ./requirements.txt

FROM python:${PYTHON_VERSION}-slim

ENV TZ="Europe/Moscow"

RUN apt update && \
    apt install -y --no-install-recommends libpq5 && \
    apt remove

COPY --from=builder /opt/venv /opt/venv

ENV PATH=/opt/venv/bin:${PATH}

WORKDIR /home/app

# ---------------
# my custom files

COPY ./config ./

COPY ./core ./

RUN mkdir data logs

COPY ./main.py ./

# COPY ./client1.session ./  !!!!!!!!!!!!!!!!!!

CMD python ./main.py
