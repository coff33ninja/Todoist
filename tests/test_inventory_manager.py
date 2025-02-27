import pytest
from core.inventory_manager import InventoryManager

@pytest.fixture
def inventory_manager():
    return InventoryManager(db_path=':memory:')


def test_gave_away(inventory_manager):
    """Test the gave_away method"""
    item_id = inventory_manager.gave_away(
        name="Old Book",
        description="A worn-out book",
        quantity=1,
        notes="Donated to library"
    )
    assert item_id is not None

    # Verify the item is logged in the items_given_away table
    cursor = inventory_manager.get_connection().cursor()
    cursor.execute('SELECT * FROM items_given_away WHERE id = ?', (item_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row['name'] == "Old Book"
    assert row['description'] == "A worn-out book"
    assert row['quantity'] == 1
    assert row['notes'] == "Donated to library"
