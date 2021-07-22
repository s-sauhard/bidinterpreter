
FROM continuumio/miniconda3

WORKDIR /app/webapp

RUN apt-get update --fix-missing
RUN apt-get -y install autoconf python3.8 python3.8-distutils pdfplumber automake libtool postgresql-client gcc g++ libpq-dev python-psycopg2 libtesseract-dev libleptonica-dev liblept5 tesseract-ocr libleptonica-dev 
RUN pip install --upgrade docker
RUN python3 -m pip install -r requirements.txt

ADD environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml
RUN echo "source activate bidinterpreter" > ~/.bashrc
ENV PATH /opt/conda/envs/bidinterpreter/bin:$PATH
RUN python -m spacy download en_core_web_sm

EXPOSE 8002

# RUN python /app/manage.py makemigrations
# RUN python /app/manage.py migrate

# COPY wait-for-it.sh /usr/local/bin/
# ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh  /usr/local/bin/
# ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/9995b721327eac7a88f0dce314ea074d5169634f/wait-for-it.sh  /usr/local/bin/
# RUN chmod +x /usr/local/bin/wait-for-it.sh
# RUN chmod +x /app/docker-entrypoint.sh
CMD ["/app/docker-entrypoint.sh"]