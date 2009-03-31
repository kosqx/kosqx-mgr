TESTCASE=deep3
RESULTS=results.txt

all:
	python main.py test postgresql ${TESTCASE} | tee -a ${RESULTS}
	python main.py test mysql      ${TESTCASE} | tee -a ${RESULTS}
	python main.py test sqlite     ${TESTCASE} | tee -a ${RESULTS}
	python main.py test oracle     ${TESTCASE} | tee -a ${RESULTS}
	python main.py test db2        ${TESTCASE} | tee -a ${RESULTS}
