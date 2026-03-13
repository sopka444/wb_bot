from fastapi import FastAPI, HTTPException
import pymysql
from pymysql.cursors import DictCursor
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "qwe123",
    "db": "thunder_bot_by_Rqiza",
    "cursorclass": DictCursor
}


class SellerInfo(BaseModel):
    wb_sid: str
    name: str
    trade_mark: Optional[str] = None


class TokenData(BaseModel):
    user_id: int
    token: str
    username: Optional[str] = None


@app.on_event("startup")
def startup():
    """Подключаемся к БД при старте сервера"""
    app.state.db = pymysql.connect(**DB_CONFIG)


@app.on_event("shutdown")
def shutdown():
    """Закрываем соединение при остановке сервера"""
    app.state.db.close()


@app.delete("/delete_seller_token/{user_id}/{seller_id}")
async def delete_seller_token(user_id: int, seller_id: int):
    """
    Удаляет токен конкретного магазина по его ID с проверкой принадлежности пользователю

    :param user_id: ID пользователя в Telegram
    :param seller_id: ID магазина в системе
    :return: Сообщение об успешном удалении или ошибку
    """
    try:
        connection = app.state.db
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_token 
                FROM seller_info si
                JOIN token t ON si.id_token = t.id_token
                JOIN user_token ut ON t.id_token = ut.id_token
                JOIN main_user mu ON ut.id_main_user = mu.id_main_user
                WHERE si.id_seller = %s AND mu.user_id = %s
                LIMIT 1
            """, (seller_id, user_id))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(404, "Магазин не найден или у вас нет к нему доступа")

            token_id = result['id_token']

            cursor.execute("DELETE FROM token WHERE id_token = %s", (token_id,))

            connection.commit()
            return {"status": "success", "message": "Токен магазина успешно удален"}

    except pymysql.Error as e:
        connection.rollback()
        raise HTTPException(500, f"Ошибка БД: {e}")


@app.get("/get_seller_token/{user_id}/{seller_id}")
async def get_seller_token(user_id: int, seller_id: int):
    """Получает токен конкретного магазина по его ID с проверкой принадлежности пользователю"""
    try:
        with app.state.db.cursor() as cursor:
            query = """
                SELECT t.token 
                FROM seller_info si
                JOIN token t ON si.id_token = t.id_token
                JOIN user_token ut ON t.id_token = ut.id_token
                JOIN main_user mu ON ut.id_main_user = mu.id_main_user
                WHERE si.id_seller = %s AND mu.user_id = %s
                LIMIT 1
            """
            cursor.execute(query, (seller_id, user_id))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(404, "Токен для данного магазина не найден или у вас нет к нему доступа")
            return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Ошибка БД: {e}")


@app.get("/get_user_stores/{user_id}")
async def get_user_stores(user_id: int):
    try:
        with app.state.db.cursor() as cursor:
            cursor.execute("""
                SELECT si.id_seller, si.name ,si.trade_mark
                FROM seller_info si
                JOIN token t ON si.id_token = t.id_token
                JOIN user_token ut ON t.id_token = ut.id_token
                JOIN main_user mu ON ut.id_main_user = mu.id_main_user
                WHERE mu.user_id = %s
                ORDER BY si.name
            """, (user_id,))

            stores = cursor.fetchall()
            return stores

    except pymysql.Error as e:
        raise HTTPException(500, f"Ошибка БД: {e}")


@app.post("/save_token")
async def save_seller_info_to_db(token_data: TokenData, seller_data: Optional[SellerInfo] = None):
    """Сохраняет токен и информацию о продавце"""
    try:
        connection = app.state.db
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO main_user (user_id, user_lastname) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE user_lastname = VALUES(user_lastname)",
                (token_data.user_id, token_data.username or "")
            )

            cursor.execute(
                "SELECT id_main_user FROM main_user WHERE user_id = %s",
                (token_data.user_id,)
            )
            user_record = cursor.fetchone()
            if not user_record:
                raise ValueError("Не удалось создать/найти пользователя")
            id_main_user = user_record['id_main_user']

            cursor.execute(
                "INSERT INTO token (token, date_registration) VALUES (%s, NOW())",
                (token_data.token,)
            )
            token_id = cursor.lastrowid

            if token_id == 0:
                cursor.execute(
                    "SELECT id_token FROM token WHERE token = %s",
                    (token_data.token,)
                )
                token_record = cursor.fetchone()
                if not token_record:
                    raise ValueError("Не удалось получить ID токена")
                token_id = token_record['id_token']

            cursor.execute(
                "INSERT INTO user_token (id_main_user, id_token) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE id_token = VALUES(id_token)",
                (id_main_user, token_id)
            )

            if seller_data:
                cursor.execute(
                    "INSERT INTO seller_info (id_token, wb_sid, name, trade_mark) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE "
                    "name = VALUES(name), trade_mark = VALUES(trade_mark)",
                    (
                        token_id,
                        seller_data.wb_sid or "",
                        seller_data.name or "",
                        seller_data.trade_mark or ""
                    )
                )

            connection.commit()
            return {"status": "success", "token_id": token_id}

    except Exception as e:
        connection.rollback()
        raise HTTPException(500, f"Ошибка сохранения: {str(e)}")


@app.get("/get_token/{user_id}")
async def get_token(user_id: int):
    """Получает токен пользователя из MySQL"""
    try:
        with app.state.db.cursor() as cursor:
            cursor.execute("""
                SELECT t.token 
                FROM main_user mu
                JOIN user_token ut ON mu.id_main_user = ut.id_main_user
                JOIN token t ON ut.id_token = t.id_token
                WHERE mu.user_id = %s
                ORDER BY t.date_registration DESC
                LIMIT 1
            """, (user_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(404, "Токен не найден")
            return result
    except pymysql.Error as e:
        raise HTTPException(500, f"Ошибка БД: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
