def clean_json(json_data):
    split = json_data.split('}{')
    if len(split) > 1:
        for i in range(len(split)):
            if not split[i].startswith('{'):
                split[i] = '{' + split[i]
            if not split[i].endswith('}'):
                split[i] += '}'
        return split
    else:
        return [json_data]