
def parse_name(name):

    parsed_name = ''
    for piece in name.strip().split(' '):
        try:
            parsed_name += piece[0].upper()
            parsed_name += piece[1:].lower()
        except Exception:
            pass

    return parsed_name
