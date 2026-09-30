from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.citizen import Citizen


def main():
    db = SessionLocal()

    try:
        citizens = list(
            db.scalars(
                select(Citizen)
                .order_by(Citizen.created_at)
            ).all()
        )

        groups = {}

        for citizen in citizens:
            key = (
                citizen.world_id,
                citizen.name
            )

            groups.setdefault(key, []).append(citizen)

        merged_users = 0
        deleted_duplicates = 0

        for (_, name), group in groups.items():

            if len(group) <= 1:
                continue

            # Mantemos o cidadão mais antigo.
            keeper = group[0]

            total_roses = sum(
                citizen.total_roses
                for citizen in group
            )

            total_wealth = sum(
                citizen.wealth
                for citizen in group
            )

            keeper.total_roses = total_roses
            keeper.wealth = total_wealth

            for duplicate in group[1:]:
                db.delete(duplicate)
                deleted_duplicates += 1

            merged_users += 1

            print(
                f"🔗 {name}: "
                f"{len(group)} cidadãos → 1 | "
                f"🌹 {total_roses} | "
                f"💰 {total_wealth}"
            )

        db.commit()

        print()
        print("==============================")
        print("✅ CONSOLIDAÇÃO CONCLUÍDA")
        print(f"Usuários consolidados: {merged_users}")
        print(f"Clones removidos: {deleted_duplicates}")
        print("==============================")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()