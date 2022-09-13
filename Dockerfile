# This Dockerfile builds the API only.

FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "-b", ":5000", "manage:app"]
