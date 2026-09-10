#!/usr/bin/env python3
import sys, json

def update_status(task_id, new_status):
    with open(".tasks/plan.json", "r+") as f:
        data = json.load(f)
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = new_status
                break
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    print(f"Updated {task_id} status to {new_status}")

if __name__ == "__main__":
    if sys.argv[1] == "update-status":
        update_status(sys.argv[2], sys.argv[4])