from pathlib import Path
import csv
import re
import sys

FILE_PATH = Path('/mnt/data/contactos.csv')


def load_contacts():
    contacts = []
    if FILE_PATH.exists():
        with FILE_PATH.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append({
                    'nombre': row.get('nombre', '').strip(),
                    'telefono': row.get('telefono', '').strip(),
                    'email': row.get('email', '').strip().lower(),
                    'cargo': row.get('cargo', '').strip()
                })
    return contacts


def save_contacts(contacts):
    with FILE_PATH.open('w', newline='', encoding='utf-8') as f:
        fieldnames = ['nombre', 'telefono', 'email', 'cargo']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in contacts:
            writer.writerow({
                'nombre': c['nombre'],
                'telefono': c['telefono'],
                'email': c['email'],
                'cargo': c['cargo']
            })


def valid_email(email: str) -> bool:
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    return re.match(pattern, email) is not None


def input_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Entrada inválida: no puede estar vacía.")


def add_contact(contacts):
    print("\\n--- Registrar nuevo contacto ---")
    nombre = input_nonempty("Nombre: ")
    telefono = input_nonempty("Número de teléfono: ")
    while True:
        email = input_nonempty("Correo electrónico: ").lower()
        if not valid_email(email):
            print("Correo inválido. Intenta de nuevo (ejemplo: usuario@dominio.com).")
            continue
        if any(c['email'] == email for c in contacts):
            print("Ya existe un contacto con ese correo. No se permite duplicado.")
            return False
        break
    cargo = input_nonempty("Cargo dentro de la empresa: ")

    contacts.append({
        'nombre': nombre,
        'telefono': telefono,
        'email': email,
        'cargo': cargo
    })
    save_contacts(contacts)
    print(f"Contacto '{nombre}' registrado correctamente.\\n")
    return True


def search_by_name(contacts):
    print("\\n--- Buscar por nombre (búsqueda parcial permitida) ---")
    q = input_nonempty("Ingresa nombre o fragmento: ").lower()
    results = [c for c in contacts if q in c['nombre'].lower()]
    if not results:
        print("No se encontró ningún contacto con ese nombre.\\n")
        return
    print(f"\\nSe encontraron {len(results)} contacto(s):")
    for i, c in enumerate(results, 1):
        print(f"{i}. Nombre: {c['nombre']}\\n   Teléfono: {c['telefono']}\\n   Email: {c['email']}\\n   Cargo: {c['cargo']}\\n")


def search_by_email(contacts):
    print("\\n--- Buscar por correo electrónico ---")
    q = input_nonempty("Ingresa el correo: ").lower()
    results = [c for c in contacts if c['email'] == q]
    if not results:
        print("No se encontró ningún contacto con ese correo.\\n")
        return
    c = results[0]
    print(f"\\nContacto encontrado:\\nNombre: {c['nombre']}\\nTeléfono: {c['telefono']}\\nEmail: {c['email']}\\nCargo: {c['cargo']}\\n")


def list_contacts(contacts):
    print("\\n--- Lista de contactos registrados ---")
    if not contacts:
        print("La libreta de contactos está vacía.\\n")
        return
    for i, c in enumerate(contacts, 1):
        print(f"{i}. Nombre: {c['nombre']} | Teléfono: {c['telefono']} | Email: {c['email']} | Cargo: {c['cargo']}")
    print("")


def delete_contact(contacts):
    print("\\n--- Eliminar contacto ---")
    modo = ''
    while modo not in ('1', '2'):
        print("Eliminar por: 1) Nombre  2) Correo electrónico")
        modo = input("Opción (1/2): ").strip()
    if modo == '1':
        q = input_nonempty("Ingresa nombre o fragmento: ").lower()
        matches = [c for c in contacts if q in c['nombre'].lower()]
    else:
        q = input_nonempty("Ingresa el correo exacto: ").lower()
        matches = [c for c in contacts if c['email'] == q]

    if not matches:
        print("No se encontró el contacto a eliminar.\\n")
        return False

    print(f"Se encontraron {len(matches)} contacto(s):")
    for idx, c in enumerate(matches, 1):
        print(f"{idx}. {c['nombre']} - {c['email']} - {c['telefono']} - {c['cargo']}")
    if len(matches) == 1:
        choice = '1'
    else:
        choice = input_nonempty(f"Ingresa el número del contacto que deseas eliminar (1-{len(matches)}): ")
    try:
        choice_i = int(choice) - 1
        to_delete = matches[choice_i]
    except Exception:
        print("Selección inválida. Operación cancelada.\\n")
        return False

    confirm = input(f"Confirmar eliminación de '{to_delete['nombre']}' (s/n): ").strip().lower()
    if confirm != 's' and confirm != 'y':
        print("Operación cancelada por el usuario.\\n")
        return False

    for i, c in enumerate(contacts):
        if c['email'] == to_delete['email']:
            contacts.pop(i)
            save_contacts(contacts)
            print(f"Contacto '{to_delete['nombre']}' eliminado correctamente.\\n")
            return True

    print("Ocurrió un error al eliminar. Intenta de nuevo.\\n")
    return False


def main_menu():
    contacts = load_contacts()
    options = {
        '1': ("Registrar un nuevo contacto", add_contact),
        '2': ("Buscar un contacto por nombre", search_by_name),
        '3': ("Buscar un contacto por correo electrónico", search_by_email),
        '4': ("Listar todos los contactos", list_contacts),
        '5': ("Eliminar un contacto", delete_contact),
        '6': ("Salir", None)
    }

    while True:
        print("=== ConnectMe - Gestión de Contactos ===")
        for k, (desc, _) in options.items():
            print(f"{k}. {desc}")
        choice = input("Selecciona una opción (1-6): ").strip()
        if choice not in options:
            print("Opción inválida. Intenta de nuevo.\\n")
            continue
        if choice == '6':
            print("Saliendo... ¡Hasta luego!")
            break
        action = options[choice][1]
        try:
            action(contacts)
        except Exception as e:
            print("Ocurrió un error durante la operación:", e)
            print("Intenta de nuevo.\\n")


if __name__ == "__main__":
    try:
        print("Iniciando ConnectMe...")
        main_menu()
    except KeyboardInterrupt:
        print("\\nPrograma interrumpido por el usuario. Guardando cambios...")
        try:
            save_contacts(load_contacts())
        except Exception:
            pass
        sys.exit(0)
