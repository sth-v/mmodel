FROM conda/miniconda3
COPY .aws .aws
COPY enviroment.yml enviroment.yml
RUN conda init
RUN conda env create -f enviroment.yml
RUN conda activate bucket_watchdog
WORKDIR /app
COPY . .

CMD ["python", "app.py", "-e", "all", "-d", "1.0"]