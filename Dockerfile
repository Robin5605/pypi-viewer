FROM python:3.12-slim@sha256:af4e85f1cac90dd3771e47292ea7c8a9830abfabbe4faa5c53f158854c2e819d as builder

RUN pip install -U  pdm

COPY pyproject.toml pdm.lock README.md /pypi_viewer/
COPY src/ /pypi_viewer/src

WORKDIR /pypi_viewer
RUN pdm install --check --prod --no-editable

FROM python:3.12-slim@sha256:af4e85f1cac90dd3771e47292ea7c8a9830abfabbe4faa5c53f158854c2e819d as runner

COPY --from=builder /pypi_viewer/.venv/ /pypi_viewer/.venv
ENV PATH="/pypi_viewer/.venv/bin:$PATH"

COPY src/ /pypi_viewer/src

CMD ["fastapi", "run", "/pypi_viewer/src/pypi_viewer/main.py"]

EXPOSE 8000
