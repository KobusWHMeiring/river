import uuid
from datetime import timedelta, date
from django.db import transaction
from ..models import Task

def create_task_series(base_task_data: dict, start_date: date, end_date: date, exclude_weekends: bool = True) -> int:
    """
    Creates a series of tasks for a date range.
    """
    tasks_to_create = []
    current_date = start_date
    group_id = uuid.uuid4()
    
    # Cap range at 90 days to prevent bloat
    if (end_date - start_date).days > 90:
        raise ValueError("Task series range cannot exceed 90 days.")

    with transaction.atomic():
        while current_date <= end_date:
            # Skip weekends if requested (Saturday=5, Sunday=6)
            if exclude_weekends and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            task_data = base_task_data.copy()
            task_data['date'] = current_date
            task_data['group_id'] = group_id
            
            tasks_to_create.append(Task(**task_data))
            current_date += timedelta(days=1)
            
        if tasks_to_create:
            Task.objects.bulk_create(tasks_to_create)
            
    return len(tasks_to_create)

def update_task_series(group_id: uuid.UUID, update_data: dict, update_all: bool = False, current_task_id: int = None) -> int:
    """
    Updates a single task or an entire series.
    Only certain fields are synced across a series to preserve historical integrity.
    """
    if not update_all or not group_id:
        # Update only the current task
        if current_task_id:
            Task.objects.filter(id=current_task_id).update(**update_data)
            return 1
        return 0

    # Sync only specific fields for the entire series
    # We NEVER sync 'is_completed' or 'date'
    sync_fields = ['instructions', 'section', 'assignee_type', 'template']
    filtered_update_data = {k: v for k, v in update_data.items() if k in sync_fields}
    
    with transaction.atomic():
        updated_count = Task.objects.filter(group_id=group_id).update(**filtered_update_data)
        
    return updated_count

def delete_task_series(group_id: uuid.UUID, delete_all: bool = False, current_task_id: int = None) -> int:
    """
    Deletes a single task or an entire series.
    """
    if not delete_all or not group_id:
        if current_task_id:
            Task.objects.filter(id=current_task_id).delete()
            return 1
        return 0
        
    with transaction.atomic():
        deleted_count, _ = Task.objects.filter(group_id=group_id).delete()
        
    return deleted_count

def move_todo_task(task_id: int, new_status: str, new_index: int) -> None:
    """
    Updates the status and position of a rolling task and re-indexes
    both source and target status columns if necessary.
    """
    import logging
    log = logging.getLogger(__name__)

    with transaction.atomic():
        task_id = int(task_id)  # JSON sends strings
        task = Task.objects.select_for_update().get(id=task_id)
        old_status = task.todo_status
        log.info(f'move_todo_task: task={task_id} old={old_status} -> new={new_status} index={new_index}')
        print(f'[DEBUG move_todo_task] task={task_id} old={old_status} -> new={new_status} index={new_index}')

        # Short-circuit: no change needed
        if old_status == new_status:
            log.info(f'move_todo_task: same status, skipping')
            print(f'[DEBUG move_todo_task] same status, skipping')
            return

        # Re-index target column (includes the task being moved)
        target_tasks = list(Task.objects.filter(
            is_rolling=True,
            todo_status=new_status
        ).exclude(id=task_id).order_by('todo_position'))

        target_tasks.insert(new_index, task)
        print(f'[DEBUG move_todo_task] target column has {len(target_tasks)} tasks after insert')

        for i, t in enumerate(target_tasks):
            if t.id == task_id:
                updated = Task.objects.filter(id=t.id).update(todo_status=new_status, todo_position=i)
                print(f'[DEBUG move_todo_task] UPDATED task {t.id}: status={new_status} pos={i} rows={updated}')
                log.info(f'move_todo_task: updated task {t.id} to status={new_status} pos={i}')
            elif t.todo_position != i:
                updated = Task.objects.filter(id=t.id).update(todo_position=i)
                print(f'[DEBUG move_todo_task] reindex task {t.id}: pos {t.todo_position} -> {i} rows={updated}')

        # Re-index source column
        source_tasks = Task.objects.filter(
            is_rolling=True,
            todo_status=old_status
        ).exclude(id=task_id).order_by('todo_position')

        for i, t in enumerate(source_tasks):
            if t.todo_position != i:
                updated = Task.objects.filter(id=t.id).update(todo_position=i)
                print(f'[DEBUG move_todo_task] source reindex task {t.id}: pos {t.todo_position} -> {i} rows={updated}')

        # Verify the update actually landed
        task.refresh_from_db()
        print(f'[DEBUG move_todo_task] VERIFY: task {task.id} now has status={task.todo_status} pos={task.todo_position}')
        log.info(f'move_todo_task: verified task {task.id} status={task.todo_status}')
