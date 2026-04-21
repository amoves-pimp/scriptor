from app.storage.review_store import review_store


class ReviewQueueService:
    def list_pending(self):
        return review_store.list_pending()

    def set_status(self, task_id: str, status: str):
        review_store.set_status(task_id, status)
        return {'task_id': task_id, 'status': status}


review_queue_service = ReviewQueueService()
