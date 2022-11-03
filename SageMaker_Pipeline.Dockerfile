FROM conda/miniconda3:latest

ENV PYTHONPATH="${PYTHONPATH}:/app:/app/src"

# RUN conda config --set channel_priority strict

COPY ./env-havos-linux.yml /app/env-havos-linux.yml
RUN conda update conda
RUN conda env create -f /app/env-havos-linux.yml --debug
SHELL ["conda", "run", "-n", "havos", "/bin/bash", "-c"]
RUN conda install pytorch
# RUN pip uninstall --yes h5py
# RUN pip install h5py
# RUN pip uninstall --yes overrides
# RUN pip install overrides
# # RUN pip install make # for allennlp
# # RUN pip install allennlp
# RUN conda install allennlp -c pytorch -c allennlp -c conda-forge

# check libs
# RUN python import allennlp 

RUN python -m nltk.downloader punkt words stopwords wordnet averaged_perceptron_tagger \
    && python -m spacy download en \
    && python -m spacy validate

COPY ./ /app

# ENTRYPOINT ["conda", "run", "-n", "havos", "--no-capture-output", "python"]
ENTRYPOINT ["conda", "run", "-n", "havos", "python"]
