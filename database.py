import random
import sqlite3


class DB:
    def __init__(self):
        self.conn = sqlite3.connect("/tmp/dao/storage.sql")
        self.cur = self.conn.cursor()

        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                userid TEXT NOT NULL,
                result INTEGER
                )
            """
        )

        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS promocodes (
                id INTEGER PRIMARY KEY,
                promocode TEXT NOT NULL,
                issued BOOLEAN NOT NULL,
                userid TEXT
                )
            """
        )

        self.conn.commit()

    def add_user(self, id) -> None:
        self.cur.execute(f"INSERT INTO users (userid) VALUES (?)", (id,))
        self.conn.commit()

    def finish_user(self, id, result) -> None:
        self.cur.execute(
            f"UPDATE users SET result = ? WHERE userid = ?",
            (
                result,
                id,
            ),
        )
        self.conn.commit()

    def get_users(self) -> list[tuple]:
        self.cur.execute("SELECT * FROM users")
        users = self.cur.fetchall()
        return users

    def user_exists(self, id) -> bool:
        self.cur.execute("SELECT userid FROM users")
        users = self.cur.fetchall()
        users = list(map(lambda x: x[0], users))
        return id in users

    def generate_promocodes(self, count) -> None:
        vocab = "abcdefghijklmnopqrstuvwxyz1234567890"

        for _ in range(count):
            promo = f"#SHOD_{random.choices(vocab, k=10)}"

            self.cur.execute(
                "INSERT INTO promocodes (promocode, issued) VALUES (?, ?)",
                (
                    promo,
                    False,
                ),
            )

        self.conn.commit()

    def issue_promocode(self, id) -> str | None:
        self.cur.execute("SELECT promocode FROM promocodes WHERE issued = FALSE")
        data = self.cur.fetchone()
        promocode = data[0]

        if promocode:
            self.cur.execute(
                "UPDATE promocodes SET userid = ? issued = TRUE WHERE promocode = ?",
                (
                    id,
                    promocode,
                ),
            )
            self.conn.commit()
            return promocode
        return None

    def get_promocode_count(self) -> int:
        self.cur.execute("SELECT promocode FROM promocodes WHERE issued = FALSE")
        data = self.cur.fetchall()
        return len(data)

    def get_promocodes(self):
        self.cur.execute("SELECT * FROM promocodes")
        data = self.cur.fetchall()
        return data

    def __del__(self) -> None:
        self.conn.close()
