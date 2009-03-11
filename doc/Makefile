all: 
	python ../tools/preprocess.py .


pdf: final
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
	rm -f main.{aux,ind,idx,ilg,brf,log,lof,lot,pdf,tex~,tex.backup,toc,out} Makefile~ tex/*.aux tex/*.tex~

