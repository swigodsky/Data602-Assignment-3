FROM python:3.6
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install statsmodels
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ntp
RUN git clone https://github.com/swigodsky/Data602-Assignment3  /usr/src/app/Cryptocurrency2
EXPOSE 5000
CMD [ "python", "/usr/src/app/Cryptocurrency2/cryptocurrency2.py" ]
