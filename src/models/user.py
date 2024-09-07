class User:
    def __init__(self, id, email, mobile):
        self.id = id
        self.email = email
        self.mobile = mobile

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, mobile={self.mobile})"