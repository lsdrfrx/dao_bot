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
                count INTEGER NOT NULL
                )
            """
        )

        self.conn.commit()

    def add_user(self, id) -> None:
        self.cur.execute(f"INSERT INTO users (userid) VALUES (?)", (id,))
        self.conn.commit()

    def finish_user(self, id, result) -> None:
        raise NotImplementedError()

    def get_users(self) -> list[tuple]:
        self.cur.execute("SELECT * FROM users")
        users = self.cur.fetchall()
        return users

    def user_exists(self, id) -> bool:
        self.cur.execute("SELECT userid FROM users")
        users = self.cur.fetchall()
        users = list(map(lambda x: x[0], users))
        return id in users

    def add_promocode(self, promocode, count) -> None:
        self.cur.execute(
            "INSERT INTO promocodes (promocode, count) VALUES (?, ?)",
            (
                promocode,
                count,
            ),
        )
        self.conn.commit()

    def issue_promocode(self) -> str | None:
        promocode = self._get_promocode()
        try:
            self._dec_promocode()
        except NoMorePromocodesError:
            return None
        return promocode

    def _get_promocode(self) -> str:
        self.cur.execute("SELECT promocode FROM promocodes")
        data = self.cur.fetchone()
        return data[0]

    def _get_promocodes_number(self) -> int:
        self.cur.execute("SELECT count FROM promocodes")
        data = self.cur.fetchone()
        return data[0]

    def _dec_promocode(self) -> None:
        count = self._get_promocodes_number()
        if count == 0:
            raise NoMorePromocodesError
        self.cur.execute(
            "UPDATE promocodes SET count = ? WHERE count = ?",
            (
                count - 1,
                count,
            ),
        )
        self.conn.commit()

    def __del__(self) -> None:
        self.conn.close()


class NoMorePromocodesError(Exception):
    pass
