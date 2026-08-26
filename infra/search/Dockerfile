FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY shared_search /app/shared_search

RUN useradd --create-home --uid 10001 searchgateway
USER searchgateway

EXPOSE 8877
CMD ["python", "-m", "shared_search.server"]
