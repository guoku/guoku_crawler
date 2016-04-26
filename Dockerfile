FROM python:2.7
MAINTAINER judy.programmer@gmail.com
EXPOSE 5555

ENV GC_DEBUG=False
ENV WORKERS=1
ENV PIP_INDEX_URL=https://pypi.mirrors.ustc.edu.cn/simple
ENV TZ "Asia/Shanghai"

RUN mkdir /usr/app
WORKDIR /usr/app
ADD requirements.txt ./
RUN pip install -r requirements.txt
COPY . /usr/app/
RUN pip install -e .

ENTRYPOINT ["/usr/app/entry.sh"]
CMD ["/bin/bash"]
