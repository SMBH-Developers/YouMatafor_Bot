import pymysql
import asyncio
import asyncssh
import aiomysql
import json

from sqlalchemy.sql.expression import update

from src.models import User, async_session

# *mdb - mariadb


async def get_users_from_mdb():
    async with asyncssh.connect(host='80.89.230.113', port=22, username='root', password='4p9Ap03VQ9Dv', known_hosts=None) as conn:
        async with conn.forward_local_port('127.0.0.1', 0, '127.0.0.1', 3306) as tunnel:
            local_bind_port = tunnel.get_port()
            print('used query')
            query = "SELECT User_ID, Registration_Date, day_bonus_step, daily_card_step, daily_affirmation_step, Got_autosending_2h, Got_autosending_24h, Got_autosending_48h FROM Users;"
            connection = await aiomysql.connect(host='localhost',  user='root', password='root', db='card_bot', port=local_bind_port)
            cur = await connection.cursor()
            await cur.execute(query)
            data = await cur.fetchall()
            await cur.close()
            connection.close()
    return data


async def fill_psql_from_mdb_data(data):
    users = [User(id=int(user[0]), registration_date=user[1],
                  daily_bonus_step=user[2], daily_card_step=user[3], daily_affirmation_step=user[4],
                  got_2h_autosending=user[5], got_24h_autosending=user[6], got_48h_autosending=user[7]
                  ) for user in data]
    async with async_session() as session:
        session.add_all(users)
        await session.commit()


async def main():
    data = await get_users_from_mdb()
    await fill_psql_from_mdb_data(data)


if __name__ == '__main__':
    asyncio.run(main())

