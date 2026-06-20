from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from Models.database import Base
from Models.category import Category

engine = create_engine("sqlite:///:memory:", echo=True)

print("\n--- TWORZENIE TABEL ---")
Base.metadata.create_all(engine)

print("\n--- TEST ZAPISU I ODCZYTU ---")
with Session(engine) as session:
    nowa_kategoria = Category(name="Moja Testowa Kategoria")

    session.add(nowa_kategoria)
    session.commit()

    pobrana_kategoria = session.query(Category).first()

    print("\n--- WYNIK TESTU ---")
    if pobrana_kategoria:
        print("✅ SUKCES! Baza działa poprawnie.")
        print(f"Pobrane ID z bazy: {pobrana_kategoria.id}")
        print(f"Pobrana nazwa: {pobrana_kategoria.name}")
        print(f"Pobrany kolor: {pobrana_kategoria.color.display_name}")
    else:
        print("❌ BŁĄD! Baza jest pusta, coś poszło nie tak.")