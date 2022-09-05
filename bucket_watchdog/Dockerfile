FROM python:3.9-buster
WORKDIR /app
COPY app.py .
RUN pip install boto3 requests colored
ENV BUCKET="lahta.contextmachine.online" CALL_URL="https://mmodel.contextmachine.online:8181/update" AWS_DEFAULT_REGION=ru-central1 AWS_ACCESS_KEY_ID=YCAJEfPewAGyo2K-BtlmWNl58 AWS_SECRET_ACCESS_KEY=YCMA8ZF2s_YFoD1WvsMCaym8dx4ZR9eXJ6_f5mmL POSTFIX=.ifc PREFIX=workspace/
CMD python app.py -e all -d 1.0