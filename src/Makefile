TESTCASE=deep3
RESULTS=results.txt

all:
	python main.py test postgresql ${TESTCASE} >> ${RESULTS}
	python main.py test mysql      ${TESTCASE} >> ${RESULTS}
	python main.py test sqlite     ${TESTCASE} >> ${RESULTS}
	python main.py test oracle     ${TESTCASE} >> ${RESULTS}
	python main.py test db2        ${TESTCASE} >> ${RESULTS}
