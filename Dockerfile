FROM python:3.5.2-onbuild

ENV network_file "local.cfg"
EXPOSE 8080

WORKDIR /usr/src/app/

CMD ["python3", "-u", "/usr/src/app/sources/main.py"]