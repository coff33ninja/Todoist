from inventory_manager import InventoryManager
from datetime import datetime

class TaskManager:
    def __init__(self, db_path='inventory.db'):
        self.inventory = InventoryManager(db_path)

    def create_repair_task(self, item_id, description, required_components=None,
                         estimated_cost=None):
        return self.inventory.add_repair_task(item_id, description,
                                           required_components, estimated_cost)

    def get_pending_tasks(self):
        return self.inventory.get_repair_tasks()

    def calculate_repair_costs(self):
        tasks = self.get_pending_tasks()
        total_cost = sum(task[5] for task in tasks if task[5] is not None)
        return total_cost

    def get_required_components(self):
        tasks = self.get_pending_tasks()
        components = {}
        for task in tasks:
            if task[4]:  # required_components
                for component in task[4].split(','):
                    component = component.strip()
                    if component in components:
                        components[component] += 1
                    else:
                        components[component] = 1
        return components
