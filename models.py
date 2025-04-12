from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, uid, email, display_name):
        self.id = uid
        self.email = email
        self.display_name = display_name

class Expense:
    def __init__(self, id, user_id, amount, category, date, description=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.category = category
        self.date = date
        self.description = description
    
    @staticmethod
    def from_dict(id, data):
        return Expense(
            id=id,
            user_id=data.get('user_id'),
            amount=data.get('amount'),
            category=data.get('category'),
            date=data.get('date'),
            description=data.get('description')
        )
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'amount': self.amount,
            'category': self.category,
            'date': self.date,
            'description': self.description
        }
