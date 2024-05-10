from ._engine import async_session
from ._models import User

from datetime import timedelta, datetime
from sqlalchemy.sql.expression import select, update, func


async def get_users_2h_autosending():
    async with async_session() as session:
        users = (await session.execute(select(User.id).where(
            (func.now() - User.registration_date).between(timedelta(minutes=127), timedelta(minutes=4290)),
            User.got_2h_autosending.is_(None)
                                                         )
                                      )
                 ).scalars().all()
    return users


async def mark_got_2h_autosending(id_):
    query = update(User).values(got_2h_autosending=func.now()).where(User.id == id_)
    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_users_24h_autosending():
    async with async_session() as session:
        users = (await session.execute(select(User.id).where(
            (func.now() - User.got_2h_autosending).between(timedelta(hours=24), timedelta(hours=48)),
            User.got_24h_autosending.is_(None)
                                                         )
                                      )
                 ).scalars().all()
    return users


async def mark_got_24h_autosending(id_):
    query = update(User).values(got_24h_autosending=func.now()).where(User.id == id_)
    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_users_48h_autosending():
    async with async_session() as session:
        users = (await session.execute(select(User.id).where(
            (func.now() - User.got_24h_autosending).between(timedelta(hours=24), timedelta(hours=48)),
            User.got_48h_autosending.is_(None)
                                                         )
                                      )
                 ).scalars().all()
    return users


async def mark_got_48h_autosending(id_):
    query = update(User).values(got_48h_autosending=func.now()).where(User.id == id_)
    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_users_for_sending_newsletter() -> list[int]:
    query = select(User.id).where(
                                  User.sending_30_april.is_(None),
                                  (User.registration_date + timedelta(days=10)) < datetime.now()
                                  ).order_by(User.registration_date.desc())
    async with async_session() as session:
        users = (await session.execute(query)).scalars().all()
    return users

async def get_users_for_sending_newsletter_by_date() -> list[int]:
    first_date = datetime(2024, 4, 1)
    second_date = datetime(2024, 4, 30)
    query = select(User.id).where(User.sending_30_april.is_(None), User.registration_date.between(datetime(2024, 4, 1), datetime(2024, 4, 30))).order_by(User.registration_date.desc())
    async with async_session() as session:
        users = (await session.execute(query)).scalars().all()
    return users


async def set_newsletter(id_: int):
    query = update(User).where(User.id == id_).values(sending_30_april=func.now())
    async with async_session() as session:
        await session.execute(query)
        await session.commit()
