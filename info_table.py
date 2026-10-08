from __future__ import annotations

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from sqlalchemy import select, update, text, Boolean
from dataclasses import dataclass

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class Grade(Base):
    __tablename__= 'grade'

    id: Mapped[int] = mapped_column(primary_key=True)
    grade = mapped_column(String, nullable=True)
    task_1 = mapped_column(String, nullable=True)
    task_2 = mapped_column(String, nullable=True)
    task_3 = mapped_column(String, nullable=True)

async def get_grades():
    async with async_session() as session:
        return await session.scalars(select(Grade))

async def get_grade(grade_id):
    async with async_session() as session:
        return await session.scalar(select(Grade).where(Grade.id == grade_id))

async def get_users_by_grade(grade: str) -> list[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.grade == grade)
        )
        return result.scalars().all()

@dataclass
class TaskData:
    task_id: str
    task_answer: int

async def get_task_photo_id(grade: str, task_number: int) -> TaskData | None:
    async with async_session() as session:
        column_name = f"task_{task_number}" 
        column = getattr(Grade, column_name)
        result = await session.scalar(
            select(column).where(Grade.grade == grade)
        )
        if not result:
            return None
        parts = result.split('_')
        task_id = '_'.join(parts[:-1])
        task_answer = parts[-1] 
        return TaskData(
            task_id=task_id,
            task_answer=task_answer
        )


class Person(Base):
    __tablename__= 'people'

    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[str] = mapped_column()

async def get_people():
    async with async_session() as session:
        return await session.scalars(select(Person))

async def get_person(person_id):
    async with async_session() as session:
        return await session.scalar(select(Person).where(Person.id == person_id))

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    grade = mapped_column(String)
    photo1_id = mapped_column(String)
    photo2_id = mapped_column(String)
    photo3_id = mapped_column(String)
    waiting_answer = mapped_column(String)

async def get_user_grade(tg_id: int) -> str:
    async with async_session() as session:
        result = await session.scalar(
            select(User.grade).where(User.tg_id == tg_id)
        )
        return result

async def set_grade(user_id: int, grade: str):
    async with async_session() as session:
        async with session.begin():
            column_name = 'grade'
            stmt = (
                update(User)
                .where(User.tg_id == user_id)
                .values({column_name: grade})
            )
            await session.execute(stmt)

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()

async def update_user_photo(grade: str, photo_id: str, person_number: int):
    async with async_session() as session:
        async with session.begin(): 
            column_name = f"photo{person_number}_id"
            stmt = (
                update(User)
                .where(User.grade == grade)
                .values({column_name: photo_id}) 
            )
            await session.execute(stmt)

async def update_user_photo_approve(grade: str, person_number: int):
    async with async_session() as session:
        async with session.begin(): 
            column_name = f"photo{person_number}_id"
            stmt = (
                update(User)
                .where(User.grade == grade)
                .values({column_name: "approved"})
            )
            await session.execute(stmt)

async def update_user_photo_reject(grade: str, person_number: int):
    async with async_session() as session:
        async with session.begin(): 
            column_name = f"photo{person_number}_id"
            stmt = (
                update(User)
                .where(User.grade == grade)
                .values({column_name: None})
            )
            await session.execute(stmt)

async def update_user_photo_task(grade: str, person_number: int):
    async with async_session() as session:
        async with session.begin(): 
            column_name = f"photo{person_number}_id"
            stmt = (
                update(User)
                .where(User.grade == grade)
                .values({column_name: "task"})
            )
            await session.execute(stmt)

@dataclass
class TaskAnswer:
    user_id: int
    task_answer: int
    person_number: int

async def get_waiting_answer(tg_id: int) -> TaskAnswer | None:
    async with async_session() as session:
        result = await session.scalar(
            select(User.waiting_answer).where(User.tg_id == tg_id)
        )
        if not result:
            return None
        parts = result.split('_')
        user_id = parts[0]
        task_answer = parts[1] 
        person_number = parts[2]
        return TaskAnswer(
            user_id=user_id,
            task_answer=task_answer,
            person_number=person_number
        )

async def set_waiting_answer(user_id: int, correct_answer: int, person_number: int):
    async with async_session() as session:
        async with session.begin():
            column_name = 'waiting_answer'
            stmt = (
                update(User)
                .where(User.tg_id == user_id)
                .values({column_name: f"{user_id}_{correct_answer}_{person_number}"})
            )
            await session.execute(stmt)

async def none_waiting_answer(user_id: int):
    async with async_session() as session:
        async with session.begin():
            column_name = 'waiting_answer'
            stmt = (
                update(User)
                .where(User.tg_id == user_id)
                .values({column_name: None})
            )
            await session.execute(stmt)


async def all_done(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        statuses = [getattr(user, f"photo{i}_id") for i in range(1, 4)]
        return all(status == "approved" for status in statuses)

class Info(Base):
    __tablename__ = 'info'

    id: Mapped[int] = mapped_column(primary_key=True)
    grade = mapped_column(String)
    photo_id = mapped_column(String)

async def get_info_id(grade: str):
    async with async_session() as session:
        result = await session.scalar(
            select(Info.photo_id).where(Info.grade == grade)
        )
        return result
