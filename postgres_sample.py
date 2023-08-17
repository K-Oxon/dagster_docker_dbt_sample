import psycopg2

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/dwh"


def main():
    cursor = psycopg2.connect(DATABASE_URL)
    print(cursor)
    cursor.close()


if __name__ == "__main__":
    main()
