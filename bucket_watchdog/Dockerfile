FROM fnndsc/conda
RUN conda init --all
RUN pip install boto3 requests colored

COPY app.py /
ENV AWS_DEFAULT_REGION=ru-central1 AWS_ACCESS_KEY_ID=YCAJEfPewAGyo2K-BtlmWNl58 AWS_SECRET_ACCESS_KEY=YCMA8ZF2s_YFoD1WvsMCaym8dx4ZR9eXJ6_f5mmL POSTFIX=ifc PREFIX=workspace
CMD python app.py -e all -d 1.0