def load_config(file_path):
    import json
    with open(file_path, 'r') as file:
        return json.load(file)

def load_credentials(file_path):
    import json
    with open(file_path, 'r') as file:
        return json.load(file)