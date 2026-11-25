from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Database initialized with synthetic games and local demo accounts.")
    print("Player: student / Student@12345")
    print("Admin:  admin   / Admin@12345")
    print("Change these demo passwords before sharing a machine.")
