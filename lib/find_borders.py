import re

acc_masks = ['\+79\d{9}[^\d]', '79\d{9}[^\d]', '89\d{9}[^\d]', '9\d{9}[^\d]',]
begin_masks = ['\+79', '(\D|^)9\d{2}', '\+7', '(\D|^)89','(\D|^)79']
web_contacts_parts = ['ru', 'http', 'com' , '\.ру', '\.рф', 'www']
social_contacts_parts = ['skype', 'telegram', 'скайп', 'vkontakne', 'вконтакте', 'vk', 'tg', 'телеграм', 'телега']

rus_numbers = \
'раз один два три четыре пять шесть семь восемь девять десять двадцать тридцать сорок пятьдесят шестьдесят семьдесят восемьдесят девяносто'
rus_numbers = rus_numbers.split()


def calc_mask_digit_begining(mask):
    
    add_coeff = 0
    if 'D' in mask:
        add_coeff = -1
    
    for symb in mask:
        if symb == '+':
            return -1 + add_coeff
        if symb in '78':
            return 0 + add_coeff
        if symb == '9':
            return 1 + add_coeff
        
    else:
        return 0

    
mask_digit_begining_dict = {}
    
for mask in begin_masks:
    mask_digit_begining_dict[mask] = calc_mask_digit_begining(mask)
 

def check_trans_in(string_part):
    for rus_number in rus_numbers:
        if rus_number in string_part:
            return True
    else:
        return False
 
def transcription_pos_calc(string_):
    rus_transc = find_iters('девят', string_)

    if rus_transc:
        tr_beg = rus_transc[0][0]
        if check_trans_in(string_[tr_beg:tr_beg+100]):
            return max(0, tr_beg - 5), min(tr_beg + 60, len(string_))

    return None


def find_accur_mask(string_):
    
    return [(m.start(0), m.end(0)-2) for m in re.finditer('|'.join(acc_masks), string_)]


def find_iters(mask, string_):
    
    return [(m.start(0), m.end(0)-1) for m in re.finditer(mask, string_)]


def find_digit_indexes(string_):

    return [m.start(0) for m in re.finditer('\d', string_)]


def find_cutting_borders(string_):

    for mask in begin_masks:
        poss = find_iters(mask, string_)

        if poss:
            poss_begin = poss[0][0]
            nine_begin = poss_begin - mask_digit_begining_dict[mask] + 1
            digit_indexes = find_digit_indexes(string_)
            last_digit_index = [ix for ix in digit_indexes if ix >= nine_begin][:10][-1]
            if last_digit_index - poss_begin > 66 or last_digit_index - poss_begin < 8:
                continue
            return (poss_begin, last_digit_index)
    
    th = find_iters('8\D9\D\d\D\d', string_)
    
    if th:
        return th[0][0], th[0][0] + 21
    
    th = find_iters('9\D\d\D\d\D', string_)
    
    if th:
        return th[0][0], th[0][0] + 19
    
    transcriptions_borders = transcription_pos_calc(string_)
    
    if transcriptions_borders:
        return transcriptions_borders
    
    return None
    
def find_phone_borders(string_):
    
    acc_borders = find_accur_mask(string_)
    
    if acc_borders:
        return acc_borders[0]
    
    return find_cutting_borders(string_)


def find_web_borders(string_):
    
    split_words = re.sub('\n|\t', ' ', string_).split(' ')
    cnt_prev_words = 0
    for w_ix, word in enumerate(split_words):
        if re.findall('|'.join(web_contacts_parts), word):
            prev_words_lengths = sum([len(w) for w in split_words[:w_ix]]) + w_ix
            return (prev_words_lengths, prev_words_lengths + len(word))
        
    else:
        return None

def find_social_borders(string_):
    
    for mask in social_contacts_parts:
        if re.findall(mask, string_):
            split_string = string_.split(mask)
            nick_row = split_string[1].split('\n')[0]
            match = re.search('[\dA_Za-z@_!]+' , nick_row)
            if match:
                prev_len = len(split_string[0]) + len(mask)
                return (prev_len + match.start(), prev_len + match.end())
    else:
        return None

    
def check_intersect(b1, b2):
    
    if set(range(b1[0], b1[1])) & set(range(b2[0], b2[1])):
        return True
    else:
        return False
    
def chose_borders_from_two(b1, b2):
    
    if check_intersect(b1, b2):
        return b1
    else:
        return None

    
def find_borders(desc_string):
    
    string_ = desc_string.lower()
    
    phone_borders = find_phone_borders(string_)
    
    if re.findall('|'.join(web_contacts_parts), string_):
        web_borders = find_web_borders(string_)
    else:
        web_borders = None
        
    if re.findall('|'.join(social_contacts_parts), string_):
        social_borders = find_social_borders(string_)
    else:
        social_borders = None
        
    #print(phone_borders, web_borders, social_borders)
        
    cnt_of_match = int(bool(phone_borders)) + int(bool(web_borders)) + int(bool(social_borders))
    
    if cnt_of_match == 0:
        return None
        
    if cnt_of_match == 3:
        return None
    
    if cnt_of_match == 1:
        return phone_borders if phone_borders else web_borders if web_borders else social_borders
    
    if phone_borders:
        return phone_borders
    
    if not phone_borders:
        return chose_borders_from_two(web_borders, social_borders)
    
    return None
        
    