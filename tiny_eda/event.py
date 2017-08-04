class Event:
    def __init__(self, type_, data):
        self.type = type_
        self.data = data

    def __str__(self):
        return str({'type': self.type,
                    'data': self.data})
