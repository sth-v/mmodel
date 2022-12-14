# Dockerfile
FROM condaforge/mambaforge:latest
MAINTAINER Andrew Astakhov aa@contextmachine.ru
WORKDIR /app
COPY environment.yml e.yml

RUN /bin/bash /opt/conda/bin/conda env update -f e.yml && /bin/bash /opt/conda/condabin/conda init --all
RUN /bin/bash PATH=$PATH:/opt/conda/bin && \
    pip install --upgradate pip && \
    pip install cmake && \
	pip install rhino3dm --no-cache
COPY . .
VOLUME ["/app/mount"]
ENTRYPOINT /bin/bash mamba activate