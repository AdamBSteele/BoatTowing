
def parse_phone(phone):
    parsed_phone = ''.join([x for x in phone if x.isdigit()])
    if len(parsed_phone) != 9 and len(parsed_phone) != 10:
        raise ValueError("Parsed phone was wrong length {}. Expected 9 or 10 digits".format(len(parsed_phone)))
    return parsed_phone
