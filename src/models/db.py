from ._engine import async_session
from ._models import User, File

from pathlib import Path
from datetime import date

from sqlalchemy.sql.expression import select, update, delete, case, func


async def registrate_if_not_exists(id_: int):
    async with async_session() as session:
        exists = (await session.execute(select(User.id).where(User.id == id_).limit(1))).one_or_none()
        if exists is None:
            user = User(id=id_)
            session.add(user)
            await session.commit()


async def delete_user(id_: int):
    query = delete(User).where(User.id == id_)

    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_day_bonus_step(id_: int):
    query = select(User.daily_bonus_step).where(User.id == id_).limit(1)
    async with async_session() as session:
        step = (await session.execute(query)).scalar_one_or_none()
    return step


async def get_daily_card_step(id_: int):
    query = select(User.daily_card_step).where(User.id == id_).limit(1)
    async with async_session() as session:
        daily_card_step = (await session.execute(query)).scalar_one_or_none()
    return daily_card_step


async def get_daily_affirmation_step(id_: int):
    query = select(User.daily_affirmation_step).where(User.id == id_).limit(1)
    async with async_session() as session:
        daily_affirmation_step = (await session.execute(query)).scalar_one_or_none()
    return daily_affirmation_step


async def update_users_daily_steps():
    query = update(User).values(
        daily_bonus_step=case((User.daily_bonus_step == 2, 0), else_=User.daily_bonus_step + 1),
        daily_card_step=case((User.daily_card_step == 5, 0), else_=User.daily_card_step + 1),
        daily_affirmation_step=case((User.daily_affirmation_step == 13, 0), else_=User.daily_affirmation_step + 1)
    )
    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_photo_id(path: Path | str):
    if isinstance(path, Path):
        path = str(path)

    query = select(File.telegram_id).where(File.path == path).limit(1)
    async with async_session() as session:
        photo_id = (await session.execute(query)).scalar_one_or_none()
    return photo_id


async def register_photo(path: Path | str, telegram_id: str):
    if isinstance(path, Path):
        path = str(path)

    async with async_session() as session:
        file = File(path=path, telegram_id=telegram_id)
        session.add(file)
        await session.commit()


async def get_count_all_users() -> int:
    query = select(func.count('*')).select_from(User)
    async with async_session() as session:
        count = (await session.execute(query)).scalar_one()
    return count


async def users_for_today() -> int:
    query = select(func.count('*')).select_from(User).where(func.DATE(User.registration_date) == date.today())
    async with async_session() as session:
        count = (await session.execute(query)).scalar_one()
    return count
