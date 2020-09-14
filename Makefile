all: tcalculator.py

tcalculator.py:
	python3 transform.py calculator.py > tcalculator.py

test: tcalculator.py tested.a
	python3 tcalculator.py tested.a

dtest: tcalculator.py tested.a
	python3 -m pudb tcalculator.py tested.a


tested.a:
	echo '(1+2)' > tested.a

clean:
	rm -rf tested.a tcalculator.py __pycache__
