#!/bin/sh
DATE=$(date +%F_%H-%M)
tmpDIR=/tmp/tests_Selenium_${DATE}
mkdir ${tmpDIR}

docker run -t -v /dev/shm:/dev/shm -v ${tmpDIR}:/tmp/tests:rw -v $(pwd)/TVWeb/Selenium:/usr/local/Selenium --add-host="flaskdock:$IPFlask" --name selenium --rm joyzoursky/python-chromedriver:3.7-alpine3.8-selenium python3 /usr/local/Selenium/test_script.py > ${tmpDIR}/test_script.log 2>&1
RET=$?
cat ${tmpDIR}/test_script.log
if [ $RET -gt 0 ]; then
    echo "Error for unit tests with Selenium." $RET
    ls -la /tmp
    cd ${tmpDIR}
    ls -laR 
    find . -name "*.png" -exec bash -c 'echo ""; echo {}; echo ""; base64 -w 0 {}' \;
    #rm -rf /tmp/tests/*
    #exit $RET
fi

docker run -t -v /dev/shm:/dev/shm -v ${tmpDIR}:/tmp/tests:rw -v $(pwd)/TVWeb/Selenium:/usr/local/Selenium --add-host="flaskdock:$IPFlask" --name selenium --rm joyzoursky/python-chromedriver:3.7-alpine3.8-selenium python3 /usr/local/Selenium/test_gui.py > ${tmpDIR}/test_gui.log
RET=$?
cat ${tmpDIR}/test_gui.log
if [ $RET -gt 0 ]; then
    echo "Error for GRID tests with Selenium." $RET
    ls -la /tmp
    cd ${tmpDIR}
    ls -laR
    find . -name "*.png" -exec bash -c 'echo ""; echo {}; echo ""; base64 -w 0 {}' \;
    #exit $RET
fi
ls -laR ${tmpDIR}

#docker run -t -v /dev/shm:/dev/shm -v ${tmpDIR}:/tmp/tests:rw -v $(pwd)/TVWeb/Selenium:/usr/local/Selenium --add-host="flaskdock:$IPFlask" --name selenium --rm joyzoursky/python-chromedriver:3.7-alpine3.8-selenium ls -la /usr/local/Selenium

