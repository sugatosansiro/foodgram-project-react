FROM python:3.7-slim
RUN pip3 install -r requirements.txt --no-cache-dir
WORKDIR /app
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000", "--chdir", "foodgram"]