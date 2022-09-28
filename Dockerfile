# This Dockerfile builds the API only.

FROM python:3.9.5
WORKDIR /app
RUN python --version
RUN pip3 --version
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . . 
EXPOSE 5000
#CMD ["gunicorn", "-b", ":5000","--timeout","0", "manage:app"]
CMD gunicorn --config gunicorn.py manage:app