FROM alpine

RUN apk --update add openssh openssh-client python python-dev py-pip \
    && rm -rf /var/cache/apk/* \
    && pip install --upgrade pip \
    && pip install pexpect
    

    
COPY change_pwd.py /change_pwd.py

EXPOSE 22
# Login, password, UID (=GID)
CMD ["mytestlogin","m5-fs&ErRt","1002"]
ENTRYPOINT ["/start.sh"]

COPY start.sh /start.sh
