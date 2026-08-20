from pydantic import ValidationError
import bcrypt

import database
from models import HardwareCreate, HardwareUpdate, UserLogin, UserRegistration


class AuthController:
    def __init__(self, view, authenticated_handler):
        self.view = view
        self._authenticated_handler = authenticated_handler
        self.view.set_callbacks(self.login, self.register)

    def register(self, username: str, password: str) -> None:
        try:
            payload = UserRegistration(username=username, password=password)
        except ValidationError as exc:
            error = exc.errors()[0]["msg"]
            self.view.show_error("Registration Failed", error)
            return

        if database.user_exists(payload.username):
            self.view.show_error("Duplicate User", "That username is already registered.")
            return

        password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        database.create_user(payload.username, password_hash)
        self.view.show_info("Success", "Registration completed. You may now log in.")
        self.view.clear_register_fields()

    def login(self, username: str, password: str) -> None:
        try:
            payload = UserLogin(username=username, password=password)
        except ValidationError as exc:
            error = exc.errors()[0]["msg"]
            self.view.show_error("Login Failed", error)
            return

        user_record = database.find_user_by_username(payload.username)
        if user_record is None:
            self.view.show_error("Login Failed", "Invalid username or password.")
            return

        stored_hash = user_record["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(payload.password.encode("utf-8"), stored_hash):
            self.view.show_error("Login Failed", "Invalid username or password.")
            return

        self.view.clear_login_fields()
        self._authenticated_handler(payload.username)


class InventoryController:
    def __init__(self, view, logout_handler):
        self.view = view
        self._logout_handler = logout_handler
        self.view.bind_callbacks(self.add_item, self.update_item, self.delete_item, self.logout)
        self.refresh_inventory()

    @staticmethod
    def compute_status(quantity: int) -> str:
        if quantity > 5:
            return "In Stock"
        if 1 <= quantity <= 5:
            return "Low Stock"
        return "Out of Stock"

    def add_item(self, item_name: str, category: str, quantity_text: str, price_text: str) -> None:
        try:
            payload = HardwareCreate(
                item_name=item_name,
                category=category,
                quantity=quantity_text,
                unit_price=price_text,
            )
        except ValidationError as exc:
            message = exc.errors()[0]["msg"]
            self.view.show_error("Add Item Failed", message)
            return

        if database.hardware_exists(payload.item_name):
            self.view.show_error("Duplicate Item", "An item with that name already exists.")
            return

        status = self.compute_status(payload.quantity)
        database.add_hardware(payload.item_name, payload.category, payload.quantity, payload.unit_price, status)
        self.refresh_inventory()
        self.view.clear_add_fields()
        self.view.show_info("Saved", "New hardware item added.")

    def update_item(self, item_id: int, quantity_text: str, price_text: str) -> None:
        try:
            payload = HardwareUpdate(
                item_id=item_id,
                quantity=quantity_text,
                unit_price=price_text,
            )
        except ValidationError as exc:
            message = exc.errors()[0]["msg"]
            self.view.show_error("Update Failed", message)
            return

        status = self.compute_status(payload.quantity)
        if database.get_hardware_by_id(payload.item_id) is None:
            self.view.show_error("Update Failed", "Selected item no longer exists.")
            return

        database.update_hardware(payload.item_id, payload.quantity, payload.unit_price, status)
        self.refresh_inventory()
        self.view.show_info("Updated", "Selected hardware item has been updated.")

    def delete_item(self, item_id: int) -> None:
        if database.get_hardware_by_id(item_id) is None:
            self.view.show_error("Delete Failed", "Selected item no longer exists.")
            return

        database.delete_hardware(item_id)
        self.refresh_inventory()
        self.view.show_info("Deleted", "Item deleted from inventory.")

    def refresh_inventory(self) -> None:
        items = database.get_all_hardware()
        self.view.populate_items(items)

    def logout(self) -> None:
        self._logout_handler()
