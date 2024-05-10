from sqlalchemy.orm import declarative_base, mapped_column, Mapped

from sqlalchemy import (
    BIGINT,
    String,
    TIMESTAMP,
    func,
    text
)

from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registration_date: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    daily_bonus_step: Mapped[int] = mapped_column(server_default=text('0'))
    daily_card_step: Mapped[int] = mapped_column(server_default=text('0'))
    daily_affirmation_step: Mapped[int] = mapped_column(server_default=text('0'))

    got_2h_autosending: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    got_24h_autosending: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    got_48h_autosending: Mapped[datetime | None] = mapped_column(TIMESTAMP)

    bf_state: Mapped[str | None] = mapped_column(String(64))

    bf_22nov: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    bf_2_22nov: Mapped[datetime | None] = mapped_column(TIMESTAMP)

    sending_29_feb: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    sending_10_march: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    sending_25_march: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    sending_4_april: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    sending_24_april: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    sending_30_april: Mapped[datetime | None] = mapped_column(TIMESTAMP)


class File(Base):
    __tablename__ = 'files'

    path: Mapped[str] = mapped_column(String(256), primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String(128))
