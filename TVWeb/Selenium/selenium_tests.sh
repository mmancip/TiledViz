#!/bin/sh
docker run -t -v /dev/shm:/dev/shm -v /tmp/tests:/tmp/tests:rw -v $(pwd)/TVWeb/Selenium:/usr/local/Selenium --add-host="flaskdock:$IPFlask" --name selenium --rm joyzoursky/python-chromedriver:3.7-alpine3.8-selenium python3 /usr/local/Selenium/test_script.py
RET=$?
if [ $RET -gt 0 ]; then
    echo "Error for unit tests with Selenium." $RET
    ls -la /tmp
    cd /tmp/tests
    ls -la 
    find . -name "*.png" -exec bash -c 'echo ""; echo {}; echo ""; base64 -w 0 $(basename {})' \;
    #rm -rf /tmp/tests/*
    #exit $RET
fi

docker run -t -v /dev/shm:/dev/shm -v /tmp/tests:/tmp/tests:rw -v $(pwd)/TVWeb/Selenium:/usr/local/Selenium --add-host="flaskdock:$IPFlask" --name selenium --rm joyzoursky/python-chromedriver:3.7-alpine3.8-selenium python3 /usr/local/Selenium/test_gui.py
RET=$?
if [ $RET -gt 0 ]; then
    echo "Error for GRID tests with Selenium." $RET
    ls -la /tmp
    cd /tmp/tests
    ls -la
    find . -name "*.png" -exec bash -c 'echo ""; echo {}; echo ""; base64 -w 0 $(basename {})' \;
    #exit $RET
fi

