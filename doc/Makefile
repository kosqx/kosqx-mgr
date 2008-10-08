all: final
	@echo "Done"

draft:
	pdflatex main.tex
	pdflatex main.tex

full:
	pdflatex main.tex
	pdflatex main.tex
	makeindex main.idx
	pdflatex main.tex
	pdflatex main.tex

final: clean full
	@echo "Done"

clean:
	rm -f main.aux main.ind main.ilg main.brf main.log main.pdf main.tex~ main.tex.backup main.toc main.out Makefile~ tex/*.aux tex/*.tex~

