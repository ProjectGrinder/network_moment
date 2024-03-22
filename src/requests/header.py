class Header:
    def __init__(self):
        self.headers = {}

    def add_header(self, name, value):
        self.headers[name] = value

    def get_header(self, name):
        return self.headers.get(name)

    def to_http(self):
        return '\r\n'.join(f'{name}: {value}' for name, value in self.headers.items())
    
    def __str__(self) -> str:
        return self.to_http()
    
    def __repr__(self) -> str:
        return self.to_http()