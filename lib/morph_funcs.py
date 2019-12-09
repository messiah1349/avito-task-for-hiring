import re
import string
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

def lemmatize(text):
    return " ".join([morph.parse(word)[0].normal_form for word in text])


def strip_eng(data):
    p = re.compile(r'[a-zA-Z]+')
    return p.sub('', data)

def strip_html(data):
    p = re.compile(r'<.*?>')
    return p.sub(' ', data)

def strip_punctuation(data):
    remove = dict.fromkeys(map(ord, '—«»' + string.punctuation.replace('-', "")), ' ')
    text = data.translate(remove).strip()
    text = text.replace("  ", " ")
    return text

def remove_number(text):
    text = re.sub(r'(0|1|2|3|4|5|6|7|8|9)', '', text)
    return text
  
def remove_stopwords(text, russian_stopwords):
    tokens = [token for token in text.split() if token not in russian_stopwords]
    return ' '.join(tokens)


def handle_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text

def preprocessing_all_method(text,
                            russian_stopwords,
                            numbers=False,
                            stop_words=False,
                            eng=False,
                            leave_only_letters=True ):
    
    text = str(text).strip().lower()

    text = handle_emojis(text)
    text = strip_punctuation(text)

    text = text.replace("\n", " ")
    text = text.replace("-", " ")
    text = text.replace("₽", "")


    if eng:
        text = strip_eng(text)
        
    if numbers:
        text = remove_number(text)
        
    text = text.replace("  ", " ")
    
    if stop_words:
        text = remove_stopwords(text, russian_stopwords)
    
    if leave_only_letters:
        text = re.sub('[^a-zA-Z0-9а-яА-Я]+', ' ', text)
        
    text = re.sub("\s\s+" , " ", text)
    
    return text