all: tcalculator.py

tcalculator.py:
	python3 transform.py calculator.py > tcalculator.py

test: tcalculator.py
	echo '(1+2)' > a
	python3 tcalculator.py a

clean:
	rm -f a tcalculator.py
