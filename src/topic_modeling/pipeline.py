from functools import partial
from sklearn.preprocessing import FunctionTransformer
# uses preprocessing from HavosAI repository: https://github.com/HavosAi/HavosAi/blob/master/src/text_processing/text_normalizer.py
import text_processing.text_normalizer as tx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.decomposition import NMF
from nltk.corpus import stopwords

def identity(arg):
    if isinstance(arg, str):
        return arg
    return arg

def _get_phrased_sents(texts, phrases=None, phrases3=None):
    return [tx.get_phrased_sentence(x.lower(), phrases, phrases3) for  x in texts]
def get_preprocessor(phrases, phrases3):
    return FunctionTransformer(
        func = _get_phrased_sents,
        validate=False,
        kw_args={'phrases': phrases, 'phrases3': phrases3}
    )


def get_topic_modeling_pipeline(phrases, phrases3, n_components, n_features=5000):
    preprocessor = get_preprocessor(phrases, phrases3)

    stopwords_list = stopwords.words('english')
    stopwords_list.extend(['thereof'])
    tfidf_vect =  TfidfVectorizer(
                    max_df=0.95, min_df=2, max_features=n_features, stop_words=stopwords_list, analyzer='word', tokenizer=identity, preprocessor=identity)

    model = NMF(n_components=n_components, random_state=1, alpha=0.1, l1_ratio=0.5)

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('vectorizer', tfidf_vect),
        ('model', model)
    ])
    return pipeline

def get_topic_modeling_pipeline_no_prep(phrases, phrases3, n_components, n_features=5000):
    tokenizer = partial(tx.get_phrased_sentence, phrases=phrases, phrases_3gram=phrases3)

    stopwords_list = stopwords.words('english')
    stopwords_list.extend(['thereof'])
    tfidf_vect =  TfidfVectorizer(
                    max_df=0.95, min_df=2, max_features=n_features, stop_words=stopwords_list, analyzer='word', tokenizer=tokenizer)

    model = NMF(n_components=n_components, random_state=1, alpha=0.1, l1_ratio=0.5)

    pipeline = Pipeline([
        ('vectorizer', tfidf_vect),
        ('model', model)
    ])
    return pipeline