2FROM python:3.6
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/swigodsky/Data602-Assignment3  /usr/src/app/Cryptocurrency2
EXPOSE 5000
CMD [ "python", "/usr/src/app/Cryptocurrency2/cryptocurrency2.py" ]
