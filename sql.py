import MySQLdb
import MySQLdb.cursors

class MySQL:
    def __init__(self):
        self.db = MySQLdb.connect("localhost", "TacoBot", "nO0r61oanPJxmZG8", "taco", cursorclass=MySQLdb.cursors.DictCursor)
        self.cur = self.db.cursor()
        self.db.autocommit(True)

    def execute(self, query, r=0):
        self.cur.execute(query)
        if r is 1:
            return self.cur.fetchone()
        elif r is 2:
            return self.cur.fetchall()

    def user(self, user):
        return self.execute(f"SELECT * FROM Users WHERE ID={user.id}", 1)

    def addMoney(self, user, amt):
        current = self.user(user)['Money']
        new = current+amt
        self.execute(f"UPDATE Users SET Money={new} WHERE ID={user.id}")