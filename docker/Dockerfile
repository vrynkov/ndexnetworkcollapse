# Use an official Python runtime as a parent image
FROM continuumio/miniconda3

RUN apt-get update
RUN apt-get install -y build-essential 

RUN mkdir /tmp/ndexnetworkcollapse
COPY ./ /tmp/ndexnetworkcollapse/
RUN pip install /tmp/ndexnetworkcollapse

RUN rm -rf /tmp/ndexnetworkcollapse

RUN mkdir /ndexnetworkcollapse
WORKDIR /ndexnetworkcollapse

CMD /bin/echo "To use run: ndexcollapsenetwork.py"
